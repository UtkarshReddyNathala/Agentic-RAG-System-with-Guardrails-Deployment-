import operator
from typing import Annotated, List, TypedDict


class AgentState(TypedDict):
    # operator.add makes each step add to the message history instead of replacing it.
    messages: Annotated[List[dict], operator.add]
    current_query: str
    documents: List[str]
    plan: List[str]
    status: str
    final_answer: str
