import os
import requests
from xml.etree import ElementTree as ET
from langchain_core.tools import tool

NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")
ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

_BIOPYTHON_AVAILABLE = False
try:
    from Bio import Entrez
    Entrez.email = NCBI_EMAIL or "anonymous@geneexplorer.local"
    _BIOPYTHON_AVAILABLE = True
except ImportError:
    pass


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

    map_el = root.find(".//Entrezgene_genomic-unit")
    if map_el is not None:
        for unit in root.findall(".//Entrezgene_genomic-unit"):
            interval = unit.find(".//Seq-interval")
            if interval is not None:
                from_el = interval.find(".//Seq-interval_from")
                to_el = interval.find(".//Seq-interval_to")
                if from_el is not None and to_el is not None:
                    gene["genomic_start"] = from_el.text
                    gene["genomic_end"] = to_el.text
                    break

    aliases_el = root.findall(".//Gene-ref/Gene-ref_synonym")
    if aliases_el:
        gene["aliases"] = [a.text for a in aliases_el if a.text]

    return gene


def _biopython_search_gene(gene_symbol: str) -> tuple:
    from Bio import Entrez
    handle = Entrez.esearch(
        db="gene",
        term=f"{gene_symbol}[sym] AND human[orgn]",
        retmax=1,
    )
    record = Entrez.read(handle)
    handle.close()
    id_list = record.get("IdList", [])
    if not id_list:
        return None, f"No results found for '{gene_symbol}' in NCBI Gene."
    gene_id = id_list[0]
    handle = Entrez.efetch(db="gene", id=gene_id, rettype="xml")
    xml_data = handle.read()
    handle.close()
    return xml_data, None


def _biopython_fetch_by_id(gene_id: str) -> tuple:
    from Bio import Entrez
    handle = Entrez.efetch(db="gene", id=gene_id, rettype="xml")
    xml_data = handle.read()
    handle.close()
    return xml_data, None


def _requests_search_gene(gene_symbol: str) -> tuple:
    search_params = {
        "db": "gene",
        "term": f"{gene_symbol}[sym] AND human[orgn]",
        "retmax": 1,
        "retmode": "json",
    }
    if NCBI_EMAIL:
        search_params["email"] = NCBI_EMAIL
    search_resp = requests.get(
        f"{ENTREZ_BASE}/esearch.fcgi",
        params=search_params,
        timeout=30,
    )
    search_resp.raise_for_status()
    search_data = search_resp.json()
    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return None, f"No results found for '{gene_symbol}' in NCBI Gene."
    gene_id = id_list[0]
    fetch_params = {"db": "gene", "id": gene_id, "rettype": "xml"}
    if NCBI_EMAIL:
        fetch_params["email"] = NCBI_EMAIL
    fetch_resp = requests.get(
        f"{ENTREZ_BASE}/efetch.fcgi",
        params=fetch_params,
        timeout=30,
    )
    fetch_resp.raise_for_status()
    return fetch_resp.text, None


def _format_gene_output(gene_info: dict, gene_symbol: str, gene_id: str) -> str:
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
def search_ncbi_gene(gene_symbol: str) -> str:
    """Search NCBI Gene database for a human gene symbol and return summary, location, and function. Input should be an HGNC gene symbol (e.g., 'MC1R', 'OCA2')."""

    xml_text = None
    err = None
    gene_id = None

    # Try Biopython first (cleaner parsing)
    if _BIOPYTHON_AVAILABLE:
        try:
            result, err = _biopython_search_gene(gene_symbol)
            if err:
                return err
            xml_text, _ = result, None
        except Exception as e:
            err = str(e)

    # Fall back to requests-based approach
    if xml_text is None:
        try:
            xml_text, err = _requests_search_gene(gene_symbol)
            if err:
                return err
        except Exception as e:
            return f"Error searching NCBI for {gene_symbol}: {e}"

    # Parse the XML
    try:
        gene_info = _parse_ncbi_summary(xml_text)
    except Exception as e:
        return f"Error parsing NCBI response for {gene_symbol}: {e}"

    if not gene_info.get("symbol"):
        gene_info["symbol"] = gene_symbol

    return _format_gene_output(
        gene_info,
        gene_symbol,
        gene_info.get("gene_id", "unknown"),
    )


@tool
def fetch_ncbi_gene_by_id(gene_id: str) -> str:
    """Fetch NCBI Gene record by Entrez Gene ID (e.g., '4157' for MC1R)."""

    xml_text = None

    if _BIOPYTHON_AVAILABLE:
        try:
            xml_text, err = _biopython_fetch_by_id(gene_id)
            if err:
                return err
        except Exception as e:
            pass

    if xml_text is None:
        try:
            fetch_params = {"db": "gene", "id": gene_id, "rettype": "xml"}
            if NCBI_EMAIL:
                fetch_params["email"] = NCBI_EMAIL
            resp = requests.get(
                f"{ENTREZ_BASE}/efetch.fcgi",
                params=fetch_params,
                timeout=30,
            )
            resp.raise_for_status()
            xml_text = resp.text
        except Exception as e:
            return f"Error fetching NCBI Gene record for ID {gene_id}: {e}"

    try:
        gene_info = _parse_ncbi_summary(xml_text)
    except Exception as e:
        return f"Error parsing NCBI response for ID {gene_id}: {e}"

    if not gene_info:
        return f"Could not parse NCBI record for Gene ID {gene_id}."

    return _format_gene_output(
        gene_info,
        gene_info.get("symbol", f"ID:{gene_id}"),
        gene_id,
    )
