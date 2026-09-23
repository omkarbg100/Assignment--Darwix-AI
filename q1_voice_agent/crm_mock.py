"""
Q1 - CRM Mock: Lead storage, CLI viewer, and management utility.
Leads are saved to crm_leads.json in this directory.
This script provides a CLI to inspect, search, and export logged leads.

Usage:
    python crm_mock.py list                    # List all leads
    python crm_mock.py show LEAD-A1B2C3D4      # Show one lead
    python crm_mock.py stats                   # Summary statistics
    python crm_mock.py export --format csv     # Export to CSV
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import uuid

LEADS_FILE = Path(__file__).parent / "crm_leads.json"
CALLBACKS_FILE = Path(__file__).parent / "callbacks.json"


def load_leads() -> list[dict]:
    if not LEADS_FILE.exists():
        return []
    with open(LEADS_FILE) as f:
        return json.load(f)


def load_callbacks() -> list[dict]:
    if not CALLBACKS_FILE.exists():
        return []
    with open(CALLBACKS_FILE) as f:
        return json.load(f)


def save_leads(leads: list[dict]):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2)


def save_callbacks(callbacks: list[dict]):
    with open(CALLBACKS_FILE, "w", encoding="utf-8") as f:
        json.dump(callbacks, f, indent=2)


def create_lead(**kwargs) -> dict:
    """Save a new lead record to crm_leads.json."""
    leads = load_leads()
    lead_id = kwargs.pop("lead_id", f"LEAD-{str(uuid.uuid4())[:8].upper()}")
    record = {
        "lead_id": lead_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        **kwargs,
    }
    leads.append(record)
    save_leads(leads)
    return record


def create_callback(**kwargs) -> dict:
    """Save a callback record to callbacks.json."""
    callbacks = load_callbacks()
    record = {
        "callback_id": f"CB-{str(uuid.uuid4())[:6].upper()}",
        "created_at": datetime.utcnow().isoformat() + "Z",
        **kwargs,
    }
    callbacks.append(record)
    save_callbacks(callbacks)
    return record


def cmd_list(args):
    leads = load_leads()
    if not leads:
        print("No leads recorded yet. Run the voice agent and make some calls!")
        return

    print(f"\n{'─' * 80}")
    print(f"  {'LEAD ID':<18} {'NAME':<20} {'AGE':<5} {'CITY':<15} {'PLAN':<12} {'QUALIFIED'}")
    print(f"{'─' * 80}")
    for lead in leads:
        qualified = "✅ YES" if lead.get("qualified") else "❌ NO"
        print(
            f"  {lead.get('lead_id', 'N/A'):<18}"
            f" {lead.get('name', 'N/A'):<20}"
            f" {lead.get('age', '?'):<5}"
            f" {lead.get('city', 'N/A'):<15}"
            f" {lead.get('recommended_plan', 'TBD'):<12}"
            f" {qualified}"
        )
    print(f"{'─' * 80}")
    print(f"  Total: {len(leads)} leads\n")


def cmd_show(args):
    leads = load_leads()
    lead = next((l for l in leads if l.get("lead_id") == args.lead_id), None)
    if not lead:
        print(f"Lead '{args.lead_id}' not found.")
        sys.exit(1)

    print(f"\n{'═' * 50}")
    print(f"  CRM LEAD RECORD: {lead['lead_id']}")
    print(f"{'═' * 50}")
    for key, value in lead.items():
        print(f"  {key:<30} {value}")
    print(f"{'═' * 50}\n")


def cmd_stats(args):
    leads = load_leads()
    callbacks = load_callbacks()

    if not leads:
        print("No data yet.")
        return

    qualified = [l for l in leads if l.get("qualified")]
    plans = {}
    cities = {}
    for lead in qualified:
        plan = lead.get("recommended_plan", "Unknown")
        city = lead.get("city", "Unknown")
        plans[plan] = plans.get(plan, 0) + 1
        cities[city] = cities.get(city, 0) + 1

    print(f"\n{'═' * 40}")
    print("  CRM SUMMARY STATISTICS")
    print(f"{'═' * 40}")
    print(f"  Total leads logged  : {len(leads)}")
    print(f"  Qualified           : {len(qualified)} ({len(qualified)/len(leads)*100:.0f}%)")
    print(f"  Not qualified       : {len(leads) - len(qualified)}")
    print(f"  Callbacks scheduled : {len(callbacks)}")
    print(f"\n  Plan Distribution (qualified):")
    for plan, count in sorted(plans.items(), key=lambda x: -x[1]):
        print(f"    {plan:<15} {count}")
    print(f"\n  Top Cities:")
    for city, count in sorted(cities.items(), key=lambda x: -x[1])[:5]:
        print(f"    {city:<15} {count}")
    print(f"{'═' * 40}\n")


def cmd_export(args):
    leads = load_leads()
    if not leads:
        print("No leads to export.")
        return

    fmt = args.format.lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(__file__).parent / f"crm_export_{timestamp}.{fmt}"

    if fmt == "csv":
        if not leads:
            return
        fieldnames = list(leads[0].keys())
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(leads)
        print(f"✅ Exported {len(leads)} leads to {output_file}")
    elif fmt == "json":
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2)
        print(f"✅ Exported {len(leads)} leads to {output_file}")
    else:
        print(f"Unsupported format: {fmt}. Use 'csv' or 'json'.")


def main():
    parser = argparse.ArgumentParser(description="CRM Mock — Lead Management CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all CRM leads")

    show_parser = subparsers.add_parser("show", help="Show a specific lead")
    show_parser.add_argument("lead_id", help="Lead ID (e.g. LEAD-A1B2C3D4)")

    subparsers.add_parser("stats", help="Show summary statistics")

    export_parser = subparsers.add_parser("export", help="Export leads to file")
    export_parser.add_argument("--format", default="csv", choices=["csv", "json"])

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
