import requests
from langchain_core.tools import tool

GWAS_API_BASE = "https://www.ebi.ac.uk/gwas/rest/api"


@tool
def search_trait_associations(trait: str) -> str:
    """Search for gene-trait associations from the GWAS Catalog by trait name (e.g., 'blonde hair', 'hair color', 'eye color'). Returns top associated genes, locations, and pubmed IDs."""

    query = trait.lower().strip()

    # GWAS Catalog API: search associations by trait
    # The API supports /api/efo/search or /api/associations/search/byefotrait
    try:
        url = f"{GWAS_API_BASE}/efo/search"
        params = {"term": query, "size": 5}
        resp = requests.get(url, params=params, timeout=30, headers={"Accept": "application/json"})
        resp.raise_for_status()
        efo_data = resp.json()

        if not efo_data.get("_embedded", {}).get("efoResults"):
            return f"No GWAS Catalog EFO terms found for '{trait}'. Try a broader term (e.g., 'hair color' instead of 'blonde hair')."

        # Take the first EFO term
        efo = efo_data["_embedded"]["efoResults"][0]
        efo_uri = efo.get("uri", "")
        efo_label = efo.get("label", query)

        # Now get associations for this EFO term
        assoc_url = f"{GWAS_API_BASE}/associations/search/efo"
        assoc_params = {
            "efoUri": efo_uri,
            "size": 20,
        }
        assoc_resp = requests.get(
            assoc_url, params=assoc_params, timeout=30, headers={"Accept": "application/json"}
        )
        assoc_resp.raise_for_status()
        assoc_data = assoc_resp.json()

    except requests.exceptions.Timeout:
        return f"GWAS Catalog API timed out for '{trait}'. The service may be slow; try again later."
    except requests.exceptions.RequestException as e:
        # Fallback: return well-known associations based on public literature
        return _fallback_trait_associations(trait)

    associations = assoc_data.get("_embedded", {}).get("associations", [])
    if not associations:
        return _fallback_trait_associations(trait)

    seen_genes = set()
    results = [f"GWAS Catalog associations for '{efo_label}' (EFO: {efo_uri})"]

    for assoc in associations:
        if len(seen_genes) >= 10:
            break

        genes = _extract_genes_from_association(assoc)
        if not genes:
            continue

        pvalue = assoc.get("pvalue", "N/A")
        pvalue_desc = assoc.get("pvalueDescription", "")
        snps = assoc.get("strongestAllele", "")
        risk_allele = assoc.get("riskFrequency", "")
        pubmed_id = assoc.get("pubmedId", "")

        for gene in genes:
            gene_symbol = gene.get("geneName", "")
            if gene_symbol and gene_symbol not in seen_genes:
                seen_genes.add(gene_symbol)
                chrom = gene.get("chromosomeName", "")
                loc = f" (chr{chrom})" if chrom else ""
                snp_info = f" | SNPs: {snps}" if snps else ""
                pval_info = f" | p={pvalue}" if pvalue != "N/A" else ""
                pmid = f" | PMID: {pubmed_id}" if pubmed_id else ""
                results.append(
                    f"- {gene_symbol}{loc}{snp_info}{pval_info}{pmid}"
                )

    if len(results) == 1:
        results.append("(No specific gene-level associations returned from API)")

    return "\n".join(results)


def _extract_genes_from_association(assoc: dict) -> list:
    """Extract gene entries from a GWAS Catalog association response."""
    genes = []

    # Check loci -> genes
    loci = assoc.get("loci", [])
    for locus in loci:
        locus_genes = locus.get("genes", [])
        for g in locus_genes:
            genes.append({
                "geneName": g.get("geneName", ""),
                "chromosomeName": locus.get("chromosomeName", ""),
            })

    # Check directly nested genes (some API versions)
    if not genes:
        direct_genes = assoc.get("genes", [])
        for g in direct_genes:
            genes.append({
                "geneName": g.get("geneName", ""),
                "chromosomeName": g.get("chromosomeName", ""),
            })

    # Check reported genes (list of strings somewhere)
    reported = assoc.get("reportedGenes", [])
    for gene_name in reported:
        if isinstance(gene_name, str):
            genes.append({
                "geneName": gene_name,
                "chromosomeName": "",
            })

    return genes


def _fallback_trait_associations(trait: str) -> str:
    """Fallback when GWAS Catalog API is unreachable. Returns curated public knowledge based on well-studied traits."""

    trait = trait.lower().strip()

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

    # Try exact or partial match
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

    # Generic response if trait not in known list
    return (
        f"GWAS Catalog API was unreachable for '{trait}', and '{trait}' is not in the curated fallback set. "
        "Please try again later or use a more specific trait term. "
        "Known curated traits: hair color, eye color, height."
    )
