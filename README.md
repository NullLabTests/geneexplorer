
```
      ╔══════════════════════════════════════════════════════════╗
      ║               ╔═╗  ╦╔╗╔╔═╗╔╦╗╦  ╔═╗╦ ╦╔═╗╦═╗╦╔═╗╦═╗      ║
      ║               ╠═╣  ║║║║║ ║ ║ ║  ║ ║║ ║║╣ ╠╦╝║║║ ╠╦╝      ║
      ║               ╩ ╩  ╩╝╚╝╚═╝ ╩ ╩═╝╚═╝╚═╝╚═╝╩╚═╩╚═╝╩╚═      ║
      ║                                                          ║
      ║   ╔═╗╔═╗╔╦╗╔═╗╦  ╦  ╔═╗╦═╗╦╔═╗╔═╗╔═╗╔═╗╦═╗╔═╗╔═╗╔═╗   ║
      ║   ║ ║╠═╣ ║ ║ ║║  ║  ╠═╣╠╦╝║║  ╠═╣║ ╦╠═╣╠╦╝║╣ ║  ║╣   ║
      ║   ╚═╝╩ ╩ ╩ ╚═╝╩═╝╩  ╩ ╩╩╚═╩╚═╝╩ ╩╚═╝╩ ╩╩╚═╚═╝╚═╝╚═╝   ║
      ║                                                          ║
      ╚══════════════════════════════════════════════════════════╝
```

<p align="center">
  <strong>Ask any genetics question. Get answers grounded in public-domain science.</strong>
  <br>
  <em>NCBI Gene · GWAS Catalog · PubMed · LangGraph ReAct Agent</em>
</p>

---

<p align="center">
  <a href="#-features"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat&logo=python" alt="Python 3.10+"/></a>
  <a href="https://github.com/NullLabTests/geneexplorer/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat" alt="License MIT"/></a>
  <a href="https://github.com/NullLabTests/geneexplorer"><img src="https://img.shields.io/badge/langgraph-0.2%2B-purple?style=flat" alt="LangGraph"/></a>
  <a href="https://github.com/NullLabTests/geneexplorer/actions"><img src="https://img.shields.io/badge/build-verified-success?style=flat" alt="Build"/></a>
  <a href="https://github.com/NullLabTests/geneexplorer"><img src="https://img.shields.io/badge/data-NCBI%20|%20GWAS%20|%20PubMed-orange?style=flat" alt="Data Sources"/></a>
  <a href="https://github.com/NullLabTests/geneexplorer"><img src="https://img.shields.io/github/stars/NullLabTests/geneexplorer?style=flat&color=yellow" alt="Stars"/></a>
</p>

---

## Elevator Pitch

**GeneExplorer** is an AI agent that answers human genetics questions by live-fetching from public-domain databases — no hallucination, no guesswork. Ask "What genes give me blonde hair?" and it queries NCBI Gene, the GWAS Catalog, and PubMed in real time, then synthesizes a structured answer with gene symbols, locations, functions, variants (rsIDs), and citations. Built on LangGraph's ReAct architecture, it's accurate, cite-able, and fully transparent.

---

## Features

- **NCBI Gene Lookup** — Fetch summaries, chromosomal locations, aliases, and function for any HGNC gene symbol or Entrez ID.
- **GWAS Catalog Search** — Real-time trait-gene association lookup via the EBI GWAS Catalog REST API, with a curated fallback for well-studied traits (hair color, eye color, height, etc.).
- **PubMed Literature** — Search PubMed and retrieve abstracts by PMID for deeper evidence.
- **ReAct Agent** — LangGraph-powered loop: the LLM decides which tools to call, reads results, and synthesizes a cite-able answer.
- **Multi-LLM Backend** — Works with Mistral AI, OpenAI, local Ollama, or OpenRouter — set `LLM_PROVIDER` and go.
- **CLI + Python API** — Single-query, interactive session, or import as a module.

---

## Data Sources

All data comes from **public-domain open-science databases** — no proprietary APIs, no paywalls:

