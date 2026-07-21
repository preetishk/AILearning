---
type: metric
title: Authentication Failure Rate
description: Prometheus metric measuring percentage of failed login & token validation attempts.
resource: https://grafana.internal/d/auth-metrics?panelId=4
tags:
  - metric
  - prometheus
  - auth
  - alerting
timestamp: 2026-07-21T08:00:00Z
author: devops-team@example.com
version: 1.0.0
status: active
---

# Authentication Failure Rate Metric

Measures ratio of `HTTP 401` / `HTTP 403` responses relative to total authentication traffic.

## Alerting Thresholds

- **Warning**: Failure rate > 2% over 5 minutes.
- **Critical**: Failure rate > 5% over 5 minutes. Triggers auto-page to SRE.
- **Resolution Procedure**: Refer to [Auth Outage Recovery Runbook](../runbooks/auth_outage_recovery.md).
