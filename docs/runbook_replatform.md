# Replatform Runbook

This runbook covers the steps to migrate a workload using the **replatform** strategy – moving to the cloud with minor architectural optimisations such as adopting a managed database service or containerising the application.

## When to Use Replatform

Use replatform when:
- You want to reduce operational overhead (e.g. move from self-managed DB to RDS/Cloud SQL)
- The application can tolerate minor configuration changes
- You want quick wins without a full re-architecture

## Common Replatform Patterns

| Source | Target |
|--------|--------|
| Self-managed MySQL/Postgres | Amazon RDS / Azure Database |
| Bare-metal / VM application | Container (ECS / AKS / GKE) |
| On-prem object storage | S3 / Azure Blob / GCS |
| Self-managed message queue | Amazon SQS / Azure Service Bus |

## Pipeline Overview

| Step | Task | Type | Description |
|------|------|------|-------------|
| 1 | Assessment & Architecture Review | Manual | Confirm target architecture |
| 2 | Provision Target Infrastructure | Automated | Deploy IaC templates |
| 3 | Migrate Data to Managed Service | Automated | Bulk-load or stream data |
| 4 | Deploy Application to Target | Automated | Deploy artefacts to new platform |
| 5 | Smoke Test | Automated | Automated integration tests |
| 6 | User Acceptance Testing | Manual | Application owner UAT |
| 7 | DNS Cutover | Automated | Switch traffic to target |
| 8 | Decommission Source | Manual | Final sign-off and cleanup |

## Pre-Requisites Checklist

- [ ] Target managed service provisioned and accessible
- [ ] Connection strings updated in application configuration
- [ ] Data migration scripts tested in non-production
- [ ] UAT environment prepared for stakeholder testing
- [ ] Rollback plan documented

## Execution Steps

### Step 1 – Provision Infrastructure

Deploy the target infrastructure using the IaC templates in `templates/`. Review and update `config/environments.json` with your target environment details.

### Step 2 – Migrate Data

Use the appropriate data migration tool:
- **Databases**: AWS DMS, Azure Database Migration Service, or `pg_dump` / `mysqldump`
- **Object storage**: `aws s3 sync` or `azcopy`
- **Files**: `rsync` over SSH

### Step 3 – Deploy Application

```bash
python scripts/execute_migration.py \
  --wave WAVE_1 \
  --config config/wave_config.json \
  --pipeline templates/replatform_pipeline.json
```

### Step 4 – Run UAT

Provide the application owner with access to the target environment. UAT should cover:
- Core user journeys
- Data read / write operations
- Integration with downstream systems

### Step 5 – DNS Cutover

Update DNS records with a low TTL (e.g. 60 seconds) at least 24 hours before cutover, then update the A/CNAME records to point to the target.

## Rollback Procedure

1. Revert DNS to point to source.
2. Confirm source data is still intact (no destructive operations performed).
3. Root-cause the failure and reschedule.

## Post-Migration Tasks

- [ ] Update CMDB
- [ ] Configure monitoring and alerting on the new managed service
- [ ] Remove source infrastructure after stabilisation period
- [ ] Document architecture changes
