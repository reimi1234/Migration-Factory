# Rehost (Lift-and-Shift) Runbook

This runbook covers the steps to migrate a workload using the **rehost** strategy – moving a server to the cloud with no application code or configuration changes.

## When to Use Rehost

Use rehost when:
- Time-to-migrate is the primary constraint
- The application cannot be modified easily
- You plan to optimise the workload post-migration

## Pipeline Overview

| Step | Task | Type | Description |
|------|------|------|-------------|
| 1 | Install Migration Agent | Automated | Install replication agent on source |
| 2 | Start Initial Replication | Automated | Full-disk replication to target |
| 3 | Monitor Replication Progress | Automated | Wait for lag to reach acceptable level |
| 4 | Approve Cutover | Manual | Team lead approval required |
| 5 | Execute Cutover | Automated | Stop source, launch target, redirect traffic |
| 6 | Run Post-Migration Tests | Automated | Automated smoke tests on target |
| 7 | Confirm Success & Decommission Source | Manual | Application owner sign-off |

## Pre-Requisites Checklist

- [ ] Pre-flight checks passing (`preflight_check.py`)
- [ ] Maintenance window scheduled and communicated to stakeholders
- [ ] Rollback plan documented and reviewed
- [ ] Target instance type and storage confirmed
- [ ] Security groups and IAM roles provisioned in target

## Execution Steps

### Step 1 – Install Migration Agent

```bash
python scripts/execute_migration.py \
  --wave WAVE_1 \
  --config config/wave_config.json \
  --pipeline templates/rehost_pipeline.json \
  --dry-run
```

Review the dry-run output, then remove `--dry-run` to execute.

### Step 2 – Monitor Replication

Check replication lag in your migration tool dashboard (e.g. AWS MGN, CloudEndure). Proceed to cutover only when lag is < 1 minute.

### Step 3 – Cutover

1. Notify stakeholders that cutover is starting.
2. Stop workloads on source server (graceful shutdown preferred).
3. Execute the cutover task in the pipeline.
4. Update DNS / load balancer to point to the target.

### Step 4 – Validate

```bash
python scripts/post_migration_validate.py \
  --wave WAVE_1 \
  --config config/wave_config.json
```

All validation checks must pass before confirming success.

## Rollback Procedure

If the migration fails after cutover:

1. Redirect traffic back to the source (revert DNS / load balancer).
2. Restart any services stopped on the source.
3. Notify stakeholders of the rollback.
4. Root-cause the failure and reschedule.

## Post-Migration Tasks

- [ ] Update CMDB with new instance details
- [ ] Remove source server from monitoring
- [ ] Schedule source server decommission (default: 30 days after successful validation)
- [ ] Update runbooks and documentation
