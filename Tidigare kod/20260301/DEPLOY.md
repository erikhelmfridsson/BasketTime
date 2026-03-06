# Deploy BasketTime to Render.com with custom domain (app.baskettime.app)

This project is a **Flask** app (static frontend + API). Follow these steps to deploy on Render and point **app.baskettime.app** to it via Loopia DNS.

---

## 1. Push the project to GitHub

1. Create a new repository on [GitHub](https://github.com/new) (e.g. `baskettime`).
2. From your project root:

   ```bash
   git init
   git add .
   git commit -m "Initial commit – BasketTime + Render setup"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

   Replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub user and repo name.

---

## 2. Create a Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/) and sign in (or use GitHub).
2. Click **New +** → **Web Service**.
3. Connect your GitHub account if needed, then select the repository that contains this project.
4. Use the settings below.

---

## 3. Render service settings (exact values)

| Setting | Value |
|--------|--------|
| **Name** | `baskettime` (or any name; you’ll use it in the CNAME) |
| **Region** | Choose closest to your users (e.g. Frankfurt) |
| **Branch** | `main` |
| **Runtime** | `Python 3` (uses `runtime.txt`) |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --bind 0.0.0.0:$PORT app:app` |
| **Instance Type** | Free (or paid if you prefer) |

**Environment variables** (Environment tab → Add Environment Variable):

| Key | Value | Required |
|-----|--------|----------|
| `SECRET_KEY` | Long random string (e.g. generate with `openssl rand -hex 32`) | Yes, for production |
| `DATABASE_URL` | (Leave empty at first, or add after creating PostgreSQL – see below) | Optional; app uses SQLite if not set |

After saving, Render will build and deploy. Your app will be at:

**https://&lt;your-service-name&gt;.onrender.com**

(e.g. `https://baskettime.onrender.com` if the service name is `baskettime`).

---

## 4. (Optional) Attach PostgreSQL on Render

1. In Render Dashboard: **New +** → **PostgreSQL**.
2. Create the database (e.g. same region as the Web Service).
3. Open the Web Service → **Environment**.
4. In the PostgreSQL service, copy **Internal Database URL** (or **External** if you need off-Render access).
5. Add it as `DATABASE_URL` in the Web Service’s environment variables.
6. Redeploy the Web Service if it was already running.

**Note:** If `DATABASE_URL` is not set, the app uses SQLite (file-based DB). For production with multiple instances or persistence across deploys, use PostgreSQL.

---

## 5. Custom domain: Loopia DNS (app.baskettime.app)

1. In Render: open your Web Service → **Settings** → **Custom Domains**.
2. Click **Add Custom Domain** and enter: **`app.baskettime.app`**.
3. Render will show the target hostname: **`&lt;your-service-name&gt;.onrender.com`** (same as the default URL).
4. In **Loopia** (where `baskettime.app` is managed):
   - Add or edit a **CNAME** record:
     - **Host/Name:** `app` (so the full name is `app.baskettime.app`).
     - **Target/Points to:** `&lt;your-service-name&gt;.onrender.com`  
       Example: `baskettime.onrender.com`.
   - Remove any conflicting A or CNAME for `app` if present.
5. Save in Loopia. DNS can take a few minutes to propagate.
6. Back in Render, wait until the domain shows as verified (green). Render will issue HTTPS automatically.

Result:

- **app.baskettime.app** → **https://&lt;your-service-name&gt;.onrender.com** (HTTPS).

---

## 6. HTTPS

- Render serves your app over **HTTPS** by default. No extra config needed.
- The app does not rely on hardcoded `http://` links; use relative URLs or `https` where needed.

---

## Quick reference

| Item | Value |
|------|--------|
| **Framework** | Flask |
| **Build command** | `pip install -r requirements.txt` |
| **Start command** | `gunicorn --bind 0.0.0.0:$PORT app:app` |
| **CNAME (Loopia)** | `app` → `&lt;your-service-name&gt;.onrender.com` |
| **Custom domain** | `app.baskettime.app` |
