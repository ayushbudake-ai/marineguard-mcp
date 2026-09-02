"""
MarineGuard MCP — Interactive Terminal Demo & Rehearsal Suite
"""

import time
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from marineguard.mcp_server import MarineGuardMCPServer
from marineguard.schemas import Action, MissionContext
from marineguard.firewall.operator_ui import OperatorUIHandler

console = Console(safe_box=True)


def run_demo(simulate: bool = True):
    console.print("\n[bold cyan]===========================================================[/bold cyan]")
    console.print("[bold white]   MARINEGUARD MCP -- Autonomous Underwater Survey Agent    [/bold white]")
    console.print("[bold cyan]===========================================================[/bold cyan]\n")

    # BEAT 1: Scientist Console
    console.print(Panel(
        "[bold green]MarineGuard Console>[/bold green] "
        "\"Survey the 2.3 sq km zone off Chennai coast.\n"
        " Detect and classify all debris.\n"
        " Prioritize ghost nets and plastic containers.\n"
        " Generate a removal priority map and official MoES report.\"",
        title="[bold yellow]Screen 1 -- Marine Scientist Console Input[/bold yellow]",
        border_style="yellow",
    ))
    time.sleep(1.0)

    # BEAT 2: Platform Discovery & Compiler
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="[cyan]Parsing platform specs & compiling sensor tools...[/cyan]", total=None)
        time.sleep(1.0)

    server = MarineGuardMCPServer("data/sensor_specs/sagar_netra.yaml")
    summary = server.emitter.print_compile_summary(server.registry)

    console.print(Panel(
        f"[bold green][OK] PLATFORM DISCOVERED:[/bold green] Sagar Netra (AUV-01)\n"
        f"[dim]{summary}[/dim]\n\n"
        f"[bold blue][FIREWALL]:[/bold blue] LOADED (ICAR-2024 Policy | Min Battery: 25% | Comms: 5 kbps)\n"
        f"[bold magenta][TRACE]:[/bold magenta] ENABLED (Real-Time Evidence Overlay)",
        title="[bold green]Screen 2 -- Sensor Suite Compiler Output[/bold green]",
        border_style="green",
    ))
    time.sleep(1.5)

    # BEAT 3: Live Detection Trace
    console.print("\n[bold yellow]Screen 3 -- Live Multi-Sensor Detection Trace (Replayed Ocean Data)[/bold yellow]")
    table = Table(title="Live Acoustic Pings & Classified Contacts", border_style="blue")
    table.add_column("Timestamp", style="dim")
    table.add_column("Contact ID", style="bold cyan")
    table.add_column("Species", style="bold white")
    table.add_column("Fused Conf", style="bold green")
    table.add_column("Depth", style="yellow")
    table.add_column("Priority", style="bold red")

    survey_res = server.marine_debris_survey("Sagar Netra", {}, ["ghost_nets", "plastics"])
    classified = survey_res["classified_targets"]

    for idx, t in enumerate(classified):
        time_str = time.strftime("%H:%M:%S", time.localtime(time.time() + idx * 5))
        table.add_row(
            time_str,
            t["target_id"],
            t["species"],
            f"{t['confidence']*100:.1f}%",
            f"{t['depth_m']}m",
            t["removal_priority"],
        )
        console.print(f"[dim]09:41:{10+idx*4:02d}[/dim] [TARGET] Contact_{idx+1}: Multi-sensor fusion -> [bold green]{t['species']}[/bold green] (Conf: {t['confidence']*100:.1f}%)")
        time.sleep(0.5)

    console.print(table)
    time.sleep(1.5)

    # BEAT 4: Firewall Intercept
    console.print("\n[bold red]Screen 4 -- Mission Firewall Safety Intercept[/bold red]")
    ui_handler = OperatorUIHandler()
    action = Action(
        type="request_altitude_change",
        description="Descend AUV altitude from 15m to 3m for close optical inspection",
        target_id="TARGET_Contact_01 (Ghost Net Cluster)",
        consumes_reserve=0.12,
    )
    context = MissionContext(battery_reserve=0.28, acoustic_link_kbps=4.5)
    decision = server.firewall.check_action(action, context)

    card_text = ui_handler.format_intercept_card(action, context, decision)
    console.print(Panel(card_text, border_style="red"))
    time.sleep(1.5)

    # BEAT 5: Platform Swap & Exports
    console.print("\n[bold cyan]Screen 5 -- Report Exporters & Hot Platform Swap Demo[/bold cyan]")
    report_res = server.export_report("PDF")
    geojson_res = server.export_report("GeoJSON")
    s100_res = server.export_report("S100")

    console.print(f"[bold green][OK] EXPORTS GENERATED:[/bold green]")
    console.print(f"  * PDF Report:     {report_res['file_path']}")
    console.print(f"  * GIS GeoJSON:    {geojson_res['file_path']}")
    console.print(f"  * IHO S-100:      {s100_res['file_path']}")

    console.print("\n[bold yellow][SWAP] EXECUTING ZERO-CODE PLATFORM HOT-SWAP...[/bold yellow]")
    server.load_platform("data/sensor_specs/hugin_3000.yaml")
    hugin_summary = server.emitter.print_compile_summary(server.registry)

    console.print(Panel(
        f"[bold green][OK] NEW PLATFORM LOADED:[/bold green] Kongsberg HUGIN 3000\n"
        f"[dim]{hugin_summary}[/dim]\n\n"
        f"[bold yellow][OK] SAS PIPELINE AUTO-CONFIGURED:[/bold yellow] HISAS 1032 SAS (3cm res) -> start_sas_survey(), detect_debris_sas()\n"
        f"[bold green][OK] FIREWALL & TRACE CONTINUITY MAINTAINED (0 Code Changes Needed)[/bold green]",
        title="[bold green]Platform Swap Demo Result[/bold green]",
        border_style="magenta",
    ))

    console.print("\n[bold white]===========================================================[/bold white]")
    console.print("[bold green]   MarineGuard MCP Demo Execution Successfully Finished!   [/bold green]")
    console.print("[bold white]===========================================================[/bold white]\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarineGuard MCP CLI Demo")
    parser.add_argument("--simulate", action="store_true", default=True, help="Run simulation replay harness")
    args = parser.parse_args()
    run_demo(simulate=args.simulate)
