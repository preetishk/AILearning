---
type: service
title: User Authentication Service
description: Core authentication & JWT token generation microservice for the platform.
resource: https://github.com/org/auth-service
tags:
  - auth
  - security
  - identity
  - core-services
timestamp: 2026-07-21T10:00:00Z
author: security-team@example.com
version: 2.4.0
status: active
---

# User Authentication Service

The **User Authentication Service** handles OAuth2, session validation, and JWT issuing for all API requests.

## Key Dependencies & Architecture

- **Primary Database**: Reads and updates user credentials in the [Users Database Table](../databases/users_db.md).
- **Monitoring & Alerting**: Key performance metric is [Auth Failure Rate Metric](../metrics/auth_failure_rate.md).
- **Emergency Procedure**: In case of auth degradation or token verification failures, consult the [Auth Outage Recovery Runbook](../runbooks/auth_outage_recovery.md).

## Operational Details

- Port: `8080`
- Token Expiry: `15 minutes` (Refresh tokens: `7 days`)
- Rate Limit: `100 requests / min` per IP address.
