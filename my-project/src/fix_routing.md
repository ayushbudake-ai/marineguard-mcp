# Why the browser is still showing the React Router splash page

Your project's file tree (app/, build/, .react-router/, Dockerfile) is React
Router v7 "Framework Mode" — the `npx create-react-router@latest` scaffold —
not a plain Vite SPA. Framework mode owns its own root shell (app/root.tsx)
and route table (app/routes.ts), separate from the src/ folder the
MarineGuard pages were built into.

Nothing in app/routes.ts points at any MarineGuard page yet, so the dev
server is still serving the scaffold's default route — that ">< React
Router / What's next?" screen is app/welcome/welcome.tsx, the template's
own placeholder. The build succeeding and the assistant reporting success
just means the code compiles; it doesn't mean the router points anywhere
new. That's a separate step.

## Fix — 3 changes

1. **Replace app/routes.ts** with the contents of `app-routes.ts` in this
   zip (rename it to `app/routes.ts`, overwriting the scaffold's version).
   It registers DashboardLayout as the shared layout and every page as a
   child route.

2. **Import the stylesheet once**, near the top of `app/root.tsx`:
   ```ts
   import "../src/index.css";
   ```
   Leave the rest of root.tsx (the `Layout` / `<Meta />` / `<Links />` /
   `<Scripts />` shell) untouched — that part isn't route-specific.

3. **Restart the dev server** (`npm run dev`) so Vite picks up the new
   route table — a hot reload sometimes doesn't re-read app/routes.ts.

## Two more things this unblocks

- **Metrics.jsx, Reports.jsx, About.jsx** are new in this zip — the
  sidebar has always linked to `/metrics`, `/reports`, `/about`, but those
  three pages didn't actually exist until now. Without them, applying the
  route config above would just trade one broken screen for a build error
  on those three routes.

- **Detection Map needs two packages** that were assumed installed but
  never confirmed:
  ```
  npm install leaflet react-leaflet
  ```
  If you skip this, every other route will work fine — it'll only break
  when you click into Detection Map specifically.

If your actual `app/routes.ts` or `app/root.tsx` look meaningfully
different from the standard scaffold (e.g. you're on file-based routing
instead of config-based), paste their current contents and the exact fix
can be adjusted to match.
