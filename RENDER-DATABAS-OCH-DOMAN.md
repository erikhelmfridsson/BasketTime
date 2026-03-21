# Databas och domän (baskettime.app) på Render

Guide för att sätta upp PostgreSQL på Render, koppla appen med säker anslutning och använda **baskettime.app** med HTTPS.

---

## Del 1: Skapa PostgreSQL-databas på Render

1. Gå till **dashboard.render.com** och logga in.
2. Klicka **New +** → **PostgreSQL**.
3. Fyll i:
   - **Name:** t.ex. `baskettime-db`
   - **Database:** t.ex. `baskettime` (eller låt Render välja)
   - **User:** t.ex. `baskettime_user` (eller standard)
   - **Region:** välj **samma region** som din Web Service (t.ex. Frankfurt) så att appen använder **Internal URL** (snabbare och inom Render-nätet).
   - **PostgreSQL Version:** 15 eller 16.
4. Klicka **Create Database**.
5. Vänta tills status är **Available**.

### Hämta anslutnings-URL

- Öppna databasen → **Connect** (höger uppe).
- **Internal Database URL** – använd denna om din **Web Service (BasketTime)** ligger i samma region. Servernamn ser ut ungefär som `dpg-xxx-a.oregon-postgres.render.com` (internt).
- **External Database URL** – används om du kör appen utanför Render.

Kopiera **Internal Database URL** (om appen är på Render). Den ser ut ungefär så här:

```
postgres://baskettime_user:XXXX@dpg-xxxxx-a/baskettime
```

För att **tvinga SSL** (krypterad anslutning till databasen) lägger du till i slutet av URL:en (om den inte redan har parametrar):

```
?sslmode=require
```

Exempel:

```
postgres://baskettime_user:XXXX@dpg-xxxxx-a/baskettime?sslmode=require
```

(Appen konverterar automatiskt `postgres://` till `postgresql://`.)

---

## Del 2: Koppla databasen till BasketTime (Web Service)

1. Öppna din **Web Service** (BasketTime-appen) på Render.
2. Gå till **Environment**.
3. Kontrollera att dessa variabler finns (Render sätter ofta **DATABASE_URL** automatiskt om du kopplade databasen när du skapade tjänsten):
   - **DATABASE_URL** – klistra in **Internal Database URL** (med `?sslmode=require` om du vill tvinga SSL).
   - **SECRET_KEY** – en lång slumpmässig sträng (t.ex. genererad med `openssl rand -hex 32`).

Om databasen skapades separat: klicka **Connect** på databasen, kopiera **Internal Database URL**, lägg till `?sslmode=require` om du vill, och sätt som **DATABASE_URL** i Web Service.

4. Spara. Render startar om appen. Vid första anrop mot appen skapas tabellerna (användare, lag, matcher) automatiskt via `db.create_all()`.

### Vad som finns i databasen

- **users** – inloggade användare (användarnamn, lösenords-hash, valfri **e-post** för inloggning och lösenordsåterställning, samt fält för återställningstoken).
- **teams** – lag som användaren skapat.
- **team_players** – spelare i varje lag.
- **matches** – sparade matcher.
- **match_players** – spelardata per match.

Det finns ingen separat "admin"-tabell: varje inloggad användare hanterar **sina egna** lag och matcher. Första användaren som skapar konto är i praktiken den som kan använda appen; du kan senare lägga till en "admin"-roll i `User` om du vill.

---

## Del 3: Domän baskettime.app med HTTPS

Render ger **HTTPS automatiskt** för egen domän (gratis certifikat, förnyas automatiskt).

### Steg 1: Lägg till domän i Render

1. Öppna din **Web Service** (BasketTime) på Render.
2. Gå till **Settings** → **Custom Domains**.
3. Klicka **Add Custom Domain**.
4. Ange **baskettime.app** (och eventuellt **www.baskettime.app**).
5. Render visar vilka DNS-poster du ska skapa (och ev. ett tillfälligt CNAME för verifiering).

