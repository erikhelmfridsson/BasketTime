# Skapa databas på Loopia för BasketTime

Appen behöver en databas för **användare** och **lag** (plus matcher). **Standard i detta repo** är PostgreSQL på Render (via `DATABASE_URL`) eller SQLite lokalt. Denna guide gäller om du vill använda **MariaDB/MySQL hos Loopia** i stället (t.ex. på VPS eller annan hosting som når databasen).

På Loopia skapar du **MariaDB/MySQL** enligt nedan.

---

## Steg 1: Skapa databasen i Loopia Kundzon

1. Logga in på **loopia.se/loggain** (Kundzon).
2. Gå till **Lägg till / Skapa…** → **Databaser**.
3. Klicka **Lägg till** → **Ny MariaDB/MySQL-databas**.
4. Välj vilket **domännamn** databasen ska kopplas till.
5. Fyll i en beskrivning (t.ex. "BasketTime") och klicka **Lägg till**.

Notera:
- **Databasserver:** t.ex. `mysql123.loopia.se`
- **Databasens namn:** t.ex. `dittdomän_se`

---

## Steg 2: Skapa databasanvändare

1. Öppna den databas du skapade.
2. Skapa en **ny användare** med lösenord.
3. Ge användaren **alla rättigheter** på denna databas (för att tabellerna ska kunna skapas).
4. Spara och notera:
   - **Användarnamn:** t.ex. `dbanv@s13579` (format användarnamn@servernummer)
   - **Lösenord:** det du angav

---

## Steg 3: Anslutningssträng (DATABASE_URL)

Format för MySQL/MariaDB:

```
mysql+pymysql://ANVÄNDARE:LÖSENORD@SERVER/DATABASNAMN
```

**Exempel** (ersätt med dina uppgifter från Loopia):

```
mysql+pymysql://dbanv%40s13579:MittLösenord@mysql123.loopia.se/dittdomän_se
```

**OBS:** Om lösenordet innehåller tecken som `@`, `#`, `%` eller `?` måste de **URL-kodas** (t.ex. `@` → `%40`).

---

## Steg 4: Var kör du appen?

- **Appen på Loopia (samma webbhotell som databasen):**  
  Använd servernamn från Loopia (t.ex. `mysql123.loopia.se`). Kontrollera i Kundzon om du ska använda `localhost` eller servernamnet.

- **Appen på Render (eller annan molntjänst):**  
  Loopia tillåter oftast **inte** anslutning till MySQL från internet (endast från deras egna servrar). Då kan du **inte** använda Loopia-databasen med en app som bara kör på Render. Använd då istället t.ex. **Render PostgreSQL** (som du redan kan ha) eller en moln-MySQL som tillåter fjärranslutning.

---

## Steg 5: Sätt DATABASE_URL i appen

- **Lokalt:** Skapa en fil `.env` (lägg den i `.gitignore`) med t.ex.:
  ```
  DATABASE_URL=mysql+pymysql://användare:lösenord@mysql123.loopia.se/databasnamn
  ```
  Ladda den i appen (t.ex. med `python-dotenv`) eller exportera i terminalen innan du startar.

- **På Loopia / produktion:** Sätt miljövariabeln **DATABASE_URL** i din hosting-panel till samma sträng.

När appen startar skapar den tabellerna (användare, lag, matcher) automatiskt via `db.create_all()`.

---

## Sammanfattning

| Uppgift        | Var du hittar det i Loopia     |
|----------------|---------------------------------|
| Databasserver  | Sidan för databasen, t.ex. mysqlXXX.loopia.se |
| Databasnamn    | Samma sida                      |
| Användarnamn   | Databasanvändaren, t.ex. anv@servernr |
| Lösenord       | Det du angav för användaren     |

Koppla ihop till appen med `DATABASE_URL=mysql+pymysql://...`. **PyMySQL** finns i `requirements.txt`; SQLAlchemy använder drivaren för MySQL-URL:er.

**OBS:** Om du kör på **Render** med PostgreSQL behöver du normalt **inte** denna guide – använd Render PostgreSQL och `postgresql://...` (se [RENDER-DATABAS-OCH-DOMAN.md](./RENDER-DATABAS-OCH-DOMAN.md)).
