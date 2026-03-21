# Flytta BasketTime från Render till Loopia

## Viktigt: Vanligt webbhotell räcker inte

BasketTime är en **Flask-app** som körs med **Gunicorn**. Loopia **vanliga webbhotell** (delad hosting) stöder bara PHP och enkla Python-CGI-skript – inte Flask/WSGI.

Du har därför två realistiska alternativ:

---

## Alternativ 1: Loopia VPS (rekommenderat om du vill vara hos Loopia)

Med **Loopia VPS** får du en egen Linux-server (Ubuntu/Debian) där du kan installera Python, Gunicorn, Nginx och din databas. Då kan du flytta hela appen dit.

### Steg 1: Beställ Loopia VPS

- Gå till loopia.se → VPS.
- Välj storlek (för BasketTime räcker oftast minsta variant).
- Välj Ubuntu eller Debian.
- Sätt upp SSH-nyckel eller lösenord för inloggning.

### Steg 2: Anslut och förbered servern

```bash
ssh root@din-vps-ip
```

Uppdatera och installera det som behövs:

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip nginx libpq-dev
```

### Steg 3: Skapa databas (på Loopia)

- I Loopia Kundzon: skapa en **MariaDB/MySQL-databas** (eller använd den du redan skapat).
- Skapa databasanvändare och notera: **servernamn** (t.ex. mysql123.loopia.se), **databasnamn**, **användare**, **lösenord**.
- Anslutningssträng: `mysql+pymysql://anv:lösenord@mysqlXXX.loopia.se/databasnamn`

(Om VPS:en är hos Loopia kan databasen ofta nås från samma nätverk.)

### Steg 4: Ladda upp appen till VPS

Till exempel med **git** (om du har repo på GitHub):

```bash
apt install -y git
cd /var/www
git clone https://github.com/erikhelmfridsson/BasketTime.git
cd BasketTime
```

Eller ladda upp filer med **FTP/SFTP** till t.ex. `/var/www/BasketTime`.

### Steg 5: Python-miljö och Gunicorn

```bash
cd /var/www/BasketTime
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Skapa en miljöfil med hemligheter:

```bash
nano .env
```

Innehåll (anpassa värdena):

```
SECRET_KEY=din-långa-hemliga-nyckel
DATABASE_URL=mysql+pymysql://anv:lösenord@mysqlXXX.loopia.se/databasnamn
PUBLIC_APP_URL=https://dindomän.se
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_DEFAULT_SENDER=noreply@dindomän.se
```

`PUBLIC_APP_URL` och `MAIL_*` behövs om du vill att **Glömt lösenord** ska skicka e-post (samma som på Render – se [RENDER-DATABAS-OCH-DOMAN.md](./RENDER-DATABAS-OCH-DOMAN.md)). Om du utelämnar dem fungerar appen i övrigt, men inte utskick av återställningslänk.

Ladda `.env` i appen (lägg till `python-dotenv` i requirements och i början av `app.py`: `from dotenv import load_dotenv; load_dotenv()`), eller exportera variablerna i systemd (se nedan).

### Steg 6: Systemd-tjänst (så att Gunicorn körs vid start)

Skapa filen `/etc/systemd/system/baskettime.service`:

```ini
[Unit]
Description=BasketTime Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/BasketTime
Environment="PATH=/var/www/BasketTime/venv/bin"
EnvironmentFile=/var/www/BasketTime/.env
ExecStart=/var/www/BasketTime/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:10000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Starta tjänsten:

```bash
systemctl daemon-reload
systemctl enable baskettime
systemctl start baskettime
systemctl status baskettime
```

### Steg 7: Nginx som reverse proxy

Skapa t.ex. `/etc/nginx/sites-available/baskettime`:

```nginx
server {
    listen 80;
    server_name dindomän.se www.dindomän.se;
    location / {
        proxy_pass http://127.0.0.1:10000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Aktivera och starta om Nginx:

```bash
ln -s /etc/nginx/sites-available/baskettime /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### Steg 8: HTTPS med Let's Encrypt (rekommenderat)

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d dindomän.se -d www.dindomän.se
```

### Steg 9: Domänen på Loopia

- I Loopia Kundzon: DNS för domänen.
- Skapa en **A-post** som pekar på din VPS:s **IP-adress** (för både `@` och `www` om du vill).

---

## Alternativ 2: Behåll Render och använd Loopia bara till domän

- **Appen** fortsätter köra på Render (gratis eller betald plan).
- **Domän:** Köp/hava domän hos Loopia och peka den till Render:
  - I Loopia: DNS → CNAME för `www` till `din-app.onrender.com`, eller A-post till Render:s IP om de anger en.
- **Databas:** Fortsätt använda Render PostgreSQL (eller annan molndatabas).

Då behöver du inte flytta appen – bara konfigurera domänen.

---

## Sammanfattning

| Vad du vill           | Rekommendation |
|-----------------------|----------------|
| Allt hos Loopia        | Loopia **VPS** + steg ovan (databas på Loopia MySQL, app på VPS). |
| Bara domän hos Loopia | Behåll app + databas på **Render**, peka domänen (CNAME/A) till Render. |
| Billigast enkelt      | Render free tier + Loopia domän som pekar dit. |

Om du vill kan vi gå igenom ett steg i taget (t.ex. bara systemd + Nginx eller bara DNS).