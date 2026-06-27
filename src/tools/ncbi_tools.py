import os
import re
import requests
from xml.etree import ElementTree as ET
from langchain_core.tools import tool

NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")
ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _parse_ncbi_summary(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    gene = {}

    gene_id_el = root.find(".//Gene-track/Gene-track_geneid")
    if gene_id_el is not None:
        gene["gene_id"] = gene_id_el.text

    symbol_el = root.find(".//Gene-ref/Gene-ref_locus")
    if symbol_el is not None:
        gene["symbol"] = symbol_el.text

    fullname_el = root.find(".//Gene-ref/Gene-ref_desc")
    if fullname_el is not None:
        gene["full_name"] = fullname_el.text

    summary_el = root.find(".//Entrezgene_summary")
    if summary_el is not None:
        gene["summary"] = summary_el.text.strip()

    chrom_el = root.find(".//Entrezgene_location")
    if chrom_el is not None:
        gene["chromosome"] = chrom_el.text.strip()

    # Extract genomic coordinates
    map_el = root.find(".//Entrezgene_genomic-unit")
    if map_el is not None:
        interval = map_el.find(".//Seq-interval")
        if interval is not None:
            from_el = interval.find(".//Seq-interval_from")
            to_el = interval.find(".//Seq-interval_to")
            if from_el is not None and to_el is not None:
                gene["genomic_start"] = from_el.text
                gene["genomic_end"] = to_el.text

    aliases_el = root.findall(".//Gene-ref/Gene-ref_synonym")
    if aliases_el:
        gene["aliases"] = [a.text for a in aliases_el if a.text]

    return gene


def _fetch_ncbi_xml(db: str, gene_id: str) -> str:
    params = {"db": db, "id": gene_id, "rettype": "xml"}
    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL
    url = f"{ENTREZ_BASE}/efetch.fcgi"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text


@tool
def search_ncbi_gene(gene_symbol: str) -> str:
    """Search NCBI Gene database for a human gene symbol and return summary, location, and function. Input should be an HGNC gene symbol (e.g., 'MC1R', 'OCA2')."""

    # Step 1: ESearch for the gene symbol
    search_params = {
        "db": "gene",
        "term": f"{gene_symbol}[sym] AND human[orgn]",
        "retmax": 1,
        "retmode": "json",
    }
    if NCBI_EMAIL:
        search_params["email"] = NCBI_EMAIL

    try:
        search_resp = requests.get(
            f"{ENTREZ_BASE}/esearch.fcgi",
            params=search_params,
            timeout=30,
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()
    except Exception as e:
        return f"Error searching NCBI for {gene_symbol}: {e}"

    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return f"No results found for gene symbol '{gene_symbol}' in NCBI Gene."

    gene_id = id_list[0]

    # Step 2: EFetch detailed record in XML
    try:
        xml_text = _fetch_ncbi_xml("gene", gene_id)
    except Exception as e:
        return f"Error fetching NCBI record for {gene_symbol} (ID: {gene_id}): {e}"

    gene_info = _parse_ncbi_summary(xml_text)

    lines = [
        f"NCBI Gene entry for {gene_info.get('symbol', gene_symbol)} [ID: {gene_info.get('gene_id', gene_id)}]",
    ]
    if gene_info.get("full_name"):
        lines.append(f"Full name: {gene_info['full_name']}")
    if gene_info.get("chromosome"):
        lines.append(f"Chromosomal location: {gene_info['chromosome']}")
    if gene_info.get("genomic_start"):
        coords = f"{gene_info['genomic_start']} - {gene_info['genomic_end']}"
        lines.append(f"Genomic coordinates (0-based): {coords}")
    if gene_info.get("aliases"):
        lines.append(f"Aliases: {', '.join(gene_info['aliases'])}")
    if gene_info.get("summary"):
        summary = gene_info["summary"]
        if len(summary) > 2000:
            summary = summary[:2000] + "..."
        lines.append(f"Summary: {summary}")

    return "\n".join(lines)


@tool
def fetch_ncbi_gene_by_id(gene_id: str) -> str:
    """Fetch NCBI Gene record by Entrez Gene ID (e.g., '4157' for MC1R)."""
    try:
        xml_text = _fetch_ncbi_xml("gene", gene_id)
    except Exception as e:
        return f"Error fetching NCBI Gene record for ID {gene_id}: {e}"

    gene_info = _parse_ncbi_summary(xml_text)
    if not gene_info:
        return f"Could not parse NCBI record for Gene ID {gene_id}."

    lines = [
        f"NCBI Gene entry [{gene_info.get('gene_id', gene_id)}]",
    ]
    if gene_info.get("symbol"):
        lines.append(f"Symbol: {gene_info['symbol']}")
    if gene_info.get("full_name"):
        lines.append(f"Full name: {gene_info['full_name']}")
    if gene_info.get("chromosome"):
        lines.append(f"Chromosomal location: {gene_info['chromosome']}")
    if gene_info.get("summary"):
        summary = gene_info["summary"]
        if len(summary) > 2000:
            summary = summary[:2000] + "..."
        lines.append(f"Summary: {summary}")

    return "\n".join(lines)
