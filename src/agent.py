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
import sys

from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from src.tools import search_ncbi_gene, fetch_ncbi_gene_by_id, search_trait_associations, web_search, fetch_pubmed_abstract
from src.prompts import SYSTEM_PROMPT

load_dotenv()


def _get_llm(model_name: str = None, temperature: float = 0):
    provider = os.getenv("LLM_PROVIDER", "mistral").lower().strip()
    api_key = None

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


def create_gene_explorer_agent(
    model_name: str = None,
    temperature: float = 0,
    verbose: bool = False,
) -> object:
    """Create a GeneExplorer LangGraph ReAct agent.

    Parameters
    ----------
    model_name : str or None
        LLM model name (provider default used if None)
    temperature : float
        LLM temperature (default 0 for deterministic answers)
    verbose : bool
        Not used directly here; use run_query(verbose=True)

    Returns
    -------
    Compiled LangGraph agent
    """
    llm = _get_llm(model_name=model_name, temperature=temperature)

    tools = [
        search_ncbi_gene,
        fetch_ncbi_gene_by_id,
        search_trait_associations,
        web_search,
        fetch_pubmed_abstract,
    ]

    agent = create_react_agent(
        llm,
        tools,
        state_modifier=SystemMessage(content=SYSTEM_PROMPT),
    )

    return agent


def run_query(
    query: str,
    model_name: str = None,
    temperature: float = 0,
    verbose: bool = False,
) -> str:
    """Run a single genetics query through the GeneExplorer agent.

    Parameters
    ----------
    query : str
        The user's question (e.g., "What genes are associated with blonde hair?")
    model_name : str or None
        LLM model name
    temperature : float
        LLM temperature
    verbose : bool
        Print agent steps

    Returns
    -------
    str
        The agent's final answer
    """
    agent = create_gene_explorer_agent(
        model_name=model_name,
        temperature=temperature,
        verbose=verbose,
    )

    if verbose:
        print(f"\n{'='*60}")
        print(f"GeneExplorer Query: {query}")
        print(f"{'='*60}\n")

    result = agent.invoke({
        "messages": [HumanMessage(content=query)],
    })

    final_answer = result["messages"][-1].content

    if verbose:
        print(f"\n{'='*60}")
        print("Final Answer:")
        print(f"{'='*60}")
        print(final_answer)

    return final_answer


def main():
    """CLI entry point for interactive GeneExplorer session."""
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
            verbose=args.verbose,
        )
        print(answer)
    else:
        print(f"GeneExplorer Interactive Mode (LLM_PROVIDER={provider})")
        print("Type 'exit', 'quit', or Ctrl+C to stop.\n")
        agent = create_gene_explorer_agent(
            model_name=args.model,
            temperature=args.temperature,
            verbose=args.verbose,
        )

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

            result = agent.invoke({
                "messages": [HumanMessage(content=query)],
            })
            print(result["messages"][-1].content)
            print()


if __name__ == "__main__":
    main()