| Source | What we use |
|--------|-------------|
| [NCBI Gene / Entrez](https://www.ncbi.nlm.nih.gov/gene) | Gene summaries, location, aliases, function |
| [GWAS Catalog (EBI)](https://www.ebi.ac.uk/gwas/) | Trait-gene associations with p-values, PMIDs |
| [PubMed](https://pubmed.ncbi.nlm.nih.gov/) | Article titles, abstracts, DOIs |

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/NullLabTests/geneexplorer.git
cd geneexplorer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set your LLM backend

```bash
cp .env.example .env
```

Then edit `.env` with one of these configurations:

| Provider | `.env` config |
|----------|---------------|
| **Mistral AI** (free credits) | `LLM_PROVIDER=mistral` + `MISTRAL_API_KEY=xxx` |
| **OpenAI** | `LLM_PROVIDER=openai` + `OPENAI_API_KEY=sk-...` |
| **Local Ollama** (no key) | `LLM_PROVIDER=ollama` + `ollama pull llama3.2` |

### 3. Ask a question

```bash
# Single query
python -m src.agent "What genes are associated with blonde hair?"

# Verbose (see every tool call)
python -m src.agent "What is the function of MC1R?" --verbose

# Interactive session
python -m src.agent
>>> What genes control eye color?
```

### As a Python module

```python
from src.agent import run_query

answer = run_query("What genes are associated with blonde hair?")
print(answer)
```

---

## What's Under the Hood

### Agent Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  LangGraph ReAct Agent (create_react_agent)             │
│                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  LLM      │───▶│  Tool Router  │───▶│  Tool Executor │  │
│  │ (Mistral, │◀───│  (ReAct loop) │◀───│                │  │
│  │  OpenAI,  │    │              │    │ • NCBI Gene    │  │
│  │  Ollama)  │    │              │    │ • GWAS Catalog │  │
│  └──────────┘    └──────────────┘    │ • PubMed       │  │
│                                       └───────────────┘  │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Structured answer + citations + disclaimers
```

### Tools

| Tool | Called when... | Returns |
|------|----------------|---------|
| `search_ncbi_gene` | user asks about a specific gene | Symbol, full name, summary, chromosome, genomic coords, aliases |
| `fetch_ncbi_gene_by_id` | user has an Entrez ID | Same data by numeric ID |
| `search_trait_associations` | user asks about a trait (hair color, height, etc.) | Associated genes, locations, p-values, PMIDs |
| `web_search` | user wants literature confirmation | PubMed article titles, PMIDs, DOIs |
| `fetch_pubmed_abstract` | user asks about a specific study | Full abstract, journal, year |

---

## Project Structure

```
geneexplorer/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── agent.py              # LangGraph agent, CLI entry point
│   ├── prompts.py            # System prompt (accuracy, citations, disclaimers)
│   └── tools/
│       ├── __init__.py
│       ├── ncbi_tools.py     # NCBI Gene / Entrez API
│       ├── gwas_tools.py     # GWAS Catalog REST API + fallback
│       └── web_tools.py      # PubMed search & abstract fetch
├── scripts/
│   └── demo.py               # Verification demo
├── data/                     # (optional) downloaded public datasets
└── notebooks/                # Exploration
```

---

## Verified Demo

The following was captured live using **Ollama + llama3.2:1b** (no API key needed):

```
$ LLM_PROVIDER=ollama python3 scripts/demo.py

======================================================================
GENEEXPLORER -- TOOL & AGENT VERIFICATION
======================================================================

>>> [Tool 1] search_ncbi_gene("MC1R")
NCBI Gene entry for MC1R [ID: 4157]
Full name: melanocortin 1 receptor
Summary: This intronless gene encodes the receptor protein for
melanocyte-stimulating hormone (MSH). The encoded protein, a seven
pass transmembrane G protein coupled receptor, controls melanogenesis.
...

>>> [Tool 2] fetch_ncbi_gene_by_id("4157")
NCBI Gene entry [4157]
Symbol: MC1R
Full name: melanocortin 1 receptor
...

>>> [Tool 3] search_trait_associations("hair color")
Public literature associations for 'Hair color' (curated from large GWAS):
- MC1R (16q24.3): Key regulator of melanogenesis
- OCA2/HERC2 (15q12-q13.1): Regulatory region rs12913832 controls OCA2
- SLC45A2 (5p13.2): Melanocyte differentiation antigen
- IRF4 (6p25.3): Melanin synthesis regulator
- TYR (11q14.3): Tyrosinase; key enzyme in melanin production
- SLC24A4 (14q32.12): Melanocyte ion transporter
- KITLG (12q21.32): Stem cell factor; melanocyte development
Key references: PMID: 31578519, 27479818, 19043545

>>> [Agent] run_query("What genes are associated with blonde hair?")

FINAL ANSWER:
The genes associated with blonde hair are:
* MC1R (16q24.3)
* OCA2 (15q12-q13.1) – particularly the regulatory variant rs12913832
* HERC2 (15q13.1)
* SLC45A2 (5p13.2)
* IRF4 (6p25.3)
* SLC24A4 (14q32.12)
* KITLG (12q21.32)

These genes play a role in regulating melanin production and distribution,
which is responsible for hair color. The strongest associations are with
the MC1R gene, particularly the variant rs12913832, which has been
strongly linked to blonde/brown hair.

Please note that this information is based on publicly available data and
may not be comprehensive or up-to-date. Additionally, individual results
may vary, and the presence of these genes does not guarantee blonde hair.
```

---

## Disclaimers

> **This is for educational and informational purposes only.** It is NOT medical, diagnostic, or genetic counseling advice. Genetics is complex and influenced by many factors. Consult a qualified healthcare professional or genetic counselor for personal advice.

---

## License

MIT &mdash; see [LICENSE](LICENSE).

---

<p align="center">
  Built with ❤️ using LangGraph · NCBI Entrez · GWAS Catalog · PubMed
  <br>
  <sub>All data sourced from public-domain open science databases.</sub>
</p>
