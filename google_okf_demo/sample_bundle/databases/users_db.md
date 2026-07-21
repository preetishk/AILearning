---
type: database_table
title: Users Database Table
description: PostgreSQL table storing user accounts, password hashes, and MFA configurations.
resource: postgresql://prod-cluster.internal:5432/identity_db#users
tags:
  - database
  - postgresql
  - user-data
  - pii
timestamp: 2026-07-21T09:00:00Z
author: dba-team@example.com
version: 3.1.0
status: active
---

# Users Database Table

Contains core user identity records in PostgreSQL cluster `identity_db`.

## Schema Definition

| Column | Type | Description |
|---|---|---|
| `id` | `UUID` | Primary Key |
| `email` | `VARCHAR(255)` | Unique user email address |
| `password_hash` | `TEXT` | Argon2id password hash |
| `status` | `VARCHAR(50)` | Active, Suspended, Pending |

## Security & Compliance

- Contains PII. Accessible only by [User Authentication Service](../services/auth_service.md).
- Automated daily snapshots stored in encrypted S3 bucket.
