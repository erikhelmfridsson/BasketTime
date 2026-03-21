# BasketTime – checklista för version 1.0

Detta är en prioriterad lista. Du behöver inte ha allt, men ju fler punkter du har, desto tryggare känns 1.0.

---

## Måste (säkerhet & drift)

- [ ] **SECRET_KEY i produktion**  
  På Render (och annan hosting): sätt miljövariabeln `SECRET_KEY` till en lång, slumpmässig sträng. Använd aldrig `dev-secret-change-in-production` i produktion.

- [ ] **HTTPS**  
  Render ger HTTPS automatiskt. Om du hostar någon annanstans ska appen bara nås över HTTPS.

- [ ] **Databas i produktion**  
  På Render: använd deras PostgreSQL och sätt `DATABASE_URL`. Lokal SQLite är bra för utveckling, inte för delad produktion.

---

## Bör (användarupplevelse)

- [ ] **Tydligt fel vid nätverksproblem**  
  Om inloggning eller API-anrop misslyckas: visa ett kort, begripligt meddelande (t.ex. "Kunde inte nå servern. Kontrollera nätverk och försök igen.") istället för att bara inte hända nåt.

- [ ] **Laddningsindikator vid inloggning**  
  T.ex. "Loggar in..." eller en enkel spinner medan `/api/auth/login` körs, så användaren ser att något händer.

- [ ] **Versionsnummer någonstans**  
  T.ex. "BasketTime 1.0" i sidfot eller under Inställningar, så användare och du vet vilken version som körs.

- [ ] **README uppdaterad**  
  Kort beskrivning av appen, hur man kör lokalt, och (om du vill) länk till den livestatna adressen.

---

## Kan vänta till 1.1

- **Lösenordsåterställning** – finns nu via e-post (SMTP + `PUBLIC_APP_URL` på servern). **Valfritt för 1.0:** om du inte konfigurerar mail kan du fortfarande släppa; användare utan konfigurerad SMTP får ingen “Glömt lösenord”-funktion.
- **Starkare lösenordskrav** – t.ex. minst 8 tecken eller krav på siffra/tecken; bra men inte kritiskt för 1.0.
- **Integritetspolicy / cookie-info** – viktigt vid större eller kommersiell användning; för intern/sluten användning kan det vänta.
- **Automatiska tester** – önskvärt långsiktigt; 1.0 kan lanseras efter manuell testning om du är nöjd med flödena.

---

## Sammanfattning för en "OK" 1.0

**Minimum för att kalla det 1.0:**

1. Appen deployad på Render (eller motsvarande) med HTTPS.
2. `SECRET_KEY` och `DATABASE_URL` satta i produktion.
3. Du har testat: skapa konto, logga in, skapa lag, spela en match, spara, historik, statistik, CSV-export.
4. Korta, tydliga felmeddelanden vid nätverksfel (minst vid inloggning).
5. Versionsnummer (t.ex. 1.0) synligt i appen.

Resten av listan ovan gör 1.0 stabilare och mer polerad men är inte strikt nödvändigt för att släppa en första version.
