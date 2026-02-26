/**
 * BasketTime i18n – load locale, t(key), apply data-i18n, language switcher.
 * Depends on: none. Fires 'i18n-ready' when locale is loaded (app should init then).
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'baskettime.lang';
  var DEFAULT_LANG = 'sv';
  var SUPPORTED = ['sv', 'en', 'de'];

  var current = DEFAULT_LANG;
  var strings = {};

  /** Inbäddade fallbacks när locales/*.json inte kan laddas (t.ex. file://). */
  var FALLBACK_SV = {"app.title":"BasketTime","app.description":"BasketTime – Speltidsregistrering för basket","login.title":"Logga in","login.description":"Ange dina uppgifter för att komma åt BasketTime.","login.username":"Användarnamn","login.usernamePlaceholder":"Användarnamn","login.password":"Lösenord","login.passwordPlaceholder":"Lösenord","login.submit":"Logga in","login.register":"Skapa konto","nav.match":"Match","nav.teams":"Lag","nav.history":"Historik","nav.stats":"Statistik","nav.aria":"Huvudnavigering","view.phone":"Telefon","view.desktop":"Dator","view.ariaGroup":"Visa appen i telefon- eller datorläge","view.ariaPhone":"Telefonläge","view.ariaDesktop":"Datorläge","createMatch.title":"Ny match","createMatch.nameLabel":"Matchnamn","createMatch.namePlaceholder":"t.ex. Hemmamatch 1","createMatch.nameAria":"Matchnamn","createMatch.dateLabel":"Datum","createMatch.dateAria":"Matchdatum","createMatch.selectTeamLabel":"Välj lag","createMatch.selectTeamAria":"Välj lag","createMatch.selectTeamPlaceholder":"– Välj lag –","createMatch.start":"Börja","activeMatch.startPause":"Starta tid","activeMatch.stopPause":"Stoppa tid","activeMatch.menu":"Meny","activeMatch.editNames":"Redigera namn","activeMatch.saveMatch":"Avsluta match","activeMatch.resetMatch":"Återställ match","activeMatch.newMatch":"Ny match","activeMatch.ariaStartPause":"Starta eller stoppa tid","activeMatch.ariaMenu":"Meny","activeMatch.ariaEditNames":"Redigera spelarnamn","activeMatch.ariaSaveMatch":"Avsluta och spara match","activeMatch.ariaResetMatch":"Återställ match","activeMatch.ariaNewMatch":"Skapa ny match","activeMatch.ariaPlayerList":"Spelarlista med speltid","status.running":"Pågår","status.paused":"Pausad","teams.hint":"Skapa lag och lägg till spelare. Välj sedan lag när du startar en ny match.","teams.empty":"Inga lag ännu. Skapa ett lag nedan.","teams.addTeam":"Nytt lag","teams.edit":"Redigera","teams.delete":"Radera","teams.ariaEdit":"Redigera lag","teams.ariaDelete":"Radera lag","teams.playersCount":"{{count}} spelare","ongoing.button":"Pågående match","ongoing.aria":"Gå till pågående match","history.empty":"Inga matcher sparade ännu.","history.clearAll":"Rensa all historik","history.ariaClearAll":"Rensa hela säsongshistoriken","history.duration":"Varaktighet:","stats.empty":"Ingen statistik ännu. Spara minst en match.","stats.exportCsv":"Exportera CSV","stats.ariaExportCsv":"Exportera statistik till CSV","detail.back":"Tillbaka till historik","detail.exportCsv":"Exportera CSV","detail.deleteMatch":"Radera match","detail.ariaExportCsv":"Exportera match till CSV","detail.ariaDeleteMatch":"Radera denna match","table.name":"Namn","table.court":"Plan","table.bench":"Bänk","table.matches":"Matcher","table.playerTimesAria":"Speltid plan och bänk","table.timeCourtAria":"Tid på plan","table.timeBenchAria":"Tid på bänk","table.statsAria":"Assists, fouls, mål","player.decreaseAssists":"Minska assists","player.increaseAssists":"Öka assists","player.decreaseFouls":"Minska fouls","player.increaseFouls":"Öka fouls","player.decreaseGoals":"Minska mål","player.increaseGoals":"Öka mål","player.onCourt":"Plan","player.onBench":"Bänk","player.ariaOnCourt":"På plan","player.ariaOnBench":"På bänk","player.plays":"{{name}} spelar","player.selectHint":"Välj vilka som spelar i denna match (minst en).","modal.editNames.title":"Redigera spelarnamn","modal.editNames.close":"Stäng","modal.team.title":"Lag","modal.team.newTitle":"Nytt lag","modal.team.editTitle":"Redigera lag","modal.team.nameLabel":"Lagnamn","modal.team.nameAria":"Lagnamn","modal.team.playersLabel":"Spelare i laget","modal.team.removePlayer":"Ta bort sista spelare","modal.team.addPlayer":"Lägg till spelare","modal.team.save":"Spara lag","modal.deleteTeam.title":"Radera lag?","modal.deleteTeam.body":"Detta går inte att ångra.","modal.deleteTeam.bodyWithName":"Laget \"{{name}}\" och alla dess spelare raderas. Detta går inte att ångra.","modal.matchMenu.title":"Meny","modal.confirmClear.title":"Rensa all historik?","modal.confirmClear.body":"Alla sparade matcher och statistik raderas. Detta går inte att ångra.","settings.title":"Inställningar","settings.aria":"Öppna inställningar","settings.viewMode":"Visa","settings.language":"Språk","settings.theme":"Färgtema","settings.themeBlue":"Blå","settings.themeGreen":"Grön","settings.themeRed":"Röd","settings.themePurple":"Lila","settings.themeBlack":"Svart","settings.themeYellow":"Gul","settings.logout":"Logga ut","modal.cancel":"Avbryt","modal.clearAll":"Rensa allt","modal.delete":"Radera","default.myTeam":"Mitt lag","default.team":"Lag","default.teamN":"Lag {{n}}","default.playerN":"Spelare {{n}}","default.newTeam":"Nytt lag","default.match":"Match","default.playerNameAria":"Namn spelare {{n}}","csv.matchName":"Matchnamn","csv.matchDate":"Matchdatum","csv.team":"Lag","csv.matchDuration":"Matchlängd (mm:ss)","csv.playerName":"Spelarnamn","csv.onCourt":"Plan (mm:ss)","csv.onCourtSeconds":"Plan (sek)","csv.bench":"Bänk (mm:ss)","csv.benchSeconds":"Bänk (sek)","csv.percentPlayed":"% spelad","csv.assists":"Assists","csv.fouls":"Fouls","csv.goals":"Mål","csv.statsPlayer":"Spelare","csv.statsTeam":"Lag","csv.statsTotalCourt":"Total plan (mm:ss)","csv.statsTotalBench":"Total bänk (mm:ss)","csv.statsMatchesRecorded":"Matcher registrerade","csv.statsMatchesPlayed":"Matcher spelade","csv.statsAvgCourt":"Snitt plan/match (mm:ss)","csv.statsAvgPct":"Snitt % spelad","share.statsTitle":"BasketTime statistik","share.matchTitle":"BasketTime match"};
  var FALLBACK_EN = {"app.title":"BasketTime","app.description":"BasketTime – Basketball play time tracking","login.title":"Log in","login.description":"Enter your details to access BasketTime.","login.username":"Username","login.usernamePlaceholder":"Username","login.password":"Password","login.passwordPlaceholder":"Password","login.submit":"Log in","login.register":"Create account","nav.match":"Match","nav.teams":"Teams","nav.history":"History","nav.stats":"Statistics","nav.aria":"Main navigation","view.phone":"Phone","view.desktop":"Desktop","view.ariaGroup":"View app in phone or desktop mode","view.ariaPhone":"Phone mode","view.ariaDesktop":"Desktop mode","createMatch.title":"New match","createMatch.nameLabel":"Match name","createMatch.namePlaceholder":"e.g. Home game 1","createMatch.nameAria":"Match name","createMatch.dateLabel":"Date","createMatch.dateAria":"Match date","createMatch.selectTeamLabel":"Select team","createMatch.selectTeamAria":"Select team","createMatch.selectTeamPlaceholder":"– Select team –","createMatch.start":"Start","activeMatch.startPause":"Start time","activeMatch.stopPause":"Stop time","activeMatch.menu":"Menu","activeMatch.editNames":"Edit names","activeMatch.saveMatch":"End match","activeMatch.resetMatch":"Reset match","activeMatch.newMatch":"New match","activeMatch.ariaStartPause":"Start or stop time","activeMatch.ariaMenu":"Menu","activeMatch.ariaEditNames":"Edit player names","activeMatch.ariaSaveMatch":"End and save match","activeMatch.ariaResetMatch":"Reset match","activeMatch.ariaNewMatch":"Create new match","activeMatch.ariaPlayerList":"Player list with play time","status.running":"Running","status.paused":"Paused","teams.hint":"Create teams and add players. Then select a team when you start a new match.","teams.empty":"No teams yet. Create a team below.","teams.addTeam":"New team","teams.edit":"Edit","teams.delete":"Delete","teams.ariaEdit":"Edit team","teams.ariaDelete":"Delete team","teams.playersCount":"{{count}} players","ongoing.button":"Ongoing match","ongoing.aria":"Go to ongoing match","history.empty":"No matches saved yet.","history.clearAll":"Clear all history","history.ariaClearAll":"Clear entire season history","history.duration":"Duration:","stats.empty":"No statistics yet. Save at least one match.","stats.filterByTeam":"Filter by team","stats.filterTeamAria":"Select teams","stats.showChart":"Show chart","stats.ariaShowChart":"Show chart view of statistics","stats.exportCsv":"Export CSV","stats.ariaExportCsv":"Export statistics to CSV","stats.chartTitle":"Time on court","stats.chartBar":"Bar","stats.chartLine":"Line","stats.chartLineTitle":"Avg court time per match","detail.back":"Back to history","detail.exportCsv":"Export CSV","detail.deleteMatch":"Delete match","detail.ariaExportCsv":"Export match to CSV","detail.ariaDeleteMatch":"Delete this match","table.name":"Name","table.court":"Court","table.bench":"Bench","table.matches":"Matches","table.playerTimesAria":"Play time court and bench","table.timeCourtAria":"Time on court","table.timeBenchAria":"Time on bench","table.pointsLetter":"P","table.statsAria":"Assists, fouls, points","player.decreaseAssists":"Decrease assists","player.increaseAssists":"Increase assists","player.decreaseFouls":"Decrease fouls","player.increaseFouls":"Increase fouls","player.decreaseGoals":"Decrease points","player.increaseGoals":"Increase points","player.onCourt":"Court","player.onBench":"Bench","player.ariaOnCourt":"On court","player.ariaOnBench":"On bench","player.plays":"{{name}} plays","player.selectHint":"Select who plays in this match (at least one).","modal.editNames.title":"Edit player names","modal.editNames.close":"Close","modal.team.title":"Team","modal.team.newTitle":"New team","modal.team.editTitle":"Edit team","modal.team.nameLabel":"Team name","modal.team.nameAria":"Team name","modal.team.playersLabel":"Players in team","modal.team.removePlayer":"Remove last player","modal.team.addPlayer":"Add player","modal.team.save":"Save team","modal.deleteTeam.title":"Delete team?","modal.deleteTeam.body":"This cannot be undone.","modal.deleteTeam.bodyWithName":"The team \"{{name}}\" and all its players will be deleted. This cannot be undone.","modal.matchMenu.title":"Menu","modal.confirmClear.title":"Clear all history?","modal.confirmClear.body":"All saved matches and statistics will be deleted. This cannot be undone.","settings.title":"Settings","settings.aria":"Open settings","settings.viewMode":"View","settings.language":"Language","settings.theme":"Color theme","settings.themeBlue":"Blue","settings.themeGreen":"Green","settings.themeRed":"Red","settings.themePurple":"Purple","settings.themeBlack":"Black","settings.themeYellow":"Yellow","settings.logout":"Log out","modal.cancel":"Cancel","modal.clearAll":"Clear all","modal.delete":"Delete","default.myTeam":"My team","default.team":"Team","default.teamN":"Team {{n}}","default.playerN":"Player {{n}}","default.newTeam":"New team","default.match":"Match","default.playerNameAria":"Name player {{n}}","csv.matchName":"Match name","csv.matchDate":"Match date","csv.team":"Team","csv.matchDuration":"Match duration (mm:ss)","csv.playerName":"Player name","csv.onCourt":"On court (mm:ss)","csv.onCourtSeconds":"On court (seconds)","csv.bench":"Bench (mm:ss)","csv.benchSeconds":"Bench (seconds)","csv.percentPlayed":"% played","csv.assists":"Assists","csv.fouls":"Fouls","csv.goals":"Point","csv.statsPlayer":"Player","csv.statsTeam":"Team","csv.statsTotalCourt":"Total court (mm:ss)","csv.statsTotalBench":"Total bench (mm:ss)","csv.statsMatchesRecorded":"Matches recorded","csv.statsMatchesPlayed":"Matches played","csv.statsAvgCourt":"Avg court/match (mm:ss)","csv.statsAvgPct":"Avg % played","share.statsTitle":"BasketTime statistics","share.matchTitle":"BasketTime match"};
  var FALLBACK_DE = {"app.title":"BasketTime","app.description":"BasketTime – Spielzeiterfassung für Basketball","login.title":"Anmelden","login.description":"Gib deine Daten ein, um auf BasketTime zuzugreifen.","login.username":"Benutzername","login.usernamePlaceholder":"Benutzername","login.password":"Passwort","login.passwordPlaceholder":"Passwort","login.submit":"Anmelden","login.register":"Konto erstellen","nav.match":"Spiel","nav.teams":"Teams","nav.history":"Verlauf","nav.stats":"Statistik","nav.aria":"Hauptnavigation","view.phone":"Handy","view.desktop":"Desktop","view.ariaGroup":"App im Handy- oder Desktopmodus anzeigen","view.ariaPhone":"Handymodus","view.ariaDesktop":"Desktopmodus","createMatch.title":"Neues Spiel","createMatch.nameLabel":"Spielname","createMatch.namePlaceholder":"z. B. Heimspiel 1","createMatch.nameAria":"Spielname","createMatch.dateLabel":"Datum","createMatch.dateAria":"Spieldatum","createMatch.selectTeamLabel":"Team wählen","createMatch.selectTeamAria":"Team wählen","createMatch.selectTeamPlaceholder":"– Team wählen –","createMatch.start":"Starten","activeMatch.startPause":"Zeit starten","activeMatch.stopPause":"Zeit stoppen","activeMatch.menu":"Menü","activeMatch.editNames":"Namen bearbeiten","activeMatch.saveMatch":"Spiel beenden","activeMatch.resetMatch":"Spiel zurücksetzen","activeMatch.newMatch":"Neues Spiel","activeMatch.ariaStartPause":"Zeit starten oder stoppen","activeMatch.ariaMenu":"Menü","activeMatch.ariaEditNames":"Spielernamen bearbeiten","activeMatch.ariaSaveMatch":"Spiel beenden und speichern","activeMatch.ariaResetMatch":"Spiel zurücksetzen","activeMatch.ariaNewMatch":"Neues Spiel erstellen","activeMatch.ariaPlayerList":"Spielerliste mit Spielzeit","status.running":"Läuft","status.paused":"Pausiert","teams.hint":"Teams anlegen und Spieler hinzufügen. Wähle dann ein Team beim Start eines neuen Spiels.","teams.empty":"Noch keine Teams. Lege unten ein Team an.","teams.addTeam":"Neues Team","teams.edit":"Bearbeiten","teams.delete":"Löschen","teams.ariaEdit":"Team bearbeiten","teams.ariaDelete":"Team löschen","teams.playersCount":"{{count}} Spieler","ongoing.button":"Laufendes Spiel","ongoing.aria":"Zum laufenden Spiel","history.empty":"Noch keine Spiele gespeichert.","history.clearAll":"Gesamten Verlauf löschen","history.ariaClearAll":"Gesamte Saisonhistorie löschen","history.duration":"Dauer:","stats.empty":"Noch keine Statistik. Speichere mindestens ein Spiel.","stats.filterByTeam":"Nach Team filtern","stats.filterTeamAria":"Teams auswählen","stats.showChart":"Grafik anzeigen","stats.ariaShowChart":"Grafische Statistik anzeigen","stats.exportCsv":"CSV exportieren","stats.ariaExportCsv":"Statistik als CSV exportieren","stats.chartTitle":"Spielzeit auf dem Feld","stats.chartBar":"Stapel","stats.chartLine":"Linje","stats.chartLineTitle":"Ø Spielzeit pro Spiel","detail.back":"Zurück zum Verlauf","detail.exportCsv":"CSV exportieren","detail.deleteMatch":"Spiel löschen","detail.ariaExportCsv":"Spiel als CSV exportieren","detail.ariaDeleteMatch":"Dieses Spiel löschen","table.name":"Name","table.court":"Feld","table.bench":"Bank","table.matches":"Spiele","table.playerTimesAria":"Spielzeit Feld und Bank","table.timeCourtAria":"Zeit auf dem Feld","table.timeBenchAria":"Zeit auf der Bank","table.pointsLetter":"P","table.statsAria":"Assists, Fouls, Punkte","player.decreaseAssists":"Assists verringern","player.increaseAssists":"Assists erhöhen","player.decreaseFouls":"Fouls verringern","player.increaseFouls":"Fouls erhöhen","player.decreaseGoals":"Punkte verringern","player.increaseGoals":"Punkte erhöhen","player.onCourt":"Feld","player.onBench":"Bank","player.ariaOnCourt":"Auf dem Feld","player.ariaOnBench":"Auf der Bank","player.plays":"{{name}} spielt","player.selectHint":"Wähle, wer in diesem Spiel mitspielt (mindestens einer).","modal.editNames.title":"Spielernamen bearbeiten","modal.editNames.close":"Schließen","modal.team.title":"Team","modal.team.newTitle":"Neues Team","modal.team.editTitle":"Team bearbeiten","modal.team.nameLabel":"Teamname","modal.team.nameAria":"Teamname","modal.team.playersLabel":"Spieler im Team","modal.team.removePlayer":"Letzten Spieler entfernen","modal.team.addPlayer":"Spieler hinzufügen","modal.team.save":"Team speichern","modal.deleteTeam.title":"Team löschen?","modal.deleteTeam.body":"Das lässt sich nicht rückgängig machen.","modal.deleteTeam.bodyWithName":"Das Team \"{{name}}\" und alle seine Spieler werden gelöscht. Das lässt sich nicht rückgängig machen.","modal.matchMenu.title":"Menü","modal.confirmClear.title":"Gesamten Verlauf löschen?","modal.confirmClear.body":"Alle gespeicherten Spiele und Statistiken werden gelöscht. Das lässt sich nicht rückgängig machen.","settings.title":"Einstellungen","settings.aria":"Einstellungen öffnen","settings.viewMode":"Ansicht","settings.language":"Sprache","settings.theme":"Farbschema","settings.themeBlue":"Blau","settings.themeGreen":"Grün","settings.themeRed":"Rot","settings.themePurple":"Lila","settings.themeBlack":"Schwarz","settings.themeYellow":"Gelb","settings.logout":"Abmelden","modal.cancel":"Abbrechen","modal.clearAll":"Alles löschen","modal.delete":"Löschen","default.myTeam":"Mein Team","default.team":"Team","default.teamN":"Team {{n}}","default.playerN":"Spieler {{n}}","default.newTeam":"Neues Team","default.match":"Spiel","default.playerNameAria":"Name Spieler {{n}}","csv.matchName":"Spielname","csv.matchDate":"Spieldatum","csv.team":"Team","csv.matchDuration":"Spieldauer (mm:ss)","csv.playerName":"Spielername","csv.onCourt":"Feld (mm:ss)","csv.onCourtSeconds":"Feld (Sek.)","csv.bench":"Bank (mm:ss)","csv.benchSeconds":"Bank (Sek.)","csv.percentPlayed":"% gespielt","csv.assists":"Assists","csv.fouls":"Fouls","csv.goals":"Punkte","csv.statsPlayer":"Spieler","csv.statsTeam":"Team","csv.statsTotalCourt":"Gesamt Feld (mm:ss)","csv.statsTotalBench":"Gesamt Bank (mm:ss)","csv.statsMatchesRecorded":"Spiele erfasst","csv.statsMatchesPlayed":"Spiele gespielt","csv.statsAvgCourt":"Ø Feld/Spiel (mm:ss)","csv.statsAvgPct":"Ø % gespielt","share.statsTitle":"BasketTime Statistik","share.matchTitle":"BasketTime Spiel"};
  var FALLBACKS = { sv: FALLBACK_SV, en: FALLBACK_EN, de: FALLBACK_DE };

  function getStored() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      return SUPPORTED.indexOf(v) >= 0 ? v : DEFAULT_LANG;
    } catch (e) {
      return DEFAULT_LANG;
    }
  }

  function setStored(lang) {
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (e) {}
  }

  /**
   * Translate key. Optional second argument: { name: 'X', n: 1, count: 5 } for {{name}}, {{n}}, {{count}}.
   */
  function t(key, params) {
    var s = strings[key];
    if (s == null) return key;
    if (params && typeof params === 'object') {
      Object.keys(params).forEach(function (k) {
        s = s.replace(new RegExp('\\{\\{' + k + '\\}\\}', 'g'), String(params[k]));
      });
    }
    return s;
  }

  function setLang(lang) {
    if (SUPPORTED.indexOf(lang) < 0) return;
    current = lang;
    setStored(lang);
    loadLocale(lang).then(function () {
      apply();
      if (document.documentElement) document.documentElement.setAttribute('lang', lang);
      document.dispatchEvent(new CustomEvent('i18n-ready'));
    });
  }

  function getLang() {
    return current;
  }

  function loadLocale(lang) {
    return fetch('locales/' + lang + '.json')
      .then(function (r) {
        if (!r.ok) throw new Error('Locale failed');
        return r.json();
      })
      .then(function (data) {
        strings = data;
        return data;
      })
      .catch(function () {
        strings = FALLBACKS[lang] || FALLBACK_SV;
        return Promise.resolve(strings);
      });
  }

  /**
   * Apply translations: data-i18n (textContent), data-i18n-placeholder, data-i18n-aria-label.
   */
  function apply() {
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      if (key) el.textContent = t(key);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-placeholder');
      if (key) el.setAttribute('placeholder', t(key));
    });
    document.querySelectorAll('[data-i18n-aria-label]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-aria-label');
      if (key) el.setAttribute('aria-label', t(key));
    });
    var title = document.querySelector('title');
    if (title) title.textContent = t('app.title');
    var metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute('content', t('app.description'));
  }

  window.i18n = {
    t: t,
    setLang: setLang,
    getLang: getLang,
    getSupported: function () { return SUPPORTED.slice(); },
    ready: false
  };

  current = getStored();
  function onLocaleLoaded() {
    apply();
    if (document.documentElement) document.documentElement.setAttribute('lang', current);
    window.i18n.ready = true;
    document.dispatchEvent(new CustomEvent('i18n-ready'));
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      loadLocale(current).then(onLocaleLoaded);
    });
  } else {
    loadLocale(current).then(onLocaleLoaded);
  }
})();
