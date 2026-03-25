# backend/graph/graph_runner.py

from typing import Dict, Any

from agents.retriever_agent import retriever_agent
from agents.generator_agent import generator_agent
from agents.fact_checker_agent import fact_checker_agent
from agents.citation_agent import citation_agent
from agents.summarizer import summariser_agent


async def run_graph(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    GRAPH RUNNER

    Executes the agent graph in a fixed order.
    Acts as a lightweight orchestration layer.
    """

    state = initial_state

    # 1️⃣ Retrieval
    state = await retriever_agent(state)

    # 2️⃣ Generation (RAG)
    state = await generator_agent(state)

    # 3️⃣ Fact checking
    state = await fact_checker_agent(state)

    # 4️⃣ Citations
    state = await citation_agent(state)

    # 5️⃣ Summarisation (optional, UI-facing)
    state = await summariser_agent(state)

    return state
