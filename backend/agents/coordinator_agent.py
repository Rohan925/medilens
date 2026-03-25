from typing import Dict, Any
from agents.retriever_agent import retriever_agent
from agents.summarizer import summariser_agent
from agents.citation_agent import citation_agent
from agents.generator_agent import generator_agent


async def coordinator_agent(initial_state: Dict[str, Any]) -> Dict[str, Any]:

    state = initial_state

    state = await retriever_agent(state)
    state = await summariser_agent(state)
    state = await generator_agent(state)
    state = await citation_agent(state)

    return state
