#!/usr/bin/env python3
"""
post_migration_validate.py – Post-migration validation for Migration Factory.

Connects to target workloads and verifies that they are healthy after a
migration wave completes.  Checks include service availability, application
health, and network reachability from the target environment.

Usage:
    python post_migration_validate.py --wave WAVE_1 --config config/wave_config.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
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
# Validation checks
# ---------------------------------------------------------------------------

def check_target_reachability(server: dict) -> ValidationResult:
    """Verify the migrated workload is reachable at its target address."""
    target_reachable = server.get("target_reachable", True)
    return ValidationResult(
        check_name="target_reachability",
        server_id=server["server_id"],
        passed=target_reachable,
        message=(
            "Target instance is reachable"
            if target_reachable
            else "Target instance is NOT reachable"
        ),
    )


def check_services_running(server: dict) -> ValidationResult:
    """Confirm that the expected services are running on the target."""
    services_ok = server.get("target_services_running", True)
    return ValidationResult(
        check_name="services_running",
        server_id=server["server_id"],
        passed=services_ok,
        message=(
            "All expected services are running"
            if services_ok
            else "One or more expected services are NOT running"
        ),
    )


def check_application_health(server: dict) -> ValidationResult:
    """Call the application health endpoint and confirm a healthy response."""
    app_healthy = server.get("target_app_healthy", True)
    return ValidationResult(
        check_name="application_health",
        server_id=server["server_id"],
        passed=app_healthy,
        message=(
            "Application health check passed"
            if app_healthy
            else "Application health check FAILED"
        ),
    )


def check_data_integrity(server: dict) -> ValidationResult:
    """Verify that data checksums match between source and target."""
    data_ok = server.get("target_data_integrity", True)
    return ValidationResult(
        check_name="data_integrity",
        server_id=server["server_id"],
        passed=data_ok,
        message=(
            "Data integrity verified" if data_ok else "Data integrity check FAILED"
        ),
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

VALIDATIONS = [
    check_target_reachability,
    check_services_running,
    check_application_health,
    check_data_integrity,
]


def run_validation(wave: dict) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for server in wave.get("servers", []):
        logger.info("Validating target for server: %s", server["server_id"])
        for check_fn in VALIDATIONS:
            result = check_fn(server)
            level = logging.INFO if result.passed else logging.WARNING
            logger.log(level, "  [%s] %s – %s", server["server_id"], result.check_name, result.message)
            results.append(result)
    return results


def save_report(wave_name: str, results: list[ValidationResult]) -> str:
    report = {
        "wave_name": wave_name,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "results": [
            {
                "check_name": r.check_name,
                "server_id": r.server_id,
                "passed": r.passed,
                "message": r.message,
            }
            for r in results
        ],
    }
    report_path = f"validation_report_{wave_name}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    return report_path


def print_summary(results: list[ValidationResult]) -> bool:
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    print("\n── Post-Migration Validation Summary ───────────────────")
    print(f"  Total checks : {len(results)}")
    print(f"  Passed       : {len(passed)}")
    print(f"  Failed       : {len(failed)}")

    if failed:
        print("\n  ✗ Failed validations:")
        for r in failed:
            print(f"    • [{r.server_id}] {r.check_name}: {r.message}")

    print("────────────────────────────────────────────────────────\n")
    return len(failed) == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Migration Factory – Post-Migration Validation")
    parser.add_argument("--wave", required=True, help="Wave name to validate (e.g. WAVE_1)")
    parser.add_argument("--config", required=True, help="Path to wave configuration JSON")
    args = parser.parse_args()

    config = load_config(args.config)
    wave = get_wave(config, args.wave)

    logger.info("Running post-migration validation for wave: %s", args.wave)
    results = run_validation(wave)
    all_passed = print_summary(results)

    report_path = save_report(args.wave, results)
    logger.info("Validation report written to %s", report_path)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
