# BasketTime – att göra

Prioriterad lista för drift och vidareutveckling. Bocka av när något är klart.

---

## Drift & produktion (Render)

- [ ] **`SECRET_KEY`** satt i Render (aldrig standardvärdet från utveckling).
- [ ] **`DATABASE_URL`** kopplad till PostgreSQL (Internal URL, gärna med `sslmode=require`).
- [ ] **`PUBLIC_APP_URL`** satt till publik HTTPS-adress utan avslutande `/` (t.ex. `https://baskettime.app`) så lösenordsåterställningslänkar i e-post blir rätt.
- [ ] **SMTP för “Glömt lösenord”:** `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` (+ `MAIL_USE_TLS` / `MAIL_USE_SSL` enligt leverantör). Testa ett utskick efter deploy.
- [ ] **Egen domän:** Custom Domain i Render + DNS hos registrar enligt [RENDER-DATABAS-OCH-DOMAN.md](./RENDER-DATABAS-OCH-DOMAN.md).
- [ ] Efter större frontendändring: **öka `CACHE_NAME` i `sw.js`** så PWA-cache uppdateras (se [DEPLOY.md](./DEPLOY.md)).

---

## Test efter deploy (röktest)

- [ ] Skapa konto med **användarnamn + e-post + lösenord**; logga in.
- [ ] Logga in med **e-post** som användarnamn (samma konto).
- [ ] Befintligt konto utan e-post (om sådana finns): logga in med användarnamn; lägg till e-post under **Inställningar**.
- [ ] **Glömt lösenord** (om SMTP är konfigurerat): få mail, öppna länk, sätt nytt lösenord.
- [ ] Lag → match → historik → statistik → CSV-export.

---

## Kod / kvalitet (valfritt)

- [ ] Automatiska tester (API eller E2E) – låg prioritet enligt versionschecklista.
- [ ] Integritetspolicy / cookieinformation om målgruppen kräver det.
- [ ] Starkare lösenordsregler (längd/tecken) om önskat.

---

## Dokumentation

- [ ] Uppdatera **live-URL** i [README.md](./README.md) när adressen är spikad.
- [ ] Vid ny huvudversion: synka versionssträng i appen (`locales` / inställningar) och ev. [VERSION-1.0-CHECKLIST.md](./VERSION-1.0-CHECKLIST.md) eller ersätt med ny checklista.

---

*Senast sammanställd för dokumentationsgenomgång. Lägg gärna till egna rader längst upp under “Egna anteckningar” om du vill.*

### Egna anteckningar

_(tom rad för anteckningar)_
