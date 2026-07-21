---
type: database_table
title: Transactions Database Table
description: Relational table recording financial transactions, billing events, and audit traces.
resource: postgresql://prod-cluster.internal:5432/finance_db#transactions
tags:
  - database
  - postgresql
  - transactions
  - finance
timestamp: 2026-07-21T09:15:00Z
author: dba-team@example.com
version: 2.0.0
status: active
---

# Transactions Database Table

Maintained by [Payment Processing Service](../services/payment_service.md).

## Key Information

- Partitioned monthly by `created_at`.
- High write volume; read-replicas used for financial analytics.
