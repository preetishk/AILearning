---
type: index
title: Open Knowledge Format Catalog
description: Auto-generated central index of all OKF knowledge units in this bundle.
timestamp: '2026-07-21T13:52:26.889670'
---

# Open Knowledge Format Catalog

Total Knowledge Units: **10**

## Type: `database_table`
- [Transactions Database Table](./databases/transactions_db.md) - Relational table recording financial transactions, billing events, and audit traces.
- [Users Database Table](./databases/users_db.md) - PostgreSQL table storing user accounts, password hashes, and MFA configurations.

## Type: `metric`
- [API P99 Latency](./metrics/api_latency.md) - Histogram tracking 99th percentile response duration across all public API gateways.
- [Authentication Failure Rate](./metrics/auth_failure_rate.md) - Prometheus metric measuring percentage of failed login & token validation attempts.

## Type: `policy`
- [Password Security Policy](./policies/password_policy.md) - Enforces complexity and Argon2 hashing requirements.

## Type: `runbook`
- [Auth Outage Incident Recovery Runbook](./runbooks/auth_outage_recovery.md) - Step-by-step incident response playbook when authentication service degradation occurs.

## Type: `service`
- [User Authentication Service](./services/auth_service.md) - Core authentication & JWT token generation microservice for the platform.
- [Payment Processing Service](./services/payment_service.md) - Manages stripe integration, subscription billing, and payment transaction logging.
