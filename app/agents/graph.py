import logfire
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.nodes.planner import planner_node
from app.agents.nodes.responder import generate_node
from app.agents.nodes.retriever import retrieve_node
from app.agents.state import AgentState
from app.config import settings


def create_checkpointer() -> BaseCheckpointSaver:
    """
    Create a Postgres checkpointer that saves chat history permanently.
    Falls back to in-memory MemorySaver only if Postgres can't be reached.

    Note: setup() runs on its own autocommit connection because LangGraph's
    setup includes CREATE INDEX CONCURRENTLY, which Neon rejects inside a
    transaction (the default for a connection pool).
    """
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg_pool import ConnectionPool

        pool = ConnectionPool(
            conninfo=settings.postgres_uri,
            max_size=20,
            open=False,
            timeout=10,
            num_workers=3,
            check=ConnectionPool.check_connection,
            max_idle=240,
        )
        # Make sure Postgres is reachable now. Otherwise the first question
        # would hang while the pool keeps retrying.
        pool.open()
        conn = pool.getconn()
        pool.putconn(conn)

        # Create the checkpoint tables on a separate autocommit connection:
        # Neon rejects CREATE INDEX CONCURRENTLY inside a transaction.
        try:
            with PostgresSaver.from_conn_string(settings.postgres_uri) as setup_saver:
                setup_saver.setup()
        except Exception as e:
            logfire.warning(f"⚠️ Postgres checkpointer setup failed ({e}); falling back to MemorySaver.")
            pool.close()
            return MemorySaver()

        checkpointer = PostgresSaver(pool)
        logfire.info("🗄️ Postgres checkpointer configured.")
        return checkpointer
    except Exception as e:
        logfire.warning(
            f"⚠️ Postgres checkpointer unavailable ({e}); falling back to MemorySaver. "
            "Do not use MemorySaver in production — state is lost on restart."
        )
        return MemorySaver()


def build_graph(checkpointer: BaseCheckpointSaver | None = None) -> StateGraph:
    """
    Build and compile the LangGraph RAG agent.

    Args:
        checkpointer: Optional checkpointer. If None, a Postgres-backed
            checkpointer is created. Pass a MemorySaver in tests.
    """
    if checkpointer is None:
        checkpointer = create_checkpointer()

    # 1. Initialize the State Graph
    workflow = StateGraph(AgentState)

    # 2. Define the Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retrieve_node)
    workflow.add_node("responder", generate_node)

    # 3. Define the Edges & Routing Logic
    def route_planner(state: AgentState):
        """
        Choose the next step based on the planner's decision.
        """
        if state["current_query"] == "CONVERSATIONAL":
            return "responder"
        return "retriever"

    workflow.set_entry_point("planner")

    # After the planner, go to the retriever (technical) or the responder (small talk)
    workflow.add_conditional_edges("planner", route_planner, {"retriever": "retriever", "responder": "responder"})

    workflow.add_edge("retriever", "responder")
    workflow.add_edge("responder", END)

    # 4. Compile the Graph with Memory
    return workflow.compile(checkpointer=checkpointer)


# The graph is built once when the app starts (see app.main.startup_event),
# not on import, so tests can pass in their own checkpointer.
