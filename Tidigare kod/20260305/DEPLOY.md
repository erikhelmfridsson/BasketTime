# Ladda upp till GitHub och Render

## Steg 1: Spara och pusha till GitHub

Kör i terminalen från projektmappen `PlayTime`:

```powershell
# 1. Lägg till ändrade filer (utan mappen "Tidigare kod" om du inte vill ha med den)
git add README.md app.js i18n.js locales/ styles.css

# 2. Committa med ett meddelande
git commit -m "Uppdateringar: Gå till match, Plan/Bänk före start, stapeldiagram-CSS, m.m."

# 3. Pusha till GitHub
git push origin main
```

Om du får fel om att `origin` saknas:
```powershell
git remote -v
```
Om det inte står någon `origin`, koppla till ditt repo:
```powershell
git remote add origin https://github.com/DITT-ANVANDARNAMME/DITT-REPO-NAMN.git
```

Om du får **autentiseringsfel** vid push:
- GitHub accepterar inte längre lösenord för git över HTTPS. Använd antingen:
  - **Personal Access Token (PAT):** GitHub → Settings → Developer settings → Personal access tokens. Skapa en token med scope `repo`. Använd token som lösenord när `git push` frågar.
  - **SSH:** Sätt upp SSH-nyckel och använd en URL som `git@github.com:användare/repo.git`.

---

## Steg 2: Render ska bygga från GitHub

1. **Logga in på [Render](https://render.com)** och öppna ditt BasketTime-projekt (Web Service).

2. **Auto Deploy:** Kontrollera att **Auto-Deploy** är aktiverat för `main` (Settings → Build & Deploy). Då startar en ny deploy automatiskt när du pushat till `main`.

3. **Manuell deploy:** Om du vill bygga utan ny push: Dashboard → din tjänst → **Manual Deploy** → **Deploy latest commit**.

4. **Miljövariabler på Render:**  
   Under **Environment** ska du ha:
   - `DATABASE_URL` – din Render PostgreSQL-databas-URL (om du använder PostgreSQL).
   - `SECRET_KEY` – en hemlig nyckel för sessioner (t.ex. en lång slumpsträng).

5. **Build command** (vanligt för Flask):  
   `pip install -r requirements.txt`

6. **Start command:**  
   `gunicorn app:app`  
   (eller `python app.py` om du inte använder gunicorn; Render rekommenderar gunicorn.)

---

## Vanliga fel

| Problem | Lösning |
|--------|--------|
| `git push` kräver inloggning | Använd PAT eller SSH (se ovan). |
| `! [rejected] main -> main` | Någon annan har pushat. Kör `git pull origin main` och sedan `git push origin main`. |
| Render: "Build failed" | Kolla build-loggen. Saknas `requirements.txt` eller fel Python-version? Ställ **Python Version** under Environment till t.ex. 3.12. |
| Render: App kraschar efter start | Kolla att `DATABASE_URL` och `SECRET_KEY` är satta och att startkommandot är `gunicorn app:app`. |
| Sidan visar "Application failed" | Öppna **Logs** på Render för felmeddelanden; ofta databas eller miljövariabler. |

---

## Snabbkommandon (kopiera och klistra in)

```powershell
cd c:\Users\erik\Helmkon\Kod\PlayTime
git add README.md app.js i18n.js locales/de.json locales/en.json locales/sv.json styles.css
git commit -m "Uppdateringar för BasketTime"
git push origin main
```

Efter lyckad push väntar du någon minut så att Render bygger och startar om tjänsten (om Auto Deploy är på).
