#!/usr/bin/env python3
"""
preflight_check.py – Pre-migration validation for Migration Factory.

Validates that all prerequisites are met for a migration wave before
execution begins, including network connectivity, credential validity,
and disk space on target instances.

Usage:
    python preflight_check.py --wave WAVE_1 --config config/wave_config.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import NamedTuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class CheckResult(NamedTuple):
    check_name: str
    server_id: str
    passed: bool
    message: str


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)
    with path.open() as f:
        return json.load(f)


def get_wave(config: dict, wave_name: str) -> dict:
    for wave in config.get("waves", []):
        if wave["wave_name"] == wave_name:
            return wave
    logger.error("Wave '%s' not found in config.", wave_name)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_network_connectivity(server: dict) -> CheckResult:
    """
    Verify that the source server is reachable.

    In production this would perform a real TCP/ICMP probe.  Here we
    simulate the check using the 'reachable' flag in the server config.
    """
    reachable = server.get("reachable", True)
    return CheckResult(
        check_name="network_connectivity",
        server_id=server["server_id"],
        passed=reachable,
        message="Server is reachable" if reachable else "Server is NOT reachable",
    )


def check_disk_space(server: dict, min_free_gb: float = 10.0) -> CheckResult:
    """Ensure sufficient free disk space on the source server."""
    free_gb = server.get("free_disk_gb", 50.0)
    passed = free_gb >= min_free_gb
    return CheckResult(
        check_name="disk_space",
        server_id=server["server_id"],
        passed=passed,
        message=(
            f"Free disk space OK ({free_gb} GB available)"
            if passed
            else f"Insufficient free disk space ({free_gb} GB < {min_free_gb} GB required)"
        ),
    )


def check_credentials(server: dict) -> CheckResult:
    """Verify that valid credentials are configured for the server."""
    has_creds = bool(server.get("credentials_configured", True))
    return CheckResult(
        check_name="credentials",
        server_id=server["server_id"],
        passed=has_creds,
        message=(
            "Credentials configured" if has_creds else "Credentials NOT configured"
        ),
    )


def check_agent_installed(server: dict) -> CheckResult:
    """Confirm the migration agent is installed on the source server."""
    agent_ok = bool(server.get("agent_installed", False))
    return CheckResult(
        check_name="agent_installed",
        server_id=server["server_id"],
        passed=agent_ok,
        message=(
            "Migration agent installed" if agent_ok else "Migration agent NOT installed"
        ),
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

CHECKS = [
    check_network_connectivity,
    check_disk_space,
    check_credentials,
    check_agent_installed,
]


def run_preflight(wave: dict) -> list[CheckResult]:
    results: list[CheckResult] = []
    for server in wave.get("servers", []):
        logger.info("Running preflight checks for server: %s", server["server_id"])
        for check_fn in CHECKS:
            result = check_fn(server)
            level = logging.INFO if result.passed else logging.WARNING
            logger.log(level, "  [%s] %s – %s", server["server_id"], result.check_name, result.message)
            results.append(result)
    return results


def print_summary(results: list[CheckResult]) -> bool:
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    print("\n── Preflight Check Summary ─────────────────────────────")
    print(f"  Total checks : {len(results)}")
    print(f"  Passed       : {len(passed)}")
    print(f"  Failed       : {len(failed)}")

    if failed:
        print("\n  ✗ Failed checks:")
        for r in failed:
            print(f"    • [{r.server_id}] {r.check_name}: {r.message}")

    print("────────────────────────────────────────────────────────\n")
    return len(failed) == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Migration Factory – Pre-flight Checks")
    parser.add_argument("--wave", required=True, help="Wave name to validate (e.g. WAVE_1)")
    parser.add_argument("--config", required=True, help="Path to wave configuration JSON")
    args = parser.parse_args()

    config = load_config(args.config)
    wave = get_wave(config, args.wave)

    logger.info("Running pre-flight checks for wave: %s", args.wave)
    results = run_preflight(wave)
    all_passed = print_summary(results)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
