# Getting Started with Migration Factory

This guide walks you through setting up and running your first migration wave.

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.9+ |
| pip | latest |
| Access to source environment | SSH/WinRM credentials |
| Access to target environment | Cloud provider credentials |

## 1. Clone and Set Up

```bash
git clone https://github.com/reimi1234/Migration-Factory.git
cd Migration-Factory
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure Your Environments

Edit `config/environments.json` and replace the placeholder values with your actual VPC, subnet, and security group IDs:

```json
{
  "environments": {
    "target": {
      "vpc_id": "vpc-0abc123456789",
      "subnet_ids": ["subnet-0abc123456789"],
      "security_group_ids": ["sg-0abc123456789"]
    }
  }
}
```

## 3. Configure Your Migration Waves

Edit `config/wave_config.json` to reflect your server inventory. For each server, provide:

- `server_id` – unique identifier
- `hostname` / `ip_address` – source server details
- `os`, `cpu_cores`, `ram_gb`, `disk_gb` – workload sizing
- `tags.migration_strategy` – one of `rehost`, `replatform`, `retire`

## 4. Run the Assessment

```bash
python scripts/assess.py --config config/wave_config.json --output inventory.json
```

Review `inventory.json` to verify the recommended migration strategies.

## 5. Run Pre-flight Checks

```bash
python scripts/preflight_check.py --wave WAVE_1 --config config/wave_config.json
```

All checks must pass before proceeding. Address any failures listed in the summary.

## 6. Execute the Migration

Choose the pipeline that matches your strategy:

| Strategy | Pipeline template |
|----------|------------------|
| Rehost | `templates/rehost_pipeline.json` |
| Replatform | `templates/replatform_pipeline.json` |
| Retire | `templates/retire_pipeline.json` |

Run a dry-run first to preview actions:

```bash
python scripts/execute_migration.py \
  --wave WAVE_1 \
  --config config/wave_config.json \
  --pipeline templates/rehost_pipeline.json \
  --dry-run
```

Then run the live migration:

```bash
python scripts/execute_migration.py \
  --wave WAVE_1 \
  --config config/wave_config.json \
  --pipeline templates/rehost_pipeline.json
```

## 7. Validate the Migration

```bash
python scripts/post_migration_validate.py --wave WAVE_1 --config config/wave_config.json
```

A `validation_report_WAVE_1.json` file will be created in the current directory with detailed results.

## Next Steps

- Review the runbooks in `docs/` for strategy-specific guidance.
- Add more waves to `config/wave_config.json` as you progress through your migration.
- Customise the pipeline templates in `templates/` to match your tooling.