### Steg 2: DNS hos domänregistratorn (baskettime.app)

Du måste äga baskettime.app och hantera DNS där den är registrerad (t.ex. Loopia, GoDaddy, Cloudflare, Namecheap).

**För rotdomänen baskettime.app:**

- Många registratorer kräver **A-post** för rotdomän:
  - **Typ:** A  
  - **Värde/IP:** `216.24.57.1` (Render:s IP – dubbelkolla i Render Dashboard under Custom Domains).
- Om din leverantör stödjer **ALIAS/ANAME** mot en CNAME: peka mot det värde Render anger (t.ex. `baskettime.onrender.com`).

**För www.baskettime.app (valfritt):**

- **Typ:** CNAME  
- **Namn:** www  
- **Värde:** `din-app-namn.onrender.com` (exakt värdnamn som Render visar för din tjänst).

Ta bort eventuella **AAAA**-poster (IPv6) för domänen om Render säger det; Render använder IPv4.

### Steg 3: Vänta och kontrollera

- DNS kan ta 5–60 minuter (ibland längre).
- I Render → **Custom Domains** ska baskettime.app få en **grön bock** och "Certificate issued".
- Öppna **https://baskettime.app** – du ska få HTTPS och omdirigering från HTTP till HTTPS.

---

## E-post och lösenordsåterställning (SMTP)

För **Glömt lösenord** och bekräftelsemail behöver appen kunna skicka e-post via SMTP (t.ex. Loopia). Sätt följande **Environment** på Web Service:

| Variabel | Exempel / beskrivning |
|----------|------------------------|
| `MAIL_SERVER` | SMTP-värd (t.ex. från Loopia) |
| `MAIL_PORT` | `587` (TLS) eller `465` (SSL) |
| `MAIL_USE_TLS` | `true` för port 587 (standard om utelämnad) |
| `MAIL_USE_SSL` | `true` för port 465 (sätt då `MAIL_USE_TLS` till `false` om det behövs) |
| `MAIL_USERNAME` | SMTP-användarnamn |
| `MAIL_PASSWORD` | SMTP-lösenord |
| `MAIL_DEFAULT_SENDER` | Avsändaradress (t.ex. `noreply@baskettime.se`) |
| `PUBLIC_APP_URL` | Bas-URL till appen **utan** avslutande snedstreck, t.ex. `https://baskettime.app` – används i återställningslänken i mailet (`/reset-password.html?token=...`). Om den saknas byggs länken från inkommande begäran (`request.url_root`), vilket kan bli fel bakom proxy om den inte är satt. |

Utan dessa variabler kan konton fortfarande skapas och användas, men **återställningsmail skickas inte** (anropet till glömt-lösenord returnerar då fel om utskicket misslyckas).

**Bakgrund:** Nya konton måste ha e-post vid registrering. Äldre konton kan sakna e-post; de kan logga in som förut och lägga till e-post under **Inställningar** i appen för att aktivera återställning. Tekniskt sker utökning av befintliga `users`-tabeller vid appstart via `ensure_user_email_and_reset_columns` i `backend/schema_migrations.py`.

---

## Sammanfattning

| Vad | Var |
|-----|-----|
| Skapa databas | Render Dashboard → New + → PostgreSQL, samma region som appen |
| DATABASE_URL | Environment på Web Service; använd Internal URL + `?sslmode=require` för SSL |
| SECRET_KEY | Environment på Web Service |
| Tabeller (användare, lag, matcher) | Skapas automatiskt vid första start |
| E-post / reset | `MAIL_*` + `PUBLIC_APP_URL` (se avsnitt ovan) |
| baskettime.app | Custom Domains på Web Service + A/CNAME hos domänregistratorn |
| HTTPS | Render sköter certifikat; säker anslutning till **appen** (https://baskettime.app). Databasen ansluts med SSL om du använder `?sslmode=require`. |

Om något steg strular (t.ex. "Certificate pending" eller att appen inte når databasen) skriv vilket steg och eventuellt felmeddelande så kan vi felsöka.
