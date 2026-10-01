"""
Step 1 — collect live answers.
Sends each golden-dataset question to the running /query endpoint and saves:
actual_response (first 300 characters), actual_contexts (the source chunks)
and actual_tools_called (worked out from thought_process).
"""

import copy
import json
import os
import time

import logfire
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
API_URL = f"{BACKEND_URL}/query"
RESPONSE_TRUNCATE = 300
DELAY_BETWEEN_CALLS = 10  # seconds — keeps the run within LLM provider rate limits
REQUEST_TIMEOUT = 120  # seconds — guardrails + agent + LLM calls can exceed 60 s


def api_headers() -> dict:
    """Bearer auth header for the API when RAG_API_KEY is configured."""
    key = os.getenv("RAG_API_KEY")
    return {"Authorization": f"Bearer {key}"} if key else {}


def detect_tool(thought_process: list) -> str:
    """
    Work out which path the agent took from the thought_process list.
    Planner sets:  'Intent: Technical' + 'Search Term: ...' → retrieve_documents
                   'Intent: Conversational/Memory'           → direct_answer
    main.py sets:  'Intent: Guardrails Fired'                → guardrails
    """
    joined = " ".join(thought_process).lower()
    if "guardrails fired" in joined:
        return "guardrails"
    if "intent: technical" in joined or "search term:" in joined or "context retrieved" in joined:
        return "retrieve_documents"
    if "conversational" in joined or "memory" in joined:
        return "direct_answer"
    return "unknown"


def _fetch_query_result(question: str, thread_id: str) -> dict:
    """Send one question to /query and return the JSON response."""
    resp = requests.post(
        API_URL,
        json={"q": question, "thread_id": thread_id},
        headers=api_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") == "error":
        raise RuntimeError(data.get("message", "API returned an error"))
    return data


def run_pipeline(golden_dataset: dict, progress_callback=None) -> dict:
    """
    Add live API results to each question in the golden dataset.
    Returns a copy with actual_response, actual_contexts and actual_tools_called filled in.
    progress_callback(i, total, question, stage, response="") is called after each step.
    """
    dataset = copy.deepcopy(golden_dataset)
    samples = dataset["rag_samples"]
    n = len(samples)

    with logfire.span("🚀 Eval Phase 1 — Live Pipeline", total_samples=n):
        for i, sample in enumerate(samples):
            question = sample["question"]

            if progress_callback:
                progress_callback(i, n, question, "calling")

            with logfire.span(
                f"📤 Live Query {i + 1}/{n}",
                question=question[:80],
                domain=sample.get("domain", ""),
            ):
                try:
                    data = _fetch_query_result(question, thread_id=f"eval_run_{i}")

                    raw_answer = data.get("answer") or ""
                    thought_process = data.get("thought_process") or []
                    sources = data.get("sources") or []

                    sample["actual_response"] = raw_answer[:RESPONSE_TRUNCATE]
                    sample["actual_contexts"] = sources[:5]
                    sample["actual_tools_called"] = [detect_tool(thought_process)]

                    logfire.info(
                        "✅ Response captured",
                        tool=sample["actual_tools_called"][0],
                        response_chars=len(raw_answer),
                        context_chunks=len(sources),
                    )

                except requests.exceptions.ConnectionError:
                    logfire.error(f"❌ Cannot reach the API at {API_URL} — is it running?")
                    sample["actual_response"] = ""
                    sample["actual_contexts"] = sample.get("relevant_contexts", [])
                    sample["actual_tools_called"] = ["unknown"]

                except Exception as e:
                    logfire.error(f"❌ Query failed: {e}")
                    sample["actual_response"] = ""
                    sample["actual_contexts"] = sample.get("relevant_contexts", [])
                    sample["actual_tools_called"] = ["unknown"]

            if progress_callback:
                progress_callback(i, n, question, "done", sample["actual_response"])

            if i < n - 1:
                time.sleep(DELAY_BETWEEN_CALLS)

    return dataset


def save_results(dataset: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(dataset, f, indent=2)


def load_golden_dataset() -> dict:
    golden_path = os.path.join(os.path.dirname(__file__), "datasets", "golden_dataset.json")
    with open(golden_path) as f:
        return json.load(f)
