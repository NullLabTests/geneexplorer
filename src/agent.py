"""GeneExplorer: A LangGraph-based agent for human genetics questions.

Usage:
    python -m src.agent
    # or
    from src.agent import create_gene_explorer_agent
    agent = create_gene_explorer_agent()

Supports multiple LLM backends via LLM_PROVIDER env var:
    LLM_PROVIDER=mistral  (default, requires MISTRAL_API_KEY)
    LLM_PROVIDER=openai   (requires OPENAI_API_KEY)
    LLM_PROVIDER=ollama   (uses local Ollama server)
"""

import os

from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from src.tools import search_ncbi_gene, fetch_ncbi_gene_by_id, search_trait_associations, web_search, fetch_pubmed_abstract
from src.prompts import SYSTEM_PROMPT

load_dotenv()


def _get_llm(model_name: str = None, temperature: float = 0):
    provider = os.getenv("LLM_PROVIDER", "mistral").lower().strip()

    if provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY not set. Add it to .env or export it.")
        return ChatMistralAI(
            model=model_name or "open-mistral-nemo",
            temperature=temperature,
            api_key=api_key,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. Add it to .env or export it.")
        return ChatOpenAI(
            model=model_name or "gpt-4o-mini",
            temperature=temperature,
            api_key=api_key,
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model_name or "llama3.2",
            temperature=temperature,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )

    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set.")
        return ChatOpenAI(
            model=model_name or "mistralai/mistral-nemo",
            temperature=temperature,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Use: mistral, openai, ollama, openrouter"
        )


TOOLS = [
    search_ncbi_gene,
    fetch_ncbi_gene_by_id,
    search_trait_associations,
    web_search,
    fetch_pubmed_abstract,
]

TOOL_MAP = {tool.name: tool for tool in TOOLS}
TOOL_NODE = ToolNode(TOOLS)


# ── Custom StateGraph ──────────────────────────────────────────────────

class AgentState(MessagesState):
    """State maintained across turns (conversation history in messages)."""


def _make_call_model(model_name: str, temperature: float):
    """Return a call_model node function with model_name/temperature baked in."""

    def call_model(state: AgentState, config: RunnableConfig) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        llm = _get_llm(
            model_name=model_name,
            temperature=temperature,
        )
        response = llm.bind_tools(TOOLS).invoke(messages)
        return {"messages": [response]}

    return call_model


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def call_tool(state: AgentState) -> dict:
    return TOOL_NODE.invoke(state)


def create_gene_explorer_agent(
    model_name: str = None,
    temperature: float = 0,
    checkpointer: MemorySaver = None,
) -> object:
    """Create a GeneExplorer LangGraph agent with a custom StateGraph (ReAct loop).

    Parameters
    ----------
    model_name : str or None
        LLM model name (provider default used if None)
    temperature : float
        LLM temperature (default 0 for deterministic answers)
    checkpointer : MemorySaver or None
        If provided, enables conversation memory across invocations.

    Returns
    -------
    Compiled LangGraph StateGraph app
    """
    graph = StateGraph(AgentState)

    graph.add_node("agent", _make_call_model(model_name, temperature))
    graph.add_node("tools", call_tool)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)


def run_query(
    query: str,
    model_name: str = None,
    temperature: float = 0,
    thread_id: str = None,
    verbose: bool = False,
) -> str:
    """Run a genetics query through the GeneExplorer agent with optional conversation memory.

    Parameters
    ----------
    query : str
        The user's question.
    model_name : str or None
        LLM model name.
    temperature : float
        LLM temperature.
    thread_id : str or None
        Conversation thread ID for memory. Use same ID across calls for follow-ups.
    verbose : bool
        Print agent steps if True.

    Returns
    -------
    str
        The agent's final answer.
    """
    memory = MemorySaver() if thread_id else None
    agent = create_gene_explorer_agent(
        model_name=model_name,
        temperature=temperature,
        checkpointer=memory,
    )

    config = {
        "configurable": {
            "thread_id": thread_id or "default",
        }
    }

    if verbose:
        print(f"\n{'='*60}")
        print(f"GeneExplorer Query: {query}")
        print(f"{'='*60}\n")

    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
        config=config,
    )

    final_answer = result["messages"][-1].content

    if verbose:
        print(f"\n{'='*60}")
        print("Final Answer:")
        print(f"{'='*60}")
        print(final_answer)

    return final_answer


def main():
    """CLI entry point with conversation memory."""
    import argparse

    parser = argparse.ArgumentParser(
        description="GeneExplorer: AI agent for human genetics questions"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Genetics question to answer (if omitted, starts interactive session)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model name (default depends on LLM_PROVIDER)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0,
        help="LLM temperature (default: 0)",
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Conversation thread ID for follow-up memory (default: auto per session)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print agent steps",
    )

    args = parser.parse_args()

    provider = os.getenv("LLM_PROVIDER", "mistral")

    if args.query:
        answer = run_query(
            query=args.query,
            model_name=args.model,
            temperature=args.temperature,
            thread_id=args.thread_id,
            verbose=args.verbose,
        )
        print(answer)
    else:
        import uuid
        session_id = args.thread_id or str(uuid.uuid4())
        memory = MemorySaver()
        agent = create_gene_explorer_agent(
            model_name=args.model,
            temperature=args.temperature,
            checkpointer=memory,
        )
        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }

        print(f"GeneExplorer Interactive Mode (LLM_PROVIDER={provider})")
        print(f"Session: {session_id}")
        print("Type 'exit', 'quit', or Ctrl+C to stop.\n")

        while True:
            try:
                query = input(">>> ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if query.lower().strip() in ("exit", "quit"):
                print("Goodbye.")
                break

            if not query.strip():
                continue

            result = agent.invoke(
                {"messages": [HumanMessage(content=query)]},
                config=config,
            )
            print(result["messages"][-1].content)
            print()


if __name__ == "__main__":
    main()
