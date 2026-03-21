# BasketTime – dokumentationsindex

Alla guider ligger i **projektroten** (samma mapp som `app.py`). Kort vad varje fil handlar om:

| Fil | Innehåll |
|-----|----------|
| **[README.md](./README.md)** | Vad BasketTime är, köra lokalt, deploy-översikt, länkar till övriga guider. |
| **[DOCS.md](./DOCS.md)** | Denna fil – översikt över dokumentationen. |
| **[TODO.md](./TODO.md)** | Att-göra-lista för drift, test efter deploy och valfria förbättringar. |
| **[DEPLOY.md](./DEPLOY.md)** | Git/GitHub, Render auto-deploy, miljövariabler, felsökning, PWA-cache (`sw.js`). |
| **[STANDARD-SETUP.md](./STANDARD-SETUP.md)** | Rekommenderad Render-konfiguration (Blueprint `render.yaml` eller manuellt). |
| **[RENDER-DATABAS-OCH-DOMAN.md](./RENDER-DATABAS-OCH-DOMAN.md)** | PostgreSQL på Render, `DATABASE_URL`/`SECRET_KEY`, egen domän & HTTPS, **e-post/SMTP** och `PUBLIC_APP_URL` för lösenordsåterställning. |
| **[DATABAS-LOOPIA.md](./DATABAS-LOOPIA.md)** | MariaDB/MySQL i **Loopia** (om du inte använder Render PostgreSQL); begränsningar för app på Render. |
| **[FLYTTA-TILL-LOOPIA.md](./FLYTTA-TILL-LOOPIA.md)** | Flytta från Render till Loopia (VPS) eller bara peka domän mot Render. |
| **[VERSION-1.0-CHECKLIST.md](./VERSION-1.0-CHECKLIST.md)** | Checklista inför/när du släpper 1.0 (säkerhet, UX, test). |

### Snabb vägval

- **Bara köra lokalt:** [README.md](./README.md)  
- **Deploy på Render:** [README.md](./README.md) → [STANDARD-SETUP.md](./STANDARD-SETUP.md) / [RENDER-DATABAS-OCH-DOMAN.md](./RENDER-DATABAS-OCH-DOMAN.md)  
- **Glömt lösenord / mail:** [RENDER-DATABAS-OCH-DOMAN.md](./RENDER-DATABAS-OCH-DOMAN.md) (avsnitt om SMTP)  
- **Push till GitHub & felsökning:** [DEPLOY.md](./DEPLOY.md)  
- **Loopia-databas eller VPS:** [DATABAS-LOOPIA.md](./DATABAS-LOOPIA.md), [FLYTTA-TILL-LOOPIA.md](./FLYTTA-TILL-LOOPIA.md)

### Cursor-regler (`.cursor/rules/`)

| Regel | Innehåll |
|-------|----------|
| **baskettime-funktionsindex.mdc** | Fullständigt funktionsindex: API, filer, data, miljöer (`alwaysApply`). |
| **baskettime-core-and-ux.mdc** | Kärnapp, matchflöde, statistik/diagram, PWA, layout. |
| **baskettime-auth-deploy-context.mdc** | Auth, e-post, lösenordsåterställning, SMTP/Render. |
| **baskettime-project-context.mdc** | i18n, `t()`-konventioner, appstart, felsökning. |

Uppdatera **funktionsindex** när du lägger till större funktioner så att inget faller mellan stolarna.
