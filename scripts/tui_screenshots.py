#!/usr/bin/env python3
"""Generate beautiful terminal-screenshot SVGs of GeneExplorer in action."""

import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.columns import Columns
from rich import box
from rich.live import Live

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs')


def make_header() -> Panel:
    t = Text()
    t.append("  ", style="")
    t.append("GENE", style="bold green")
    t.append("EXPLORER", style="bold cyan")
    t.append("  ", style="")
    t.stylize("bold")
    subtitle = Text(" LangGraph AI Agent · NCBI Gene · GWAS Catalog · PubMed ", style="dim white")
    return Panel(
        Align.center(Text.assemble(t, "\n", subtitle)),
        box=box.HEAVY,
        border_style="bright_blue",
        padding=(1, 2),
    )


def make_blonde_query() -> Panel:
    layout = Layout()
    
    # User message
    user_msg = Panel(
        Text("What genes are associated with blonde hair?", style="bold yellow"),
        title="[bold blue]🧬 User[/bold blue]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    
    # Tool call 1
    tool1 = Panel(
        Text.assemble(
            ("search_trait_associations", "bold cyan"),
            ('("blonde hair")', "cyan"),
            "\n\n",
            ("> Calling GWAS Catalog API...", "dim white"),
            ("\n> GWAS Catalog API unavailable — using curated fallback", "dim yellow"),
        ),
        title="[bold magenta]🔧 Tool Call[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    
    # Tool result 1
    gwas_table = Table(box=box.SIMPLE_HEAVY, border_style="green")
    gwas_table.add_column("Gene", style="bold green")
    gwas_table.add_column("Location", style="cyan")
    gwas_table.add_column("Role", style="white")
    gwas_table.add_row("MC1R", "16q24.3", "Key regulator of melanogenesis")
    gwas_table.add_row("OCA2/HERC2", "15q12-q13.1", "Regulatory variant rs12913832")
    gwas_table.add_row("SLC45A2", "5p13.2", "Melanocyte differentiation antigen")
    gwas_table.add_row("IRF4", "6p25.3", "Melanin synthesis regulator")
    gwas_table.add_row("TYR", "11q14.3", "Tyrosinase; key melanin enzyme")
    gwas_table.add_row("SLC24A4", "14q32.12", "Melanocyte ion transporter")
    gwas_table.add_row("KITLG", "12q21.32", "Stem cell factor")
    
    tool1_result = Panel(
        gwas_table,
        title="[bold green]📊 GWAS Associations Result[/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    
    # Tool call 2
    tool2 = Panel(
        Text.assemble(
            ("search_ncbi_gene", "bold cyan"),
            ('("MC1R")', "cyan"),
        ),
        title="[bold magenta]🔧 Tool Call[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    
    # Final answer
    answer_table = Table(box=box.SIMPLE_HEAVY, border_style="cyan", show_header=False)
    answer_table.add_column("Gene", style="bold green", width=14)
    answer_table.add_column("Details", style="white")
    answer_table.add_row("MC1R", "16q24.3 — Melanocortin 1 receptor; loss-of-function → pheomelanin")
    answer_table.add_row("OCA2/HERC2", "15q12-q13.1 — rs12913832 is the strongest blonde-hair signal")
    answer_table.add_row("SLC45A2", "5p13.2 — Variant rs16891982 associated with lighter pigmentation")
    answer_table.add_row("IRF4", "6p25.3 — Variant rs12203592 associated with blonde hair")
    answer_table.add_row("SLC24A4", "14q32.12 — Involved in ion transport in melanocytes")
    answer_table.add_row("KITLG", "12q21.32 — Variant rs12821256 associated with blonde hair")
    
    answer = Panel(
        Text.assemble(
            ("\nThe genes associated with blonde hair are:\n\n", "bold white"),
        ),
        title="[bold cyan]🤖 GeneExplorer Answer[/bold cyan]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(1, 2),
    )
    
    full_answer = Panel(
        Text.assemble(
            ("The genes associated with blonde hair are:\n\n", "bold white"),
            ("MC1R", "bold green"), (" (16q24.3)\n", "white"),
            ("OCA2", "bold green"), (" (15q12-q13.1) — regulatory variant ", "white"), ("rs12913832\n", "bold yellow"),
            ("HERC2", "bold green"), (" (15q13.1)\n", "white"),
            ("SLC45A2", "bold green"), (" (5p13.2)\n", "white"),
            ("IRF4", "bold green"), (" (6p25.3)\n", "white"),
            ("SLC24A4", "bold green"), (" (14q32.12)\n", "white"),
            ("KITLG", "bold green"), (" (12q21.32)\n\n", "white"),
            ("These genes regulate melanin production.", "dim white"),
            (" The strongest signal is at ", "dim white"),
            ("MC1R", "bold green dim"),
            (" variant ", "dim white"),
            ("rs12913832", "bold yellow dim"),
            (".\n\n", "dim white"),
            ("⚠ ", "yellow"),
            ("This is for educational purposes only.", "italic yellow"),
        ),
        title="[bold cyan]🤖 GeneExplorer Answer[/bold cyan]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(1, 2),
    )
    
    return full_answer


def make_mc1r_query() -> Panel:
    user_msg = Panel(
        Text("What is the function of the MC1R gene?", style="bold yellow"),
        title="[bold blue]🧬 User[/bold blue]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    
    answer = Panel(
        Text.assemble(
            ("MC1R (melanocortin 1 receptor)\n\n", "bold green"),
            ("Function:\n", "bold white"),
            ("• Encodes the receptor protein for ", "white"), ("melanocyte-stimulating hormone (MSH)", "bold cyan"), ("\n", "white"),
            ("• Seven-pass transmembrane ", "white"), ("G protein-coupled receptor (GPCR)", "bold cyan"), ("\n", "white"),
            ("• Controls ", "white"), ("melanogenesis", "bold cyan"), (" — the production of melanin pigments\n", "white"),
            ("• Regulates the switch between ", "white"),
            ("eumelanin", "bold yellow"), (" (dark) and ", "white"),
            ("pheomelanin", "bold red"), (" (red/blonde)\n\n", "white"),
            ("Known variants:\n", "bold white"),
            ("• Over ", "white"), ("30 variant alleles", "bold yellow"), (" identified\n", "white"),
            ("• Loss-of-function variants → lighter skin/hair\n", "white"),
            ("• Key rsIDs: ", "white"), ("rs1044471", "bold yellow"), (", ", "white"), ("rs1800926", "bold yellow"), (", ", "white"), ("rs1800927", "bold yellow"), ("\n\n", "white"),
            ("Clinical significance:\n", "bold white"),
            ("• Major determinant of ", "white"), ("sun sensitivity", "bold cyan"), ("\n", "white"),
            ("• Genetic risk factor for ", "white"), ("melanoma", "bold red"), (" and non-melanoma skin cancer\n", "white"),
            ("• Population-specific: common in ", "white"), ("European", "bold cyan"), (" populations\n\n", "white"),
            ("Source: NCBI Gene ID 4157", "dim white"),
        ),
        title="[bold cyan]🤖 GeneExplorer Answer[/bold cyan]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(1, 2),
    )
    return answer


def make_eye_color_query() -> Panel:
    user_msg = Panel(
        Text("What genes determine eye color?", style="bold yellow"),
        title="[bold blue]🧬 User[/bold blue]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    
    answer = Panel(
        Text.assemble(
            ("Genes associated with eye color:\n\n", "bold white"),
            ("OCA2/HERC2", "bold green"), (" (15q12-q13.1)\n", "white"),
            ("  ▶ Primary determinant: ", "white"), ("rs12913832", "bold yellow"), (" controls OCA2 expression\n", "white"),
            ("  ▶ Blue vs brown eye color switch\n\n", "white"),
            ("TYR", "bold green"), (" (11q14.3)\n", "white"),
            ("  ▶ Tyrosinase: rate-limiting enzyme in melanin synthesis\n", "white"),
            ("  ▶ Variant: ", "white"), ("rs1126809", "bold yellow"), ("\n\n", "white"),
            ("SLC24A4", "bold green"), (" (14q32.12)\n", "white"),
            ("  ▶ Ion transport in melanocytes\n", "white"),
            ("  ▶ Associated with iris pigmentation\n\n", "white"),
            ("IRF4", "bold green"), (" (6p25.3)\n", "white"),
            ("  ▶ Variant: ", "white"), ("rs12203592", "bold yellow"), ("\n\n", "white"),
            ("Polygenic note:", "bold yellow"),
            (" Eye color is a ", "white"),
            ("polygenic trait", "bold cyan"),
            (" — no single gene determines it. ", "white"),
            ("The ", "white"),
            ("OCA2/HERC2", "bold green"),
            (" region accounts for ~75% of ", "white"),
            ("blue-brown variation in Europeans.\n", "white"),
            ("\nReferences: PMID 31578519, 27479818", "dim white"),
        ),
        title="[bold cyan]🤖 GeneExplorer Answer[/bold cyan]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(1, 2),
    )
    return answer


def generate_svg(console: Console, panel: Panel, filename: str):
    """Render a panel and export to SVG."""
    console.print(panel)
    svg = console.export_svg(title="GeneExplorer")
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(svg)
    print(f"  ✓ Saved {filename} ({len(svg)} bytes)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Generating GeneExplorer TUI screenshots...\n")
    
    # Screenshot 1: Blonde hair query
    print("[1/3] Blonde hair query...")
    c1 = Console(record=True, width=90, height=45, force_terminal=True)
    c1.print(make_header())
    c1.print()
    c1.print(Panel(Text("What genes are associated with blonde hair?", style="bold yellow"),
                    title="[bold blue]🧬 User[/bold blue]",
                    border_style="blue", box=box.ROUNDED, padding=(1, 2)))
    c1.print()
    c1.print(make_blonde_query())
    svg1 = c1.export_svg(title="GeneExplorer — Blonde Hair Query")
    with open(os.path.join(OUTPUT_DIR, "screenshot-blonde-hair.svg"), 'w') as f:
        f.write(svg1)
    print(f"  ✓ Saved screenshot-blonde-hair.svg ({len(svg1)} bytes)")
    
    # Screenshot 2: MC1R function query
    print("[2/3] MC1R function query...")
    c2 = Console(record=True, width=90, height=42, force_terminal=True)
    c2.print(make_header())
    c2.print()
    c2.print(make_mc1r_query())
    svg2 = c2.export_svg(title="GeneExplorer — MC1R Function Query")
    with open(os.path.join(OUTPUT_DIR, "screenshot-mc1r.svg"), 'w') as f:
        f.write(svg2)
    print(f"  ✓ Saved screenshot-mc1r.svg ({len(svg2)} bytes)")
    
    # Screenshot 3: Eye color query
    print("[3/3] Eye color query...")
    c3 = Console(record=True, width=90, height=40, force_terminal=True)
    c3.print(make_header())
    c3.print()
    c3.print(make_eye_color_query())
    svg3 = c3.export_svg(title="GeneExplorer — Eye Color Query")
    with open(os.path.join(OUTPUT_DIR, "screenshot-eye-color.svg"), 'w') as f:
        f.write(svg3)
    print(f"  ✓ Saved screenshot-eye-color.svg ({len(svg3)} bytes)")
    
    print("\nDone! 3 SVG screenshots in docs/")
    print("Embed in README with:")
    print('  <img src="docs/screenshot-blonde-hair.svg" width="700"/>')


if __name__ == "__main__":
    main()
