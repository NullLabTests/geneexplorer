#!/usr/bin/env python3
"""Comprehensive GeneExplorer tool & agent verification script."""

import sys
sys.path.insert(0, '.')

print('=' * 70)
print('GENEEXPLORER -- TOOL & AGENT VERIFICATION')
print('=' * 70)

# 1. NCBI Gene Tool
from src.tools import search_ncbi_gene
print()
print('>>> [Tool 1] search_ncbi_gene("MC1R")')
result = search_ncbi_gene.invoke('MC1R')
print(result[:600])
print('...')

# 2. NCBI Gene by ID
from src.tools import fetch_ncbi_gene_by_id
print()
print('>>> [Tool 2] fetch_ncbi_gene_by_id("4157")')
result = fetch_ncbi_gene_by_id.invoke('4157')
print(result[:500])
print('...')

# 3. GWAS trait search
from src.tools import search_trait_associations
print()
print('>>> [Tool 3] search_trait_associations("hair color")')
result = search_trait_associations.invoke('hair color')
print(result[:1000])
print('...')

# 4. PubMed search
from src.tools import web_search
print()
print('>>> [Tool 4] web_search("MC1R gene hair color GWAS")')
result = web_search.invoke('MC1R gene hair color GWAS')
print(result[:1000])
print('...')

# 5. Full agent query
from src.agent import run_query
print()
print('>>> [Agent] run_query("What genes are associated with blonde hair?")')
answer = run_query('What genes are associated with blonde hair?', model_name='llama3.2:1b')
print()
print('FINAL ANSWER:')
print(answer)
