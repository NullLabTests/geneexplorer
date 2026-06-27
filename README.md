# GeneExplorer

A LangGraph-powered AI agent that answers human genetics questions using public domain data from NCBI Gene/Entrez, GWAS Catalog, and PubMed.

## Features

- **NCBI Gene Lookup** — Fetches gene summaries, chromosomal locations, genomic coordinates, aliases, and function from the NCBI Entrez API.
- **GWAS Catalog Search** — Queries the GWAS Catalog REST API for trait-gene associations (e.g., hair color, eye color). Includes a curated fallback for well-studied traits when the API is unavailable.
- **PubMed Search & Abstracts** — Searches PubMed literature and fetches article abstracts for deeper evidence.
- **ReAct Agent** — Uses LangGraph's prebuilt `create_react_agent` with a system prompt enforcing accuracy, citations, polygenic nuance, and disclaimers.
- **CLI & Python API** — Use interactively or import as a module.

## Data Sources

All data is from **public domain sources**:
- [NCBI Gene / Entrez](https://www.ncbi.nlm.nih.gov/gene)
- [GWAS Catalog (EBI)](https://www.ebi.ac.uk/gwas/)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/nulllabtests/geneexplorer.git
cd geneexplorer
pip install -r requirements.txt
```

### 2. Set up your LLM backend

GeneExplorer supports multiple LLM providers. Set `LLM_PROVIDER` in `.env`:

```bash
cp .env.example .env
```

**Option A: Mistral AI (recommended, free credits available)**
```
LLM_PROVIDER=mistral
MISTRAL_API_KEY=xxx     # from https://console.mistral.ai
```

**Option B: OpenAI**
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...   # from https://platform.openai.com
```

**Option C: Local with Ollama (no API key needed)**
```
LLM_PROVIDER=ollama
# Then pull a model: ollama pull llama3.2
```

### 3. Run the agent

**Single query:**
```bash
python -m src.agent "What genes are associated with blonde hair?"
```

**Verbose mode (shows tool calls):**
```bash
python -m src.agent "What is the function of the MC1R gene?" --verbose
```

**Interactive session:**
```bash
python -m src.agent
>>> What genes are associated with eye color?
```

**As a Python module:**
```python
from src.agent import run_query

answer = run_query("What genes are related to blonde hair?")
print(answer)
```

## Project Structure

```
geneexplorer/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── agent.py              # Main agent + CLI entry point
│   ├── prompts.py            # System prompt
│   └── tools/
│       ├── __init__.py
│       ├── ncbi_tools.py     # NCBI Gene / Entrez tools
│       ├── gwas_tools.py     # GWAS Catalog search + fallback
│       └── web_tools.py      # PubMed search & abstract fetch
├── data/                     # (optional) Downloaded public datasets
├── notebooks/                # Exploration notebooks
└── tests/
```

## Tools Available to the Agent

| Tool | Description |
|------|-------------|
| `search_ncbi_gene` | Look up a human gene symbol (e.g., MC1R) in NCBI Gene — returns summary, location, function |
| `fetch_ncbi_gene_by_id` | Fetch NCBI Gene record by Entrez Gene ID |
| `search_trait_associations` | Search GWAS Catalog for gene-trait associations (e.g., "blonde hair") |
| `web_search` | Search PubMed for articles related to a query |
| `fetch_pubmed_abstract` | Retrieve the abstract of a specific article by PMID |

## Example Output

### Verified Demo (run with Ollama + llama3.2:1b)

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
Two types of melanin exist: red pheomelanin and black eumelanin. Gene
mutations that lead to a loss in function are associated with increased
pheomelanin production, which leads to lighter skin and hair color.
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
* OCA2 (15q12-q13.1) - particularly the regulatory variant rs12913832
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

## Disclaimers

> This is for **educational and informational purposes only**. It is NOT medical, diagnostic, or genetic counseling advice. Genetics is complex and influenced by many factors. Consult a qualified healthcare professional or genetic counselor for personal advice.

## License

MIT

---

*Built with LangGraph, NCBI Entrez, GWAS Catalog, and PubMed — all public data sources.*
