# BasketTime

**Version 1.0** – PWA för speltidsregistrering i basket (11 spelare, säsongsstatistik, CSV-export). Inloggning och data lagras i backend (Flask + SQLite/PostgreSQL).

<!-- När appen är live på Render, lägg in länken här:
**Live:** https://ditt-projekt.onrender.com
-->

**Dokumentation:** se [DOCS.md](./DOCS.md) för index över alla guider. **Att göra** (drift, test, valfritt): [TODO.md](./TODO.md).

## Köra lokalt (med inloggning)

Appen kräver **Flask-backend** för inloggning. Öppna inte bara `index.html` och använd inte bara `npx serve` – då finns ingen `/api` och inloggning fungerar inte.

1. **Installera beroenden** (om du inte redan gjort det):
   ```bash
   pip install -r requirements.txt
   ```

2. **Starta servern** från projektmappen:
   ```bash
   python app.py
   ```
   Servern startar på **http://localhost:10000** (eller port i miljövariabeln `PORT`).

3. **Öppna i webbläsaren:**  
   Gå till **http://localhost:10000**

4. **Första gången:** Det finns inget konto. Klicka på **Skapa konto**, ange **användarnamn** (minst 2 tecken), **e-post** (obligatorisk för nya konton) och **lösenord** (minst 6 tecken). Logga in sedan med **användarnamn eller e-post** + lösenord.

Lokalt används SQLite-databasen `baskettime.db` i projektmappen (om du inte sätter `DATABASE_URL`). Vid start läggs vid behov till kolumner för e-post och lösenordsåterställning på befintliga databaser (se `backend/schema_migrations.py`).

**Glömt lösenord** kräver att kontot har en sparad e-post (nya konton har det; äldre konton kan lägga till e-post under **Inställningar**) och att servern har SMTP inställt – se [RENDER-DATABAS-OCH-DOMAN.md](./RENDER-DATABAS-OCH-DOMAN.md).

## Endast statiska filer (utan inloggning)

Om du bara vill titta på frontend utan backend:
```bash
npx serve
```
Öppna t.ex. http://localhost:3000. Då finns ingen inloggning – appen förväntar sig API och visar inloggningssidan som inte kan slutföras.

## Lägga till på hemskärm (iPhone)

1. Öppna BasketTime i **Safari** (inte i andra webbläsare).
2. Tryck på **Dela**-ikonen (fyrkant med pil uppåt).
3. Välj **Lägg till på hemskärmen**.
4. Namnge och tryck **Lägg till**.

Appen fungerar offline efter första besök (PWA-cache). För att använda inloggning och sparad data måste du öppna appen mot samma server (samma adress) som du loggade in på.

---

## Deploy på Render med PostgreSQL-databas

Så att appen körs på Render och använder deras databas:

### A) Nytt projekt med Blueprint (enklast)

1. **Lägg koden på GitHub** (om du inte redan gjort det):
   ```bash
   git add .
   git commit -m "BasketTime 1.0"
   git remote add origin https://github.com/DITT-ANVANDARNAMN/PlayTime.git
   git push -u origin main
   ```

2. **På Render:** Gå till [dashboard.render.com](https://dashboard.render.com) → **New +** → **Blueprint**.

3. **Koppla ditt GitHub-repo** (PlayTime) och välj repot. Render läser `render.yaml` i repot.

4. **Klicka Apply.** Render skapar då:
   - en **Web Service** (Flask-appen) med Build: `pip install -r requirements.txt`, Start: `gunicorn ...`
   - en **PostgreSQL-databas** (`baskettime-db`)
   - och kopplar **DATABASE_URL** från databasen till Web Service samt genererar **SECRET_KEY**.

5. **Vänta tills deployen är klar.** Öppna din app-URL (t.ex. `https://baskettime.onrender.com`). Vid första anrop skapas tabellerna automatiskt (`db.create_all()`). Skapa konto via **Skapa konto** (användarnamn, **e-post**, lösenord) och logga in.

### B) Du har redan en Web Service – koppla databas

1. **Skapa PostgreSQL på Render:** **New +** → **PostgreSQL**. Välj namn (t.ex. `baskettime-db`), region (samma som Web Service) → **Create Database**.

2. **Koppla till Web Service:** Öppna din **Web Service** → **Environment**:
   - Klicka **Connect** på databasen (på databasens sida) och kopiera **Internal Database URL**.
   - Lägg till variabel: **Key:** `DATABASE_URL`, **Value:** klistra in URL:en. Lägg gärna till `?sslmode=require` i slutet om den saknas (app.py lägger också till det automatiskt).
   - Sätt **SECRET_KEY** till en hemlig sträng (t.ex. generera med `openssl rand -hex 32`).

3. **Spara.** Render startar om appen. Tabellerna skapas vid första anrop.

### Kontrollera att det fungerar

- Öppna appens URL i webbläsaren.
- Klicka **Skapa konto**, skapa användare och logga in.
- Skapa ett lag, starta en match – data sparas i PostgreSQL.

Mer detaljer (domän, SSL, e-post för återställning, `PUBLIC_APP_URL`, cache): se **RENDER-DATABAS-OCH-DOMAN.md** och **DEPLOY.md**.
