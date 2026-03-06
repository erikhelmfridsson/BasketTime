# BasketTime

PWA för speltidsregistrering i basket (11 spelare, säsongsstatistik, CSV-export). Inloggning och data lagras i backend (Flask + SQLite/PostgreSQL).

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

4. **Första gången:** Det finns inget konto. Klicka på **Skapa konto**, ange användarnamn (minst 2 tecken) och lösenord (minst 6 tecken). Logga in sedan med samma uppgifter.

Lokalt används SQLite-databasen `baskettime.db` i projektmappen (om du inte sätter `DATABASE_URL`).

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
