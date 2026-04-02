#!/usr/bin/env python3
"""
execute_migration.py – Migration execution orchestrator for Migration Factory.

Reads a wave configuration and a pipeline template, then executes each
pipeline task in order for every server in the wave.

Usage:
    python execute_migration.py --wave WAVE_1 \
        --config config/wave_config.json \
        --pipeline templates/rehost_pipeline.json \
        [--dry-run]
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        logger.error("File not found: %s", path)
        sys.exit(1)
    with p.open() as f:
        return json.load(f)


def get_wave(config: dict, wave_name: str) -> dict:
    for wave in config.get("waves", []):
        if wave["wave_name"] == wave_name:
            return wave
    logger.error("Wave '%s' not found in config.", wave_name)
    sys.exit(1)


def execute_task(task: dict, server: dict, dry_run: bool) -> bool:
    """
    Execute a single pipeline task for a given server.

    Returns True on success, False on failure.

    In production this would invoke the real automation (e.g. SSM Run Command,
    a Lambda function, or a REST API call).  Here we simulate the execution.
    """
    task_id = task.get("task_id", "unknown")
    task_name = task.get("name", "unknown")
    task_type = task.get("type", "automated")
    server_id = server["server_id"]

    if task_type == "manual":
        logger.info(
            "  [MANUAL] %s – %s | Skipping (manual tasks require human action)",
            server_id,
            task_name,
        )
        return True

    if dry_run:
        logger.info("  [DRY-RUN] %s – Task '%s' (%s) would be executed", server_id, task_name, task_id)
        return True

    logger.info("  [EXEC] %s – Running task '%s' (%s) …", server_id, task_name, task_id)
    # Simulate work
    time.sleep(0.1)
    logger.info("  [DONE] %s – Task '%s' completed successfully", server_id, task_name)
    return True


def run_pipeline(wave: dict, pipeline: dict, dry_run: bool) -> bool:
    """Execute all pipeline tasks for every server in the wave."""
    tasks = pipeline.get("tasks", [])
    servers = wave.get("servers", [])

    if not tasks:
        logger.warning("Pipeline has no tasks defined.")
        return True

    all_success = True

    for server in servers:
        server_id = server["server_id"]
        logger.info("Processing server: %s (%s)", server_id, server.get("hostname", ""))

        for task in tasks:
            success = execute_task(task, server, dry_run)
            if not success:
                logger.error(
                    "Task '%s' failed for server %s. Halting pipeline for this server.",
                    task.get("name"),
                    server_id,
                )
                all_success = False
                break

    return all_success


def main() -> None:
    parser = argparse.ArgumentParser(description="Migration Factory – Execute Migration")
    parser.add_argument("--wave", required=True, help="Wave name to migrate (e.g. WAVE_1)")
    parser.add_argument("--config", required=True, help="Path to wave configuration JSON")
    parser.add_argument("--pipeline", required=True, help="Path to pipeline template JSON")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without executing them",
    )
    args = parser.parse_args()

    config = load_json(args.config)
    pipeline = load_json(args.pipeline)
    wave = get_wave(config, args.wave)

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    logger.info(
        "Starting %s migration for wave '%s' using pipeline '%s'",
        mode,
        args.wave,
        pipeline.get("name", args.pipeline),
    )

    success = run_pipeline(wave, pipeline, args.dry_run)

    if success:
        logger.info("Migration wave '%s' completed successfully.", args.wave)
    else:
        logger.error("Migration wave '%s' completed with errors.", args.wave)
        sys.exit(1)


if __name__ == "__main__":
    main()
