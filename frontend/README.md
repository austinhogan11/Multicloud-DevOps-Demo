# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
## API base URL (prod)

When deploying the static site (S3/CloudFront), set an API base URL at build time:

1. Copy `.env.example` to `.env.production` and set `VITE_API_BASE` to your API Gateway URL, for example:

```
VITE_API_BASE=https://abc123.execute-api.us-east-1.amazonaws.com
```

2. Build:

```
npm run build
```

For local dev, no env is needed — the app uses `/api` and the Vite dev proxy forwards to the backend.
