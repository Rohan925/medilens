import logging

from langgraph.graph import END, START, StateGraph

from app.graph.agents.citation_agent import citation_agent
from app.graph.agents.medicine_resolver_agent import medicine_resolver_agent
from app.graph.agents.ocr_agent import ocr_agent
from app.graph.agents.response_formatter_agent import response_formatter_agent
from app.graph.agents.summarizer_agent import summarizer_agent
from app.graph.state import GraphState

logger = logging.getLogger("graph.ocr")


def build_ocr_graph():
    graph = StateGraph(GraphState)

    graph.add_node("ocr", ocr_agent)
    graph.add_node("medicine_resolver", medicine_resolver_agent)
    graph.add_node("summarizer", summarizer_agent)
    graph.add_node("citation", citation_agent)
    graph.add_node("formatter", response_formatter_agent)

    graph.add_edge(START, "ocr")
    graph.add_conditional_edges(
        "ocr",
        lambda state: "resolve" if state.medicine_name else "format",
        {
            "resolve": "medicine_resolver",
            "format": "formatter",
        },
    )
    graph.add_edge("medicine_resolver", "summarizer")
    graph.add_edge("summarizer", "citation")
    graph.add_edge("citation", "formatter")
    graph.add_edge("formatter", END)

    return graph.compile()


ocr_graph = build_ocr_graph()


def run_ocr_graph(state: GraphState) -> GraphState:
    logger.info("Graph start: ocr_graph")
    result = ocr_graph.invoke(state)
    if isinstance(result, GraphState):
        logger.info("Graph end: ocr_graph")
        return result
    final_state = GraphState.model_validate(result)
    logger.info("Graph end: ocr_graph")
    return final_state
