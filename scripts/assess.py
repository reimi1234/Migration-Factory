#!/usr/bin/env python3
"""
assess.py – Discovery and assessment script for Migration Factory.

Reads the wave configuration and produces an inventory of source workloads,
including server metadata, network dependencies, and recommended migration
strategy for each workload.

Usage:
    python assess.py --config config/wave_config.json [--output inventory.json]
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load and return the wave configuration file."""
    path = Path(config_path)
    if not path.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)
    with path.open() as f:
        return json.load(f)


def assess_workload(server: dict) -> dict:
    """
    Assess a single workload and return enriched metadata.

    In a real implementation this would query the source environment
    (e.g. via AWS Systems Manager, VMware vSphere API, or WMI) to collect
    live data.  Here we derive a recommended strategy from the static
    configuration for demonstration purposes.
    """
    tags = server.get("tags", {})
    strategy = tags.get("migration_strategy", "rehost").lower()

    return {
        "server_id": server["server_id"],
        "hostname": server["hostname"],
        "ip_address": server.get("ip_address", "unknown"),
        "os": server.get("os", "unknown"),
        "cpu_cores": server.get("cpu_cores", 0),
        "ram_gb": server.get("ram_gb", 0),
        "disk_gb": server.get("disk_gb", 0),
        "recommended_strategy": strategy,
        "tags": tags,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def run_assessment(config: dict) -> dict:
    """Run the full assessment for all waves defined in the config."""
    inventory = {
        "project": config.get("project", "Migration-Factory"),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "waves": [],
    }

    for wave in config.get("waves", []):
        wave_name = wave["wave_name"]
        logger.info("Assessing wave: %s (%d servers)", wave_name, len(wave.get("servers", [])))

        assessed_servers = [assess_workload(s) for s in wave.get("servers", [])]

        strategy_summary: dict[str, int] = {}
        for s in assessed_servers:
            strat = s["recommended_strategy"]
            strategy_summary[strat] = strategy_summary.get(strat, 0) + 1

        inventory["waves"].append(
            {
                "wave_name": wave_name,
                "server_count": len(assessed_servers),
                "strategy_summary": strategy_summary,
                "servers": assessed_servers,
            }
        )

    return inventory


def main() -> None:
    parser = argparse.ArgumentParser(description="Migration Factory – Assessment")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the wave configuration JSON file",
    )
    parser.add_argument(
        "--output",
        default="inventory.json",
        help="Path to write the output inventory (default: inventory.json)",
    )
    args = parser.parse_args()

    logger.info("Loading configuration from %s", args.config)
    config = load_config(args.config)

    logger.info("Starting assessment …")
    inventory = run_assessment(config)

    output_path = Path(args.output)
    with output_path.open("w") as f:
        json.dump(inventory, f, indent=2)

    total_servers = sum(w["server_count"] for w in inventory["waves"])
    logger.info(
        "Assessment complete. %d waves, %d servers. Inventory written to %s",
        len(inventory["waves"]),
        total_servers,
        args.output,
    )


if __name__ == "__main__":
    main()
