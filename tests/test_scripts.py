"""
tests/test_scripts.py – Unit tests for Migration Factory scripts.

Run with:
    python -m pytest tests/ -v
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure the project root is on the path so we can import from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# assess.py tests
# ---------------------------------------------------------------------------
from scripts.assess import assess_workload, run_assessment


class TestAssessWorkload:
    def _server(self, **overrides):
        base = {
            "server_id": "srv-test",
            "hostname": "test-host",
            "ip_address": "10.0.0.1",
            "os": "Ubuntu 22.04",
            "cpu_cores": 4,
            "ram_gb": 16,
            "disk_gb": 100,
            "tags": {"migration_strategy": "rehost"},
        }
        base.update(overrides)
        return base

    def test_returns_recommended_strategy_from_tags(self):
        result = assess_workload(self._server(tags={"migration_strategy": "replatform"}))
        assert result["recommended_strategy"] == "replatform"

    def test_defaults_to_rehost_when_no_strategy_tag(self):
        result = assess_workload(self._server(tags={}))
        assert result["recommended_strategy"] == "rehost"

    def test_result_contains_required_fields(self):
        result = assess_workload(self._server())
        for field in ("server_id", "hostname", "ip_address", "os", "cpu_cores", "ram_gb", "disk_gb", "assessed_at"):
            assert field in result

    def test_strategy_is_lowercased(self):
        result = assess_workload(self._server(tags={"migration_strategy": "RETIRE"}))
        assert result["recommended_strategy"] == "retire"


class TestRunAssessment:
    def test_wave_summary_counts_servers(self):
        config = {
            "project": "Test",
            "waves": [
                {
                    "wave_name": "WAVE_TEST",
                    "servers": [
                        {
                            "server_id": "s1",
                            "hostname": "h1",
                            "tags": {"migration_strategy": "rehost"},
                        },
                        {
                            "server_id": "s2",
                            "hostname": "h2",
                            "tags": {"migration_strategy": "retire"},
                        },
                    ],
                }
            ],
        }
        inventory = run_assessment(config)
        assert len(inventory["waves"]) == 1
        wave = inventory["waves"][0]
        assert wave["server_count"] == 2
        assert wave["strategy_summary"]["rehost"] == 1
        assert wave["strategy_summary"]["retire"] == 1

    def test_empty_waves(self):
        config = {"project": "Empty", "waves": []}
        inventory = run_assessment(config)
        assert inventory["waves"] == []


# ---------------------------------------------------------------------------
# preflight_check.py tests
# ---------------------------------------------------------------------------
from scripts.preflight_check import (
    check_agent_installed,
    check_credentials,
    check_disk_space,
    check_network_connectivity,
    run_preflight,
)


class TestPreflightChecks:
    def _server(self, **overrides):
        base = {
            "server_id": "srv-pf",
            "reachable": True,
            "free_disk_gb": 50.0,
            "credentials_configured": True,
            "agent_installed": True,
        }
        base.update(overrides)
        return base

    def test_network_connectivity_passes_when_reachable(self):
        r = check_network_connectivity(self._server(reachable=True))
        assert r.passed is True

    def test_network_connectivity_fails_when_not_reachable(self):
        r = check_network_connectivity(self._server(reachable=False))
        assert r.passed is False

    def test_disk_space_passes_when_sufficient(self):
        r = check_disk_space(self._server(free_disk_gb=20.0), min_free_gb=10.0)
        assert r.passed is True

    def test_disk_space_fails_when_insufficient(self):
        r = check_disk_space(self._server(free_disk_gb=5.0), min_free_gb=10.0)
        assert r.passed is False

    def test_credentials_passes_when_configured(self):
        r = check_credentials(self._server(credentials_configured=True))
        assert r.passed is True

    def test_credentials_fails_when_not_configured(self):
        r = check_credentials(self._server(credentials_configured=False))
        assert r.passed is False

    def test_agent_installed_passes(self):
        r = check_agent_installed(self._server(agent_installed=True))
        assert r.passed is True

    def test_agent_installed_fails(self):
        r = check_agent_installed(self._server(agent_installed=False))
        assert r.passed is False

    def test_run_preflight_returns_results_for_all_servers(self):
        wave = {
            "wave_name": "W",
            "servers": [self._server(server_id="s1"), self._server(server_id="s2")],
        }
        results = run_preflight(wave)
        # 4 checks × 2 servers
        assert len(results) == 8


# ---------------------------------------------------------------------------
# execute_migration.py tests
# ---------------------------------------------------------------------------
from scripts.execute_migration import execute_task, run_pipeline


class TestExecuteTask:
    def _task(self, task_type="automated", task_id="T01", name="Test Task"):
        return {"task_id": task_id, "name": name, "type": task_type}

    def _server(self):
        return {"server_id": "srv-exec", "hostname": "exec-host"}

    def test_dry_run_returns_true(self):
        assert execute_task(self._task(), self._server(), dry_run=True) is True

    def test_manual_task_returns_true_without_execution(self):
        assert execute_task(self._task(task_type="manual"), self._server(), dry_run=False) is True

    def test_automated_task_live_returns_true(self):
        assert execute_task(self._task(), self._server(), dry_run=False) is True

    def test_run_pipeline_with_empty_tasks_returns_true(self):
        wave = {"servers": [self._server()]}
        pipeline = {"tasks": []}
        assert run_pipeline(wave, pipeline, dry_run=True) is True


# ---------------------------------------------------------------------------
# post_migration_validate.py tests
# ---------------------------------------------------------------------------
from scripts.post_migration_validate import (
    check_application_health,
    check_data_integrity,
    check_services_running,
    check_target_reachability,
    run_validation,
)


class TestPostMigrationValidation:
    def _server(self, **overrides):
        base = {
            "server_id": "srv-val",
            "target_reachable": True,
            "target_services_running": True,
            "target_app_healthy": True,
            "target_data_integrity": True,
        }
        base.update(overrides)
        return base

    def test_target_reachability_passes(self):
        assert check_target_reachability(self._server()).passed is True

    def test_target_reachability_fails(self):
        assert check_target_reachability(self._server(target_reachable=False)).passed is False

    def test_services_running_passes(self):
        assert check_services_running(self._server()).passed is True

    def test_services_running_fails(self):
        assert check_services_running(self._server(target_services_running=False)).passed is False

    def test_application_health_passes(self):
        assert check_application_health(self._server()).passed is True

    def test_application_health_fails(self):
        assert check_application_health(self._server(target_app_healthy=False)).passed is False

    def test_data_integrity_passes(self):
        assert check_data_integrity(self._server()).passed is True

    def test_data_integrity_fails(self):
        assert check_data_integrity(self._server(target_data_integrity=False)).passed is False

    def test_run_validation_returns_results_for_all_servers(self):
        wave = {
            "wave_name": "W",
            "servers": [self._server(server_id="s1"), self._server(server_id="s2")],
        }
        results = run_validation(wave)
        # 4 checks × 2 servers
        assert len(results) == 8

    def test_run_validation_all_pass(self):
        wave = {"wave_name": "W", "servers": [self._server()]}
        results = run_validation(wave)
        assert all(r.passed for r in results)
