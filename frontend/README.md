# Infra Hub Frontend

React + Vite dashboard for managing shared infrastructure services.

## Env configuration

Use `frontend/.env`:

```env
VITE_PORT=5143
VITE_DEV_API_TARGET=http://127.0.0.1:8888
```

- `VITE_PORT`: frontend dev/preview port
- `VITE_DEV_API_TARGET`: backend target used by Vite dev proxy for `/api`

## API routing model

Frontend calls **relative** `'/api'` routes (no hardcoded backend host).

- Local dev: Vite proxy forwards `/api` -> `VITE_DEV_API_TARGET`
- Server deploy: Nginx should forward `/api` -> backend

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
