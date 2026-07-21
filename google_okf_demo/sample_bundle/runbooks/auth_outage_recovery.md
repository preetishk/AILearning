---
type: runbook
title: Auth Outage Incident Recovery Runbook
description: Step-by-step incident response playbook when authentication service degradation occurs.
resource: https://wiki.internal/runbooks/auth-recovery
tags:
  - runbook
  - incident-response
  - auth
  - sre
timestamp: 2026-07-21T11:00:00Z
author: sre-team@example.com
version: 1.2.0
status: active
---

# Auth Outage Recovery Runbook

Follow these steps when [Auth Failure Rate Metric](../metrics/auth_failure_rate.md) breaches critical threshold (> 5%).

## Step 1: Verify Health of User Service

Check health logs for [User Authentication Service](../services/auth_service.md):

```bash
kubectl logs -l app=auth-service --tail=100
```

## Step 2: Check Database Connection Pool

Ensure pool connections to [Users Database Table](../databases/users_db.md) are not exhausted.

```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
```

## Step 3: Emergency Restart & Rollback

If memory leak or deadlock suspected, perform a zero-downtime rolling restart:

```bash
kubectl rollout restart deployment/auth-service
```
