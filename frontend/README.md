# Infra Hub Frontend

React + Vite dashboard for managing shared infrastructure services.

## Env configuration

Use `frontend/.env`:

```env
VITE_PORT=5143
VITE_HOST=127.0.0.1
VITE_DEV_API_TARGET=http://127.0.0.1:8888
```

- `VITE_PORT`: frontend dev/preview port
- `VITE_DEV_API_TARGET`: backend target used by Vite dev proxy for `/api/v2`

## API routing model

Frontend calls **relative** `'/api/v2'` routes (no hardcoded backend host).

- Local dev: Vite proxy forwards `/api/v2` -> `VITE_DEV_API_TARGET`
- Server deploy: a same-origin proxy may forward `/api/v2` -> backend

This avoids changing frontend code between local and production.

## Development

```bash
pnpm install
pnpm dev
```

## Build

```bash
pnpm build
pnpm preview
```

## Notes

- Keep backend running before login or service actions.
- If API calls fail in dev, check backend is reachable at `VITE_DEV_API_TARGET`.
- Authentication uses an HttpOnly cookie. No bearer token or user record is stored in browser storage.
