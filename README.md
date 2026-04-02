# Migration Factory

A co-pilot workspace for orchestrating and automating large-scale cloud migrations. This repository provides scripts, templates, and configuration files to help migration teams plan, execute, and validate workload migrations at scale.

## Overview

The Migration Factory workspace standardises the migration process through:

- **Automated scripts** – Python utilities for discovery, pre-flight checks, execution, and validation
- **Pipeline templates** – JSON definitions for repeatable migration workflows
- **Configuration files** – Per-environment and per-wave settings
- **Documentation & runbooks** – Step-by-step guides for common migration scenarios

## Repository Structure

```
Migration-Factory/
├── scripts/                     # Automation scripts
│   ├── assess.py                # Discovery and assessment
│   ├── preflight_check.py       # Pre-migration validation
│   ├── execute_migration.py     # Migration execution orchestrator
│   └── post_migration_validate.py # Post-migration validation
├── templates/                   # Pipeline templates (JSON)
│   ├── rehost_pipeline.json     # Lift-and-shift pipeline
│   ├── replatform_pipeline.json # Re-platform pipeline
│   └── retire_pipeline.json     # Decommission pipeline
├── config/                      # Configuration files
│   ├── environments.json        # Target environment definitions
│   └── wave_config.json         # Migration wave configuration
├── docs/                        # Documentation & runbooks
│   ├── getting_started.md       # Quick-start guide
│   ├── runbook_rehost.md        # Rehost (lift-and-shift) runbook
│   └── runbook_replatform.md    # Re-platform runbook
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+
- Access credentials for source and target environments (see `config/environments.json`)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run an assessment

```bash
python scripts/assess.py --config config/wave_config.json
```

### Run pre-flight checks

```bash
python scripts/preflight_check.py --wave WAVE_1 --config config/wave_config.json
```

### Execute a migration wave

```bash
python scripts/execute_migration.py --wave WAVE_1 --pipeline templates/rehost_pipeline.json
```

### Validate the migration

```bash
python scripts/post_migration_validate.py --wave WAVE_1 --config config/wave_config.json
```

## Migration Pipeline Overview

Each migration goes through four phases:

| Phase | Script | Description |
|-------|--------|-------------|
| 1 – Assess | `assess.py` | Discover source workloads and capture inventory |
| 2 – Pre-flight | `preflight_check.py` | Validate network, credentials, and dependencies |
| 3 – Execute | `execute_migration.py` | Orchestrate replication and cutover |
| 4 – Validate | `post_migration_validate.py` | Confirm workloads are healthy in the target |

## Pipeline Templates

Templates in `templates/` define the ordered task list for each migration strategy:

| Template | Strategy | Description |
|----------|----------|-------------|
| `rehost_pipeline.json` | Rehost | Lift-and-shift with no code changes |
| `replatform_pipeline.json` | Replatform | Minor optimisations during migration |
| `retire_pipeline.json` | Retire | Decommission workloads no longer needed |

## Contributing

1. Fork the repository and create a feature branch.
2. Add or update scripts, templates, or documentation.
3. Open a pull request with a clear description of the change.

## License

This project is licensed under the MIT License.