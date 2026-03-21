# Standardlösning för BasketTime på Render

Detta är den rekommenderade grundkonfigurationen: en webbtjänst + en PostgreSQL-databas.

---

## Vad som ingår

| Komponent | Inställning |
|-----------|-------------|
| **Web Service** | Python, `gunicorn --workers 2`, port från `$PORT` |
| **Build** | `pip install -r requirements.txt` |
| **Databas** | PostgreSQL (plan: free; kan uppgraderas till starter osv.) |
| **Miljö** | `SECRET_KEY` (genereras av Render), `DATABASE_URL` (kopplas till databasen) |

Tabellerna (användare, lag, matcher) skapas automatiskt när appen startar. Befintliga databaser kan få extra kolumner för e-post/lösenordsåterställning utan manuell migrering (se `backend/schema_migrations.py`).

**Valfritt i produktion:** för **Glömt lösenord** och e-postlänkar, sätt även SMTP-variabler (`MAIL_*`) och **`PUBLIC_APP_URL`** enligt [RENDER-DATABAS-OCH-DOMAN.md](./RENDER-DATABAS-OCH-DOMAN.md).

---

## Sätt upp med Blueprint (render.yaml)

1. **Render Dashboard** → **New +** → **Blueprint**.
2. Koppla ditt **GitHub-repo** (BasketTime).
3. Render läser **render.yaml** i repot och skapar:
   - en **Web Service** (baskettime)
   - en **PostgreSQL** (baskettime-db) och kopplar **DATABASE_URL** till tjänsten.
4. Klicka **Apply** och vänta tills båda är gröna.

Du behöver inte fylla i Build/Start Command eller DATABASE_URL manuellt – det kommer från filen.

---

## Sätt upp manuellt (utan Blueprint)

Om du skippar render.yaml och skapar tjänst + databas själv:

1. **New +** → **PostgreSQL** → namn t.ex. `baskettime-db`, plan **Free** → Create.
2. **New +** → **Web Service** → koppla repo, branch `main`.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `gunicorn --workers 2 --bind 0.0.0.0:$PORT app:app`
5. **Environment:** Lägg till **SECRET_KEY** (generera eller skriv egen). Klicka **Connect** på databasen och lägg till **DATABASE_URL** (Internal URL).

---

## Uppgradera senare

- **Databas:** Byt plan (t.ex. Free → Starter) under databasens **Settings** om du behöver mer kapacitet eller längre retention.
- **Webb:** Öka **Instance Type** eller antal workers i Start Command (t.ex. `--workers 4`) om du vill hantera fler samtidiga användare.

Detta är standardlösningen – inget mer behövs för att komma igång.
