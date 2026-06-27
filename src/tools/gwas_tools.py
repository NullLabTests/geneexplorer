import requests
from langchain_core.tools import tool

GWAS_API_BASE = "https://www.ebi.ac.uk/gwas/rest/api"


@tool
def search_trait_associations(trait: str) -> str:
    """Search for gene-trait associations from the GWAS Catalog by trait name (e.g., 'blonde hair', 'hair color', 'eye color'). Returns top associated genes, locations, and pubmed IDs."""

    query = trait.lower().strip()

    # Option 1: try GWAS Catalog API live
    live_results = _try_gwas_live(query)
    if live_results:
        return live_results

    # Option 2: fallback to curated public literature
    return _fallback_trait_associations(query)


def _try_gwas_live(query: str) -> str | None:
    """Attempt to fetch real-time data from the GWAS Catalog REST API."""

    try:
        # Step 1: search EFO terms matching the trait
        url = f"{GWAS_API_BASE}/efo/search"
        params = {"term": query, "size": 5}
        resp = requests.get(
            url, params=params, timeout=15,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        efo_data = resp.json()
    except Exception:
        return None

    efo_results = efo_data.get("_embedded", {}).get("efoResults", [])
    if not efo_results:
        return None

    efo = efo_results[0]
    efo_uri = efo.get("uri", "")
    efo_label = efo.get("label", query)

    # Step 2: fetch associations for that EFO term
    try:
        assoc_url = f"{GWAS_API_BASE}/associations/search/efo"
        assoc_resp = requests.get(
            assoc_url,
            params={"efoUri": efo_uri, "size": 20},
            timeout=20,
            headers={"Accept": "application/json"},
        )
        assoc_resp.raise_for_status()
        assoc_data = assoc_resp.json()
    except Exception:
        return None

    associations = assoc_data.get("_embedded", {}).get("associations", [])
    if not associations:
        return None

    seen_genes = set()
    results = [f"GWAS Catalog associations for '{efo_label}' (EFO: {efo_uri})"]

    for assoc in associations[:30]:
        if len(seen_genes) >= 12:
            break

        genes = _extract_live_genes(assoc)
        if not genes:
            continue

        pvalue = assoc.get("pvalue", "N/A")
        pvalue_text = f"p={pvalue}" if pvalue != "N/A" else ""
        snp_info = assoc.get("strongestAllele", "")
        pubmed_id = assoc.get("pubmedId", "")

        for gene_symbol, chrom in genes:
            if gene_symbol and gene_symbol not in seen_genes:
                seen_genes.add(gene_symbol)
                parts = [gene_symbol]
                if chrom:
                    parts.append(f"(chr{chrom})")
                if snp_info:
                    parts.append(f"SNP: {snp_info}")
                if pvalue_text:
                    parts.append(pvalue_text)
                if pubmed_id:
                    parts.append(f"PMID: {pubmed_id}")
                results.append("  - " + " | ".join(parts))

    if len(results) > 1:
        return "\n".join(results)

    return None


def _extract_live_genes(assoc: dict) -> list[tuple[str, str]]:
    genes = []

    for locus in assoc.get("loci", []):
        chrom = locus.get("chromosomeName", "")
        for g in locus.get("genes", []):
            name = (g.get("geneName") or "").strip()
            if name:
                genes.append((name, chrom))

    if not genes:
        for g in assoc.get("genes", []):
            name = (g.get("geneName") or "").strip()
            chrom = (g.get("chromosomeName") or "").strip()
            if name:
                genes.append((name, chrom))

    if not genes:
        for name in assoc.get("reportedGenes", []):
            if isinstance(name, str) and name.strip():
                genes.append((name.strip(), ""))

    return genes


def _fallback_trait_associations(trait: str) -> str:
    """Curated public-literature fallback for well-studied traits."""

    KNOWN_TRAITS = {
        "blonde": {
            "trait": "Hair color (blonde)",
            "genes": [
                ("MC1R", "16q24.3", "Melanocortin 1 receptor; loss-of-function variants shift melanin to pheomelanin (red/blonde)"),
                ("OCA2", "15q12-q13.1", "OCA2 melanosomal transmembrane protein; regulatory variant rs12913832 strongly associated with blonde/brown hair"),
                ("HERC2", "15q13.1", "HECT and RLD domain containing E3 ubiquitin protein ligase 2; intronic variant rs12913832 regulates OCA2 expression"),
                ("SLC45A2", "5p13.2", "Solute carrier family 45 member 2; variant rs16891982 associated with lighter pigmentation"),
                ("IRF4", "6p25.3", "Interferon regulatory factor 4; variant rs12203592 associated with blonde hair"),
                ("SLC24A4", "14q32.12", "Solute carrier family 24 member 4; involved in ion transport in melanocytes"),
                ("KITLG", "12q21.32", "KIT ligand; variant rs12821256 associated with blonde hair"),
            ],
            "pmid": "31578519, 27479818, 19043545",
        },
        "hair color": {
            "trait": "Hair color",
            "genes": [
                ("MC1R", "16q24.3", "Key regulator of melanogenesis"),
                ("OCA2/HERC2", "15q12-q13.1", "Regulatory region rs12913832 controls OCA2 expression"),
                ("SLC45A2", "5p13.2", "Melanocyte differentiation antigen"),
                ("IRF4", "6p25.3", "Melanin synthesis regulator"),
                ("TYR", "11q14.3", "Tyrosinase; key enzyme in melanin production"),
                ("SLC24A4", "14q32.12", "Melanocyte ion transporter"),
                ("KITLG", "12q21.32", "Stem cell factor; melanocyte development"),
            ],
            "pmid": "31578519, 27479818, 19043545",
        },
        "eye color": {
            "trait": "Eye color",
            "genes": [
                ("OCA2/HERC2", "15q12-q13.1", "rs12913832 is the primary determinant of blue vs brown eyes"),
                ("TYR", "11q14.3", "Tyrosinase; rs1126809 associated with eye color"),
                ("SLC24A4", "14q32.12", "Associations with iris pigmentation"),
                ("IRF4", "6p25.3", "rs12203592 associated with eye color"),
                ("SLC45A2", "5p13.2", "rs16891982 associated with lighter iris color"),
            ],
            "pmid": "31578519, 27479818, 19043545",
        },
        "height": {
            "trait": "Height (stature)",
            "genes": [
                ("HMGA2", "12q14.3", "High mobility group AT-hook 2; rs1042725"),
                ("GDF5", "20q11.22", "Growth differentiation factor 5"),
                ("LCORL", "4p15.31", "Ligand dependent corepressor like"),
                ("STC2", "5q35.2", "Stanniocalcin 2; rs3830364"),
            ],
            "pmid": "35415076, 33244174, 31374226",
        },
    }

    for key, data in KNOWN_TRAITS.items():
        if key in trait or trait in key:
            lines = [
                f"Public literature associations for '{data['trait']}' (curated from large GWAS studies):",
            ]
            for symbol, loc, desc in data["genes"]:
                lines.append(f"- {symbol} ({loc}): {desc}")
            lines.append(f"Key references: PMID: {data['pmid']}")
            lines.append("")
            lines.append(
                "Note: These data are sourced from large published GWAS and meta-analyses. "
                "The GWAS Catalog API was unavailable, so this fallback uses curated public literature."
            )
            return "\n".join(lines)

    return (
        f"GWAS Catalog API was unreachable for '{trait}', and '{trait}' is not in the curated fallback set. "
        "Please try again later or use a more specific trait term. "
        "Known curated traits: hair color, eye color, height."
    )
