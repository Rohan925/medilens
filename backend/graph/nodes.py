# backend/graph/nodes.py

from graph.state import GraphState

from agents.retriever_agent import retriever_agent
from agents.generator_agent import generator_agent
from agents.fact_checker_agent import fact_checker_agent
from agents.citation_agent import citation_agent
from agents.summarizer import summariser_agent


async def retriever_node(state: GraphState) -> GraphState:
    """
    Graph node for retrieval.
    """
    return await retriever_agent(state)


async def generator_node(state: GraphState) -> GraphState:
    """
    Graph node for answer generation.
    """
    return await generator_agent(state)


async def fact_checker_node(state: GraphState) -> GraphState:
    """
    Graph node for fact checking.
    """
    return await fact_checker_agent(state)


async def citation_node(state: GraphState) -> GraphState:
    """
    Graph node for citation extraction.
    """
    return await citation_agent(state)


async def summariser_node(state: GraphState) -> GraphState:
    """
    Graph node for summarisation.
    """
    return await summariser_agent(state)
