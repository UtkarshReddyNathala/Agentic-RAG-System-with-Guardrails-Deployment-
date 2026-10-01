"""Locust load test for the RAG API `/query` endpoint.

The target host and API key are always supplied at runtime; nothing about a
specific deployment is stored in this file.

Usage (headless):
    pip install locust
    export RAG_API_KEY=<your-key>
    locust -f scripts/testing/locustfile.py \\
      --headless -u 5 -r 1 -t 10m \\
      --host https://your-api-host

Usage (web UI at http://localhost:8089):
    locust -f scripts/testing/locustfile.py --host https://your-api-host

Each /query call runs the full agent pipeline (roughly 30-50 s), so allow a
generous run time or raise the user count for a short burst.
"""

import os
import random

from locust import HttpUser, between, task

RAG_API_KEY = os.environ.get("RAG_API_KEY")
if not RAG_API_KEY:
    raise RuntimeError("RAG_API_KEY environment variable is required.")

# Questions covering different topics in the indexed corpus.
SAMPLE_QUESTIONS = [
    "What is a Kubernetes pod?",
    "Explain the difference between a process and a thread.",
    "What is a REST API and how does it work?",
    "How does a database index improve query performance?",
    "What is the purpose of a load balancer in a web application?",
]


class RAGQueryUser(HttpUser):
    """Simulates a user asking questions to the RAG `/query` endpoint."""

    # 1-5 s of think time between requests. Use between(0, 0) for a pure stress test.
    wait_time = between(1, 5)

    @task
    def query(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RAG_API_KEY}",
        }
        payload = {
            "q": random.choice(SAMPLE_QUESTIONS),
            "thread_id": f"locust-{random.randint(1, 1_000_000)}",
        }
        with self.client.post(
            "/query",
            json=payload,
            headers=headers,
            catch_response=True,
            name="/query",
            timeout=60,
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}")
                return
            try:
                data = response.json()
            except Exception as exc:
                response.failure(f"Invalid JSON: {exc}")
                return
            if data.get("status") == "error":
                response.failure(f"API error: {data.get('message')}")
            else:
                response.success()
