# Frontend

Next.js App Router frontend for the Samanvay-AI procurement workspace.

```powershell
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` in `.env.local` to point at the FastAPI service. When the API is unreachable, the typed client uses `src/lib/mockData.ts`.