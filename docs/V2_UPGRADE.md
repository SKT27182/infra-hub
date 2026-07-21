# Infra Hub v2 breaking deployment

Infra Hub v2 has no v1 API or database compatibility layer. The only
application API is `/api/v2`; old browser sessions and every unversioned
`/api/...` integration stop working.

## Fresh deployment

No database migration, volume migration, or backup workflow is included. For
an existing v1 installation, stop the application and explicitly recreate the
Infra Hub PostgreSQL data before starting v2. Other service data already uses
bind mounts beneath `INFRA_PERSIST_DIR` and is not copied by application code.

1. Review `backend/.env`. Keep `SERVICE_BIND_HOST`, `API_HOST`, and
   `APP_PUBLIC_HOST` on loopback.
2. Run `make clean-hard` only if you intentionally want to remove all current
   Infra Hub service data, then run `make up`.
3. Run `make db-bootstrap` to create the v2 user table and insert the configured
   default account only when it does not already exist.
4. Start the v2 backend/frontend and require every user to sign in again.

`password123` is supported for the requested temporary local setup, but it is
not suitable for a shared or network-accessible deployment. Replace the service
passwords and administrator password before changing the loopback-only model.

## Database-only account provisioning

Generate a bcrypt hash independently (never put the plaintext in SQL), then run:

```sql
INSERT INTO users (email, hashed_password, name, is_active)
VALUES (lower('operator@example.test'), '<bcrypt-hash>', 'Operator', TRUE);
```

There is no signup, user-management, activation, deletion, password-reset, or
recovery HTTP endpoint. If an operator replaces a password hash directly,
increment `auth_version` to revoke existing sessions.

## Verification

- `docker compose --env-file backend/.env config` resolves every published port
  to `127.0.0.1`.
- Every persistent bind source is beneath `INFRA_PERSIST_DIR`.
- `uv run pytest`, Ruff, mypy, frontend lint, and frontend build pass.
- Login creates an HttpOnly Strict cookie and browser storage contains no token.
- Service-card and Containers actions agree with `docker inspect` after start,
  stop, and restart. Stopping leaves the image and persistent data in place.
- PostgreSQL and Neo4j privileged queries accept writes, reject multiple
  statements, time out after ten seconds, and truncate returned rows.
