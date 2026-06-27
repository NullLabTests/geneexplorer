#!/usr/bin/env python3
"""GeneExplorer Streamlit frontend — chat-like UI with conversation memory."""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from dotenv import load_dotenv

from src.agent import create_gene_explorer_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

st.set_page_config(
    page_title="GeneExplorer",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🧬 GeneExplorer")
    st.markdown(
        "An AI agent that answers human genetics questions using "
        "**NCBI Gene**, **GWAS Catalog**, and **PubMed** — all public-domain data."
    )
    st.divider()

    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()
    st.markdown(f"**LLM Backend:** `{provider}`")

    if provider == "ollama":
        st.info("Running with local Ollama — no API key needed.")
    elif provider == "mistral":
        if os.getenv("MISTRAL_API_KEY"):
            st.success("Mistral AI API key configured.")
        else:
            st.error("MISTRAL_API_KEY not set!")
    elif provider == "openai":
        if os.getenv("OPENAI_API_KEY"):
            st.success("OpenAI API key configured.")
        else:
            st.error("OPENAI_API_KEY not set!")

    st.divider()

    model_name = st.text_input(
        "Model name (optional)",
        value=os.getenv("LLM_MODEL", ""),
        placeholder="e.g. llama3.2, gpt-4o-mini, open-mistral-nemo",
    )
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.05)

    st.divider()

    if st.button("🧹 New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.agent = None
        st.rerun()

    st.divider()
    st.caption(
        "⚠️ This is for educational purposes only. "
        "Not medical or genetic counseling advice."
    )

# ── Session state ──────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "agent" not in st.session_state or st.session_state.agent is None:
    memory = MemorySaver()
    st.session_state.agent = create_gene_explorer_agent(
        model_name=model_name if model_name else None,
        temperature=temperature,
        checkpointer=memory,
    )
    st.session_state.memory = memory

# ── Config ─────────────────────────────────────────────────────────────

agent_config = {
    "configurable": {
        "thread_id": st.session_state.thread_id,
    }
}

# ── Chat UI ────────────────────────────────────────────────────────────

st.title("🧬 GeneExplorer")
st.markdown("Ask any human genetics question.")

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("e.g. What genes are associated with blonde hair?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching NCBI, GWAS Catalog, PubMed..."):
            try:
                result = st.session_state.agent.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    config=agent_config,
                )
                answer = result["messages"][-1].content
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
            except Exception as e:
                err_msg = f"⚠️ Error: {e}"
                st.error(err_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": err_msg}
                )

# ── Footer ─────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Data sourced from "
    "[NCBI Gene](https://www.ncbi.nlm.nih.gov/gene), "
    "[GWAS Catalog](https://www.ebi.ac.uk/gwas/), and "
    "[PubMed](https://pubmed.ncbi.nlm.nih.gov/). "
    "Built with LangGraph."
)
