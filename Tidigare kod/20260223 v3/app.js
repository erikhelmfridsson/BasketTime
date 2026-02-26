/**
 * BasketTime – state, timer engine, views, storage, export.
 * Single timer using Date-based delta. Pauses on visibility hidden.
 */

(function () {
  'use strict';

  // ---------- Constants ----------
  var STORAGE_KEYS = {
    players: 'baskettime.players.v1',
    teams: 'baskettime.teams.v1',
    matches: 'baskettime.matches.v1',
    viewMode: 'baskettime.viewMode.v1'
  };
  var TICK_MS = 250;
  var DEFAULT_PLAYER_COUNT = 11;

  // ---------- State ----------
  var state = {
    teams: [],
    players: [],
    currentMatchName: '',
    currentMatchDateISO: '',
    currentTeamId: '',
    currentTeamName: '',
    matchRunning: false,
    matchStartTime: null,
    matchElapsedMs: 0,
    playerCourtSeconds: [],
    playerOnCourtSince: [],
    playerInMatch: [],
    playerAssists: [],
    playerFouls: [],
    playerGoals: [],
    selectionLocked: false
  };

  function numPlayers() {
    return state.players.length;
  }

  function getPlayerId(index) {
    return state.players[index] ? state.players[index].id : 'p' + (index + 1);
  }

  function hasCurrentMatch() {
    return state.currentMatchName.trim() !== '' && state.currentTeamId !== '';
  }

  function ensureState() {
    var n = numPlayers();
    while (state.playerCourtSeconds.length < n) state.playerCourtSeconds.push(0);
    while (state.playerOnCourtSince.length < n) state.playerOnCourtSince.push(null);
    while (state.playerInMatch.length < n) state.playerInMatch.push(true);
    while (state.playerAssists.length < n) state.playerAssists.push(0);
    while (state.playerFouls.length < n) state.playerFouls.push(0);
    while (state.playerGoals.length < n) state.playerGoals.push(0);
    state.playerCourtSeconds.length = n;
    state.playerOnCourtSince.length = n;
    state.playerInMatch.length = n;
    state.playerAssists.length = n;
    state.playerFouls.length = n;
    state.playerGoals.length = n;
  }

  function getPlayerAssists(index) { ensureState(); return Math.max(0, state.playerAssists[index] || 0); }
  function getPlayerFouls(index) { ensureState(); return Math.max(0, state.playerFouls[index] || 0); }
  function getPlayerGoals(index) { ensureState(); return Math.max(0, state.playerGoals[index] || 0); }

  function addPlayerStat(index, stat, delta) {
    ensureState();
    var key = stat === 'assists' ? 'playerAssists' : stat === 'fouls' ? 'playerFouls' : 'playerGoals';
    if (!state[key]) return;
    var val = (state[key][index] || 0) + delta;
    state[key][index] = Math.max(0, val);
    updatePlayerRow(index);
  }

  function isPlayerInMatch(index) {
    ensureState();
    return state.playerInMatch[index] !== false;
  }

  function setPlayerInMatch(index, inMatch) {
    ensureState();
    if (state.selectionLocked) return;
    state.playerInMatch[index] = inMatch;
  }

  function countPlayersInMatch() {
    ensureState();
    var n = 0;
    for (var i = 0; i < numPlayers(); i++) if (state.playerInMatch[i]) n++;
    return n;
  }

  // ---------- Timer engine (Date-based delta, single source of truth) ----------
  var timerInterval = null;

  function getMatchElapsedMs() {
    if (!state.matchRunning || state.matchStartTime === null) return state.matchElapsedMs;
    return state.matchElapsedMs + (Date.now() - state.matchStartTime);
  }

  function getMatchSeconds() {
    return Math.floor(getMatchElapsedMs() / 1000);
  }

  function getCourtSecondsForPlayer(index) {
    ensureState();
    var base = state.playerCourtSeconds[index] || 0;
    var since = state.playerOnCourtSince[index];
    if (!state.matchRunning || since === null) return base;
    var extra = Math.floor((Date.now() - since) / 1000);
    return base + extra;
  }

  function getBenchSecondsForPlayer(index) {
    var matchSec = getMatchSeconds();
    var courtSec = getCourtSecondsForPlayer(index);
    return Math.max(0, matchSec - courtSec);
  }

  function tick() {
    if (!state.matchRunning) return;
    updateMasterClockDisplay();
    updateAllPlayerRows();
  }

  function startTimerTicker() {
    stopTimerTicker();
    timerInterval = setInterval(tick, TICK_MS);
  }

  function stopTimerTicker() {
    if (timerInterval != null) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  function startMatch() {
    ensureState();
    if (countPlayersInMatch() === 0) return;
    state.selectionLocked = true;
    state.matchRunning = true;
    state.matchStartTime = Date.now();
    startTimerTicker();
    setMatchStatusDisplay(true);
    setStartPauseButtonLabel(false);
    renderPlayerList();
  }

  function pauseMatch() {
    stopTimerTicker();
    if (state.matchRunning) {
      state.matchElapsedMs = getMatchElapsedMs();
      state.matchRunning = false;
      state.matchStartTime = null;
      for (var i = 0; i < numPlayers(); i++) {
        if (state.playerOnCourtSince[i] !== null) {
          var added = Math.floor((Date.now() - state.playerOnCourtSince[i]) / 1000);
          state.playerCourtSeconds[i] = (state.playerCourtSeconds[i] || 0) + added;
          state.playerOnCourtSince[i] = null;
        }
      }
    }
    setMatchStatusDisplay(false);
    setStartPauseButtonLabel(true);
    updateMasterClockDisplay();
    updateAllPlayerRows();
  }

  function resetMatch() {
    pauseMatch();
    state.selectionLocked = false;
    state.matchElapsedMs = 0;
    var n = numPlayers();
    state.playerCourtSeconds = [];
    state.playerOnCourtSince = [];
    state.playerInMatch = [];
    state.playerAssists = [];
    state.playerFouls = [];
    state.playerGoals = [];
    for (var i = 0; i < n; i++) {
      state.playerCourtSeconds.push(0);
      state.playerOnCourtSince.push(null);
      state.playerInMatch.push(true);
      state.playerAssists.push(0);
      state.playerFouls.push(0);
      state.playerGoals.push(0);
    }
    renderMatchPanel();
    updateOngoingMatchButton();
    tick();
  }

  function startNewMatch() {
    pauseMatch();
    state.selectionLocked = false;
    state.currentMatchName = '';
    state.currentMatchDateISO = '';
    state.currentTeamId = '';
    state.currentTeamName = '';
    state.matchElapsedMs = 0;
    state.players = [];
    state.playerCourtSeconds = [];
    state.playerOnCourtSince = [];
    state.playerInMatch = [];
    state.playerAssists = [];
    state.playerFouls = [];
    state.playerGoals = [];
    renderMatchPanel();
    updateOngoingMatchButton();
  }

  function setPlayerOnCourt(index, onCourt) {
    ensureState();
    var since = state.playerOnCourtSince[index];
    if (state.matchRunning && since !== null) {
      var added = Math.floor((Date.now() - since) / 1000);
      state.playerCourtSeconds[index] = (state.playerCourtSeconds[index] || 0) + added;
    }
    state.playerOnCourtSince[index] = onCourt && state.matchRunning ? Date.now() : null;
    updatePlayerRow(index);
  }

  // ---------- Visibility: pause when backgrounded ----------
  function onVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      pauseMatch();
    }
  }

  document.addEventListener('visibilitychange', onVisibilityChange);

  // ---------- Storage (teams) ----------
  function loadTeams() {
    try {
      var raw = localStorage.getItem(STORAGE_KEYS.teams);
      if (raw) {
        var data = JSON.parse(raw);
        if (Array.isArray(data) && data.length > 0) return normalizeTeams(data);
      }
      var oldPlayers = loadLegacyPlayers();
      if (oldPlayers.length > 0) {
        var team = { id: 't' + Date.now(), name: 'Mitt lag', players: oldPlayers };
        var list = [team];
        saveTeams(list);
        return list;
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  function normalizeTeams(data) {
    return data.map(function (t, ti) {
      if (!t || typeof t !== 'object') return { id: 't' + ti, name: 'Lag ' + (ti + 1), players: [] };
      var players = Array.isArray(t.players) ? t.players : [];
      players = players.map(function (p, pi) {
        if (!p || typeof p !== 'object') return { id: 'p' + pi, name: 'Spelare ' + (pi + 1) };
        return { id: String(p.id || 'p' + pi), name: typeof p.name === 'string' && p.name.trim() ? p.name.trim() : 'Spelare ' + (pi + 1) };
      });
      return { id: String(t.id || 't' + ti), name: typeof t.name === 'string' && t.name.trim() ? t.name.trim() : 'Lag ' + (ti + 1), players: players };
    });
  }

  function loadLegacyPlayers() {
    try {
      var raw = localStorage.getItem(STORAGE_KEYS.players);
      if (!raw) return [];
      var data = JSON.parse(raw);
      if (!Array.isArray(data)) return [];
      return data.slice(0, 15).map(function (p, i) {
        return { id: (p && p.id) ? String(p.id) : 'p' + (i + 1), name: (p && typeof p.name === 'string' && p.name.trim()) ? p.name.trim() : 'Spelare ' + (i + 1) };
      });
    } catch (e) { return []; }
  }

  function saveTeams(teams) {
    try {
      localStorage.setItem(STORAGE_KEYS.teams, JSON.stringify(teams || state.teams));
    } catch (e) {}
  }

  function getTeamById(id) {
    for (var i = 0; i < state.teams.length; i++) if (state.teams[i].id === id) return state.teams[i];
    return null;
  }

  function addTeam(name, players) {
    var team = { id: 't' + Date.now(), name: name || 'Nytt lag', players: players || defaultTeamPlayers() };
    state.teams.push(team);
    saveTeams(state.teams);
    return team;
  }

  function defaultTeamPlayers() {
    var out = [];
    for (var i = 0; i < DEFAULT_PLAYER_COUNT; i++) out.push({ id: 'p' + (i + 1), name: 'Spelare ' + (i + 1) });
    return out;
  }

  function updateTeam(id, name, players) {
    var t = getTeamById(id);
    if (!t) return;
    if (name !== undefined) t.name = name;
    if (players !== undefined) t.players = players;
    saveTeams(state.teams);
  }

  function deleteTeam(id) {
    state.teams = state.teams.filter(function (t) { return t.id !== id; });
    saveTeams(state.teams);
  }

  function loadMatches() {
    try {
      var raw = localStorage.getItem(STORAGE_KEYS.matches);
      if (!raw) return [];
      var data = JSON.parse(raw);
      if (!Array.isArray(data)) return [];
      return data;
    } catch (e) {
      return [];
    }
  }

  function saveMatches(matches) {
    try {
      localStorage.setItem(STORAGE_KEYS.matches, JSON.stringify(matches));
    } catch (e) {}
  }

  function getMatchId(name, dateISO) {
    var datePart = '';
    if (dateISO) {
      var d = new Date(dateISO);
      datePart = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    } else {
      datePart = new Date().toISOString().slice(0, 10);
    }
    var n = (name && typeof name === 'string') ? name.trim() : '';
    var slug = n.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_\-]/g, '').slice(0, 50);
    if (!slug) slug = 'match';
    return datePart + '_' + slug;
  }

  function matchIdFromStored(m) {
    if (!m || !m.dateISO) return '';
    var d = new Date(m.dateISO);
    var datePart = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    var n = (m.name && typeof m.name === 'string') ? m.name.trim() : '';
    var slug = n.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_\-]/g, '').slice(0, 50);
    if (!slug) slug = 'match';
    return datePart + '_' + slug;
  }

  function saveOrUpdateMatch(match) {
    match.id = getMatchId(match.name, match.dateISO);
    var list = loadMatches();
    var idx = -1;
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === match.id) { idx = i; break; }
      if (matchIdFromStored(list[i]) === match.id) { idx = i; break; }
    }
    if (idx >= 0) list.splice(idx, 1);
    list.unshift(match);
    saveMatches(list);
  }

  function deleteMatchById(id) {
    var list = loadMatches().filter(function (m) { return m.id !== id; });
    saveMatches(list);
  }

  function clearAllMatches() {
    saveMatches([]);
  }

  // ---------- Views ----------
  var masterClockEl = document.getElementById('master-clock');
  var matchStatusEl = document.getElementById('match-status');
  var startPauseBtn = document.getElementById('btn-start-pause');
  var playerListEl = document.getElementById('player-list');

  function formatMmSs(seconds) {
    var m = Math.floor(seconds / 60);
    var s = Math.floor(seconds % 60);
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  function updateMasterClockDisplay() {
    if (masterClockEl) masterClockEl.textContent = formatMmSs(getMatchSeconds());
  }

  function setMatchStatusDisplay(running) {
    if (matchStatusEl) matchStatusEl.textContent = running ? 'Pågår' : 'Pausad';
    if (matchStatusEl) matchStatusEl.classList.toggle('running', running);
  }

  function setStartPauseButtonLabel(isPaused) {
    if (startPauseBtn) startPauseBtn.textContent = isPaused ? 'Starta tid' : 'Stoppa tid';
  }

  function updateOngoingMatchButton() {
    var btn = document.getElementById('btn-ongoing-match');
    if (btn) btn.hidden = !hasCurrentMatch();
  }

  function updateStartButtonState() {
    if (!startPauseBtn) return;
    var disabled = !state.selectionLocked && countPlayersInMatch() === 0;
    startPauseBtn.disabled = disabled;
    startPauseBtn.setAttribute('aria-disabled', disabled);
  }

  function updatePlayerRow(index) {
    var row = document.getElementById('player-row-' + index);
    if (!row) return;
    var courtSec = getCourtSecondsForPlayer(index);
    var benchSec = getBenchSecondsForPlayer(index);
    var courtEl = row.querySelector('.player-time-court');
    var benchEl = row.querySelector('.player-time-bench');
    var toggleEl = row.querySelector('.player-toggle');
    if (courtEl) courtEl.textContent = formatMmSs(courtSec);
    if (benchEl) benchEl.textContent = formatMmSs(benchSec);
    var onCourt = state.playerOnCourtSince[index] !== null;
    if (toggleEl) {
      toggleEl.textContent = onCourt ? 'Plan' : 'Bänk';
      toggleEl.classList.toggle('on-court', onCourt);
      toggleEl.classList.toggle('on-bench', !onCourt);
    }
    var a = getPlayerAssists(index);
    var f = getPlayerFouls(index);
    var g = getPlayerGoals(index);
    var aVal = row.querySelector('.player-stat-assists-value');
    var fVal = row.querySelector('.player-stat-fouls-value');
    var gVal = row.querySelector('.player-stat-goals-value');
    if (aVal) aVal.textContent = a;
    if (fVal) fVal.textContent = f;
    if (gVal) gVal.textContent = g;
    var aMinus = row.querySelector('.player-stat-assists-minus');
    var fMinus = row.querySelector('.player-stat-fouls-minus');
    var gMinus = row.querySelector('.player-stat-goals-minus');
    if (aMinus) aMinus.disabled = a <= 0;
    if (fMinus) fMinus.disabled = f <= 0;
    if (gMinus) gMinus.disabled = g <= 0;
  }

  function updateAllPlayerRows() {
    for (var i = 0; i < numPlayers(); i++) {
      if (state.selectionLocked && !state.playerInMatch[i]) continue;
      updatePlayerRow(i);
    }
  }

  function renderMatchPanel() {
    var createWrap = document.getElementById('create-match-wrap');
    var activeWrap = document.getElementById('active-match-wrap');
    var activeInfo = document.getElementById('active-match-info');
    if (!createWrap || !activeWrap) return;
    if (!hasCurrentMatch()) {
      createWrap.hidden = false;
      activeWrap.hidden = true;
      document.body.classList.remove('match-view-open');
      populateCreateMatchForm();
      updateOngoingMatchButton();
      return;
    }
    createWrap.hidden = true;
    activeWrap.hidden = false;
    document.body.classList.add('match-view-open');
    var dateStr = state.currentMatchDateISO ? new Date(state.currentMatchDateISO).toLocaleDateString('sv-SE') : '';
    if (activeInfo) activeInfo.textContent = state.currentMatchName + (dateStr ? ' · ' + dateStr : '') + (state.currentTeamName ? ' · ' + state.currentTeamName : '');
    renderPlayerList();
    updateStartButtonState();
    updateOngoingMatchButton();
  }

  function populateCreateMatchForm() {
    var nameEl = document.getElementById('input-match-name');
    var dateEl = document.getElementById('input-match-date');
    var selectEl = document.getElementById('select-team');
    if (dateEl && !dateEl.value) {
      var today = new Date();
      dateEl.value = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
    }
    if (selectEl) {
      selectEl.innerHTML = '<option value="">– Välj lag –</option>';
      state.teams.forEach(function (t) {
        var opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.name;
        selectEl.appendChild(opt);
      });
    }
  }

  function startMatchFromForm() {
    var nameEl = document.getElementById('input-match-name');
    var dateEl = document.getElementById('input-match-date');
    var selectEl = document.getElementById('select-team');
    var name = nameEl ? nameEl.value.trim() : '';
    var teamId = selectEl ? selectEl.value : '';
    if (!name || !teamId) return;
    var team = getTeamById(teamId);
    if (!team || !team.players.length) return;
    var dateISO = dateEl && dateEl.value ? new Date(dateEl.value + 'T12:00:00').toISOString() : new Date().toISOString();
    state.currentMatchName = name;
    state.currentMatchDateISO = dateISO;
    state.currentTeamId = team.id;
    state.currentTeamName = team.name;
    state.players = team.players.map(function (p) { return { id: p.id, name: p.name }; });
    ensureState();
    renderMatchPanel();
  }

  function renderPlayerList() {
    if (!playerListEl) return;
    ensureState();
    playerListEl.innerHTML = '';

    if (!state.selectionLocked) {
      var hint = document.createElement('p');
      hint.className = 'player-select-hint';
      hint.setAttribute('aria-live', 'polite');
      hint.textContent = 'Välj vilka som spelar i denna match (minst en).';
      playerListEl.appendChild(hint);
      for (var i = 0; i < numPlayers(); i++) {
        var p = state.players[i] || { name: 'Player ' + (i + 1) };
        var inMatch = state.playerInMatch[i] !== false;
        var li = document.createElement('li');
        li.className = 'player-row player-row-select';
        li.id = 'player-row-' + i;
        li.setAttribute('role', 'listitem');
        li.innerHTML =
          '<label class="player-select-label">' +
            '<input type="checkbox" class="player-select-checkbox" data-player-index="' + i + '" ' + (inMatch ? 'checked' : '') + ' aria-label="' + escapeHtml(p.name) + ' spelar">' +
            '<span class="player-name">' + escapeHtml(p.name) + '</span>' +
          '</label>';
        playerListEl.appendChild(li);
      }
      playerListEl.querySelectorAll('.player-select-checkbox').forEach(function (cb) {
        cb.addEventListener('change', function () {
          var idx = parseInt(cb.getAttribute('data-player-index'), 10);
          if (!isNaN(idx)) setPlayerInMatch(idx, cb.checked);
          updateStartButtonState();
        });
      });
      updateStartButtonState();
      return;
    }

    for (var i = 0; i < numPlayers(); i++) {
      if (!state.playerInMatch[i]) continue;
      var p = state.players[i] || { name: 'Player ' + (i + 1) };
      var courtSec = getCourtSecondsForPlayer(i);
      var benchSec = getBenchSecondsForPlayer(i);
      var onCourt = state.playerOnCourtSince[i] !== null;
      var a = getPlayerAssists(i);
      var f = getPlayerFouls(i);
      var g = getPlayerGoals(i);
      var li = document.createElement('li');
      li.className = 'player-row';
      li.id = 'player-row-' + i;
      li.setAttribute('role', 'listitem');
      li.innerHTML =
        '<span class="player-name" id="player-name-' + i + '">' + escapeHtml(p.name) + '</span>' +
        '<div class="player-times" aria-label="Speltid plan och bänk">' +
          '<span class="player-time-court" aria-label="Tid på plan">' + formatMmSs(courtSec) + '</span>' +
          '<span class="player-time-bench" aria-label="Tid på bänk">' + formatMmSs(benchSec) + '</span>' +
        '</div>' +
        '<div class="player-stats" aria-label="Assists, fouls, mål">' +
          '<div class="player-stat"><span class="player-stat-label" aria-hidden="true">A</span><span class="player-stat-assists-value">' + a + '</span><button type="button" class="player-stat-btn player-stat-assists-minus btn-touch" data-player-index="' + i + '" data-stat="assists" data-delta="-1" aria-label="Minska assists">−</button><button type="button" class="player-stat-btn player-stat-assists-plus btn-touch" data-player-index="' + i + '" data-stat="assists" data-delta="1" aria-label="Öka assists">+</button></div>' +
          '<div class="player-stat"><span class="player-stat-label" aria-hidden="true">F</span><span class="player-stat-fouls-value">' + f + '</span><button type="button" class="player-stat-btn player-stat-fouls-minus btn-touch" data-player-index="' + i + '" data-stat="fouls" data-delta="-1" aria-label="Minska fouls">−</button><button type="button" class="player-stat-btn player-stat-fouls-plus btn-touch" data-player-index="' + i + '" data-stat="fouls" data-delta="1" aria-label="Öka fouls">+</button></div>' +
          '<div class="player-stat"><span class="player-stat-label" aria-hidden="true">M</span><span class="player-stat-goals-value">' + g + '</span><button type="button" class="player-stat-btn player-stat-goals-minus btn-touch" data-player-index="' + i + '" data-stat="goals" data-delta="-1" aria-label="Minska mål">−</button><button type="button" class="player-stat-btn player-stat-goals-plus btn-touch" data-player-index="' + i + '" data-stat="goals" data-delta="1" aria-label="Öka mål">+</button></div>' +
        '</div>' +
        '<button type="button" class="player-toggle ' + (onCourt ? 'on-court' : 'on-bench') + ' btn-touch" data-player-index="' + i + '" aria-pressed="' + onCourt + '" aria-label="' + (onCourt ? 'På plan' : 'På bänk') + '">' + (onCourt ? 'Plan' : 'Bänk') + '</button>';
      playerListEl.appendChild(li);
    }
    playerListEl.querySelectorAll('.player-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var idx = parseInt(btn.getAttribute('data-player-index'), 10);
        if (isNaN(idx)) return;
        setPlayerOnCourt(idx, state.playerOnCourtSince[idx] === null);
      });
    });
    playerListEl.querySelectorAll('.player-stat-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var idx = parseInt(btn.getAttribute('data-player-index'), 10);
        var stat = btn.getAttribute('data-stat');
        var delta = parseInt(btn.getAttribute('data-delta'), 10);
        if (!isNaN(idx) && stat && !isNaN(delta)) addPlayerStat(idx, stat, delta);
      });
    });
  }

  function escapeHtml(s) {
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function showPanel(panelId) {
    if (panelId !== 'panel-match') document.body.classList.remove('match-view-open');
    document.querySelectorAll('.tab-panel').forEach(function (p) {
      p.classList.remove('active');
      p.hidden = true;
    });
    var panel = document.getElementById(panelId);
    if (panel) {
      panel.classList.add('active');
      panel.hidden = false;
    }
    document.querySelectorAll('.tab-btn').forEach(function (b) {
      var t = b.getAttribute('data-tab');
      var active = (t === 'match' && panelId === 'panel-match') || (t === 'teams' && panelId === 'panel-teams') || (t === 'history' && panelId === 'panel-history') || (t === 'stats' && panelId === 'panel-stats');
      b.classList.toggle('active', active);
      b.setAttribute('aria-selected', active);
    });
    updateOngoingMatchButton();
    if (panelId === 'panel-match') renderMatchPanel();
    if (panelId === 'panel-teams') renderTeamsList();
  }

  function showMatchDetail(match) {
    var panel = document.getElementById('panel-match-detail');
    var list = document.getElementById('detail-table-wrap');
    var titleEl = document.getElementById('detail-title');
    if (!panel || !list || !titleEl) return;

    var nameStr = match.name && match.name.trim() ? match.name : 'Match';
    var dateStr = match.dateISO ? new Date(match.dateISO).toLocaleDateString('sv-SE') : '';
    var teamStr = match.teamNameAtTime && match.teamNameAtTime.trim() ? match.teamNameAtTime : '';
    var durationStr = formatMmSs(match.matchSeconds || 0);
    titleEl.textContent = nameStr + (dateStr ? ' · ' + dateStr : '') + (teamStr ? ' · ' + teamStr : '') + ' · ' + durationStr;
    panel.dataset.matchId = match.id;

    var matchSec = match.matchSeconds || 0;
    var html = '<table class="detail-table" role="table"><thead><tr><th>Namn</th><th>Plan</th><th>Bänk</th><th>%</th><th>A</th><th>F</th><th>M</th></tr></thead><tbody>';
    (match.players || []).forEach(function (entry) {
      var court = entry.secondsOnCourt || 0;
      var bench = Math.max(0, matchSec - court);
      var pct = matchSec > 0 ? (100 * court / matchSec).toFixed(1) : '0.0';
      var assists = entry.assists != null ? entry.assists : 0;
      var fouls = entry.fouls != null ? entry.fouls : 0;
      var goals = entry.goals != null ? entry.goals : 0;
      html += '<tr><td>' + escapeHtml(entry.playerNameAtTime || '') + '</td><td>' + formatMmSs(court) + '</td><td>' + formatMmSs(bench) + '</td><td>' + pct + '%</td><td>' + assists + '</td><td>' + fouls + '</td><td>' + goals + '</td></tr>';
    });
    html += '</tbody></table>';
    list.innerHTML = html;

    document.querySelectorAll('.tab-panel').forEach(function (p) {
      p.classList.remove('active');
      p.hidden = true;
    });
    panel.classList.add('active');
    panel.hidden = false;
    updateOngoingMatchButton();
  }

  function renderHistoryList() {
    var container = document.getElementById('history-list');
    var empty = document.getElementById('history-empty');
    if (!container) return;
    var matches = loadMatches();
    if (matches.length === 0) {
      container.innerHTML = '';
      container.hidden = true;
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;
    container.hidden = false;
    container.innerHTML = '';
    matches.forEach(function (m) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'history-item';
      btn.setAttribute('data-match-id', m.id);
      var nameStr = m.name && m.name.trim() ? m.name : 'Match';
      var dateStr = m.dateISO ? new Date(m.dateISO).toLocaleDateString('sv-SE') : '';
      var teamStr = m.teamNameAtTime && m.teamNameAtTime.trim() ? m.teamNameAtTime : '';
      var durStr = formatMmSs(m.matchSeconds || 0);
      var topLine = nameStr + (dateStr ? ' · ' + dateStr : '');
      var subLine = (teamStr ? teamStr + ' · ' : '') + 'Varaktighet: ' + durStr;
      btn.innerHTML = '<span class="history-item-date">' + escapeHtml(topLine) + '</span><span class="history-item-duration">' + escapeHtml(subLine) + '</span>';
      btn.addEventListener('click', function () {
        showMatchDetail(m);
      });
      container.appendChild(btn);
    });
  }

  function getStatsData() {
    var matches = loadMatches();
    var byPlayer = {};
    matches.forEach(function (m) {
      var matchSec = m.matchSeconds || 0;
      var teamKey = m.teamId || m.teamNameAtTime || '';
      var teamName = (m.teamNameAtTime && m.teamNameAtTime.trim()) ? m.teamNameAtTime : (teamKey ? 'Lag' : '');
      (m.players || []).forEach(function (entry) {
        var playerId = entry.playerId || entry.playerNameAtTime;
        if (!playerId) return;
        var key = teamKey + '|' + playerId;
        if (!byPlayer[key]) {
          byPlayer[key] = { totalCourt: 0, totalBench: 0, totalAssists: 0, totalFouls: 0, totalGoals: 0, matchesRecorded: 0, matchesPlayed: 0, courtSum: 0, pctSum: 0, teamName: teamName };
        }
        var data = byPlayer[key];
        if (!data.playerName) data.playerName = entry.playerNameAtTime || playerId;
        var court = entry.secondsOnCourt || 0;
        var bench = Math.max(0, matchSec - court);
        data.totalCourt += court;
        data.totalBench += bench;
        data.totalAssists += entry.assists != null ? entry.assists : 0;
        data.totalFouls += entry.fouls != null ? entry.fouls : 0;
        data.totalGoals += entry.goals != null ? entry.goals : 0;
        data.matchesRecorded += 1;
        if (court > 0) {
          data.matchesPlayed += 1;
          data.courtSum += court;
          data.pctSum += matchSec > 0 ? 100 * court / matchSec : 0;
        }
      });
    });
    return Object.keys(byPlayer)
      .map(function (key) { var d = byPlayer[key]; return { key: key, name: d.playerName || key, data: d }; })
      .sort(function (a, b) { return (b.data.totalCourt - a.data.totalCourt); });
  }

  function renderStatsList() {
    var container = document.getElementById('stats-list');
    var empty = document.getElementById('stats-empty');
    if (!container) return;
    var sorted = getStatsData();
    if (sorted.length === 0) {
      container.innerHTML = '';
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;
    container.innerHTML = '';
    sorted.forEach(function (item) {
      var d = item.data;
      var avgCourt = d.matchesPlayed > 0 ? Math.round(d.courtSum / d.matchesPlayed) : 0;
      var avgPct = d.matchesPlayed > 0 ? (d.pctSum / d.matchesPlayed).toFixed(1) : '0.0';
      var teamStr = (d.teamName && d.teamName.trim()) ? d.teamName : '';
      var topLine = item.name + (teamStr ? ' · ' + teamStr : '');
      var div = document.createElement('div');
      div.className = 'stats-item history-item';
      div.innerHTML =
        '<span class="history-item-date">' + escapeHtml(topLine) + '</span>' +
        '<table class="detail-table stats-detail-table" role="table">' +
          '<thead><tr><th>Plan</th><th>Bänk</th><th>%</th><th>Matcher</th><th>A</th><th>F</th><th>M</th></tr></thead>' +
          '<tbody><tr>' +
            '<td>' + formatMmSs(d.totalCourt) + '</td>' +
            '<td>' + formatMmSs(d.totalBench) + '</td>' +
            '<td>' + avgPct + '%</td>' +
            '<td>' + d.matchesRecorded + '</td>' +
            '<td>' + (d.totalAssists || 0) + '</td>' +
            '<td>' + (d.totalFouls || 0) + '</td>' +
            '<td>' + (d.totalGoals || 0) + '</td>' +
          '</tr></tbody></table>';
      container.appendChild(div);
    });
  }

  function exportStatsToCsv() {
    var sorted = getStatsData();
    if (sorted.length === 0) return;
    var rows = [
      ['Spelare', 'Lag', 'Total plan (mm:ss)', 'Total bänk (mm:ss)', 'Matcher registrerade', 'Matcher spelade', 'Snitt plan/match (mm:ss)', 'Snitt % spelad', 'Assists', 'Fouls', 'Mål']
    ];
    sorted.forEach(function (item) {
      var d = item.data;
      var avgCourt = d.matchesPlayed > 0 ? Math.round(d.courtSum / d.matchesPlayed) : 0;
      var avgPct = d.matchesPlayed > 0 ? (d.pctSum / d.matchesPlayed).toFixed(1) : '0.0';
      var teamStr = (d.teamName && d.teamName.trim()) ? d.teamName : '';
      rows.push([
        (item.name || '').replace(/"/g, '""'),
        teamStr.replace(/"/g, '""'),
        formatMmSs(d.totalCourt),
        formatMmSs(d.totalBench),
        String(d.matchesRecorded),
        String(d.matchesPlayed),
        formatMmSs(avgCourt),
        avgPct,
        String(d.totalAssists || 0),
        String(d.totalFouls || 0),
        String(d.totalGoals || 0)
      ]);
    });
    var csv = rows.map(function (row) {
      return row.map(function (cell) { return '"' + String(cell).replace(/"/g, '""') + '"'; }).join(',');
    }).join('\r\n');
    var now = new Date();
    var filename = 'baskettime-statistik-' + now.getFullYear() + String(now.getMonth() + 1).padStart(2, '0') + String(now.getDate()).padStart(2, '0') + '-' + String(now.getHours()).padStart(2, '0') + String(now.getMinutes()).padStart(2, '0') + '.csv';
    var blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
    if (typeof navigator !== 'undefined' && navigator.share) {
      var file = new File([blob], filename, { type: 'text/csv;charset=utf-8' });
      navigator.share({ title: 'BasketTime statistik', files: [file] }).catch(function () {
        fallbackDownload(blob, filename);
      });
    } else {
      fallbackDownload(blob, filename);
    }
  }

  function renderTeamsList() {
    var container = document.getElementById('teams-list');
    var empty = document.getElementById('teams-empty');
    if (!container) return;
    if (state.teams.length === 0) {
      container.innerHTML = '';
      container.hidden = true;
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;
    container.hidden = false;
    container.innerHTML = '';
    state.teams.forEach(function (t) {
      var li = document.createElement('li');
      li.className = 'team-item';
      li.innerHTML =
        '<span class="team-item-name">' + escapeHtml(t.name) + '</span>' +
        '<span class="team-item-meta">' + t.players.length + ' spelare</span>' +
        '<div class="team-item-actions">' +
          '<button type="button" class="btn btn-secondary btn-touch btn-team-edit" data-team-id="' + escapeHtml(t.id) + '" aria-label="Redigera lag">Redigera</button>' +
          '<button type="button" class="btn btn-outline btn-touch btn-team-delete" data-team-id="' + escapeHtml(t.id) + '" aria-label="Radera lag">Radera</button>' +
        '</div>';
      container.appendChild(li);
    });
    container.querySelectorAll('.btn-team-edit').forEach(function (btn) {
      btn.addEventListener('click', function () { openEditTeamModal(btn.getAttribute('data-team-id')); });
    });
    container.querySelectorAll('.btn-team-delete').forEach(function (btn) {
      btn.addEventListener('click', function () { confirmDeleteTeam(btn.getAttribute('data-team-id')); });
    });
  }

  var editingTeamId = null;

  function openEditTeamModal(teamId) {
    var modal = document.getElementById('modal-edit-team');
    var titleEl = document.getElementById('modal-edit-team-title');
    var nameEl = document.getElementById('input-team-name');
    var playersEl = document.getElementById('edit-team-players');
    if (!modal || !nameEl || !playersEl) return;
    editingTeamId = teamId || null;
    if (editingTeamId) {
      var t = getTeamById(editingTeamId);
      if (!t) return;
      titleEl.textContent = 'Redigera lag';
      nameEl.value = t.name;
      renderTeamPlayerFields(t.players);
    } else {
      titleEl.textContent = 'Nytt lag';
      nameEl.value = '';
      renderTeamPlayerFields(defaultTeamPlayers());
    }
    modal.showModal();
  }

  function renderTeamPlayerFields(players) {
    var playersEl = document.getElementById('edit-team-players');
    if (!playersEl) return;
    playersEl.innerHTML = '';
    (players || []).forEach(function (p, i) {
      var row = document.createElement('div');
      row.className = 'edit-name-row';
      var label = document.createElement('label');
      label.setAttribute('for', 'team-player-' + i);
      label.textContent = 'Spelare ' + (i + 1);
      var input = document.createElement('input');
      input.type = 'text';
      input.id = 'team-player-' + i;
      input.dataset.index = String(i);
      input.value = p.name;
      input.setAttribute('aria-label', 'Namn spelare ' + (i + 1));
      row.appendChild(label);
      row.appendChild(input);
      playersEl.appendChild(row);
    });
  }

  function getTeamPlayerValuesFromModal() {
    var playersEl = document.getElementById('edit-team-players');
    if (!playersEl) return [];
    var inputs = playersEl.querySelectorAll('input[type="text"]');
    var out = [];
    inputs.forEach(function (inp, i) {
      out.push({ id: 'p' + (i + 1), name: inp.value.trim() || ('Spelare ' + (i + 1)) });
    });
    return out;
  }

  function saveTeamFromModal() {
    var nameEl = document.getElementById('input-team-name');
    var name = nameEl ? nameEl.value.trim() : '';
    if (!name) name = 'Nytt lag';
    var players = getTeamPlayerValuesFromModal();
    if (players.length === 0) players = [{ id: 'p1', name: 'Spelare 1' }];
    if (editingTeamId) {
      updateTeam(editingTeamId, name, players);
    } else {
      addTeam(name, players);
    }
    document.getElementById('modal-edit-team').close();
    renderTeamsList();
    populateCreateMatchForm();
  }

  function addTeamModalPlayer() {
    var playersEl = document.getElementById('edit-team-players');
    if (!playersEl) return;
    var n = playersEl.querySelectorAll('input[type="text"]').length;
    var row = document.createElement('div');
    row.className = 'edit-name-row';
    row.innerHTML =
      '<label for="team-player-' + n + '">Spelare ' + (n + 1) + '</label>' +
      '<input type="text" id="team-player-' + n + '" data-index="' + n + '" value="Spelare ' + (n + 1) + '" aria-label="Namn spelare ' + (n + 1) + '">';
    playersEl.appendChild(row);
  }

  function removeTeamModalPlayer() {
    var playersEl = document.getElementById('edit-team-players');
    if (!playersEl) return;
    var inputs = playersEl.querySelectorAll('.edit-name-row');
    if (inputs.length <= 1) return;
    var last = inputs[inputs.length - 1];
    if (last && last.parentNode) last.parentNode.removeChild(last);
  }

  function confirmDeleteTeam(teamId) {
    var t = getTeamById(teamId);
    if (!t) return;
    document.getElementById('modal-confirm-delete-team-body').textContent = 'Laget "' + t.name + '" och alla dess spelare raderas. Detta går inte att ångra.';
    document.getElementById('modal-confirm-delete-team').dataset.teamId = teamId;
    document.getElementById('modal-confirm-delete-team').showModal();
  }

  function openEditNamesModal() {
    var modal = document.getElementById('modal-edit-names');
    var fields = document.getElementById('edit-names-fields');
    if (!modal || !fields) return;
    fields.innerHTML = '';
    state.players.forEach(function (p, i) {
      var row = document.createElement('div');
      row.className = 'edit-name-row';
      var label = document.createElement('label');
      label.setAttribute('for', 'edit-name-' + i);
      label.textContent = 'Spelare ' + (i + 1);
      var input = document.createElement('input');
      input.type = 'text';
      input.id = 'edit-name-' + i;
      input.value = p.name;
      input.setAttribute('aria-label', 'Namn spelare ' + (i + 1));
      row.appendChild(label);
      row.appendChild(input);
      fields.appendChild(row);
    });
    modal.showModal();
  }

  function closeEditNamesModal() {
    var modal = document.getElementById('modal-edit-names');
    if (!modal) return;
    for (var i = 0; i < numPlayers(); i++) {
      var input = document.getElementById('edit-name-' + i);
      if (input && state.players[i]) state.players[i].name = input.value.trim() || ('Spelare ' + (i + 1));
    }
    if (state.currentTeamId) {
      var team = getTeamById(state.currentTeamId);
      if (team) {
        team.players = state.players.map(function (p) { return { id: p.id, name: p.name }; });
        saveTeams(state.teams);
      }
    }
    renderPlayerList();
    modal.close();
  }

  // ---------- Avsluta match (spara data och stoppa klockan) ----------
  function saveCurrentMatch() {
    var matchSeconds = getMatchSeconds();
    if (matchSeconds <= 0) return;
    var name = state.currentMatchName || 'Match';
    var dateISO = state.currentMatchDateISO || new Date().toISOString();
    var match = {
      id: getMatchId(name, dateISO),
      name: name,
      dateISO: dateISO,
      matchSeconds: matchSeconds,
      teamId: state.currentTeamId || '',
      teamNameAtTime: state.currentTeamName || '',
      players: []
    };
    for (var i = 0; i < numPlayers(); i++) {
      if (!isPlayerInMatch(i)) continue;
      var p = state.players[i];
      match.players.push({
        playerId: p ? p.id : ('p' + (i + 1)),
        playerNameAtTime: p ? p.name : ('Spelare ' + (i + 1)),
        secondsOnCourt: getCourtSecondsForPlayer(i),
        assists: getPlayerAssists(i),
        fouls: getPlayerFouls(i),
        goals: getPlayerGoals(i)
      });
    }
    saveOrUpdateMatch(match);
    pauseMatch();
    state.matchElapsedMs = 0;
    state.matchStartTime = null;
    updateMasterClockDisplay();
    state.currentMatchName = '';
    state.currentMatchDateISO = '';
    state.currentTeamId = '';
    state.currentTeamName = '';
    state.players = [];
    state.playerCourtSeconds = [];
    state.playerOnCourtSince = [];
    state.playerInMatch = [];
    state.playerAssists = [];
    state.playerFouls = [];
    state.playerGoals = [];
    renderMatchPanel();
    renderHistoryList();
    renderStatsList();
    updateOngoingMatchButton();
  }

  // ---------- Export CSV ----------
  function exportMatchToCsv(match) {
    var matchSec = match.matchSeconds || 0;
    var rows = [
      ['Match Name', 'Match Date', 'Team', 'Match Duration (mm:ss)', 'Player Name', 'On Court (mm:ss)', 'On Court (seconds)', 'Bench (mm:ss)', 'Bench (seconds)', '% Played', 'Assists', 'Fouls', 'Mål']
    ];
    var matchName = (match.name && match.name.trim()) ? match.name : 'Match';
    var dateStr = match.dateISO ? new Date(match.dateISO).toLocaleString('sv-SE') : '';
    var teamStr = (match.teamNameAtTime && match.teamNameAtTime.trim()) ? match.teamNameAtTime : '';
    var durStr = formatMmSs(matchSec);
    (match.players || []).forEach(function (entry) {
      var court = entry.secondsOnCourt || 0;
      var bench = Math.max(0, matchSec - court);
      var pct = matchSec > 0 ? (100 * court / matchSec).toFixed(1) : '0.0';
      var assists = entry.assists != null ? entry.assists : 0;
      var fouls = entry.fouls != null ? entry.fouls : 0;
      var goals = entry.goals != null ? entry.goals : 0;
      rows.push([
        matchName,
        dateStr,
        teamStr,
        durStr,
        (entry.playerNameAtTime || '').replace(/"/g, '""'),
        formatMmSs(court),
        String(court),
        formatMmSs(bench),
        String(bench),
        pct,
        String(assists),
        String(fouls),
        String(goals)
      ]);
    });
    var csv = rows.map(function (row) {
      return row.map(function (cell) { return '"' + String(cell).replace(/"/g, '""') + '"'; }).join(',');
    }).join('\r\n');
    var now = new Date();
    var y = now.getFullYear();
    var mo = String(now.getMonth() + 1).padStart(2, '0');
    var d = String(now.getDate()).padStart(2, '0');
    var h = String(now.getHours()).padStart(2, '0');
    var mi = String(now.getMinutes()).padStart(2, '0');
    var filename = 'baskettime-' + y + mo + d + '-' + h + mi + '.csv';
    var blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
    if (typeof navigator !== 'undefined' && navigator.share) {
      var file = new File([blob], filename, { type: 'text/csv;charset=utf-8' });
      navigator.share({ title: 'BasketTime match', files: [file] }).catch(function () {
        fallbackDownload(blob, filename);
      });
    } else {
      fallbackDownload(blob, filename);
    }
  }

  function fallbackDownload(blob, filename) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function getViewMode() {
    try {
      var v = localStorage.getItem(STORAGE_KEYS.viewMode);
      return (v === 'desktop' || v === 'phone') ? v : 'phone';
    } catch (e) { return 'phone'; }
  }

  function setViewMode(mode) {
    try {
      localStorage.setItem(STORAGE_KEYS.viewMode, mode);
    } catch (e) {}
    applyViewMode();
  }

  function applyViewMode() {
    var mode = getViewMode();
    document.body.classList.remove('view-mode-phone', 'view-mode-desktop');
    document.body.classList.add('view-mode-' + mode);
    var btnPhone = document.getElementById('btn-view-phone');
    var btnDesktop = document.getElementById('btn-view-desktop');
    if (btnPhone) btnPhone.setAttribute('aria-pressed', mode === 'phone');
    if (btnDesktop) btnDesktop.setAttribute('aria-pressed', mode === 'desktop');
  }

  // ---------- Wire UI ----------
  function init() {
    state.teams = loadTeams();
    state.players = [];
    ensureState();

    applyViewMode();
    var btnPhone = document.getElementById('btn-view-phone');
    var btnDesktop = document.getElementById('btn-view-desktop');
    if (btnPhone) btnPhone.addEventListener('click', function () { setViewMode('phone'); });
    if (btnDesktop) btnDesktop.addEventListener('click', function () { setViewMode('desktop'); });

    updateMasterClockDisplay();
    setMatchStatusDisplay(false);
    setStartPauseButtonLabel(true);
    renderMatchPanel();
    renderHistoryList();
    renderStatsList();
    updateOngoingMatchButton();

    var dateEl = document.getElementById('input-match-date');
    if (dateEl && !dateEl.value) {
      var today = new Date();
      dateEl.value = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
    }

    document.getElementById('btn-borja-match').addEventListener('click', startMatchFromForm);
    startPauseBtn.addEventListener('click', function () {
      if (state.matchRunning) pauseMatch(); else startMatch();
    });
    updateStartButtonState();
    document.getElementById('btn-edit-names').addEventListener('click', openEditNamesModal);
    document.getElementById('btn-save-match').addEventListener('click', saveCurrentMatch);
    document.getElementById('btn-reset-match').addEventListener('click', resetMatch);
    document.getElementById('btn-new-match').addEventListener('click', startNewMatch);

    var modalMatchMenu = document.getElementById('modal-match-menu');
    var btnMatchMenu = document.getElementById('btn-match-menu');
    if (btnMatchMenu && modalMatchMenu) {
      btnMatchMenu.addEventListener('click', function () {
        modalMatchMenu.showModal();
        btnMatchMenu.setAttribute('aria-expanded', 'true');
      });
      modalMatchMenu.addEventListener('close', function () {
        btnMatchMenu.setAttribute('aria-expanded', 'false');
      });
      document.getElementById('btn-menu-edit-names').addEventListener('click', function () {
        modalMatchMenu.close();
        openEditNamesModal();
      });
      document.getElementById('btn-menu-save-match').addEventListener('click', function () {
        modalMatchMenu.close();
        saveCurrentMatch();
      });
      document.getElementById('btn-menu-reset-match').addEventListener('click', function () {
        modalMatchMenu.close();
        resetMatch();
      });
      document.getElementById('btn-menu-new-match').addEventListener('click', function () {
        modalMatchMenu.close();
        startNewMatch();
      });
      document.getElementById('btn-close-match-menu').addEventListener('click', function () {
        modalMatchMenu.close();
        btnMatchMenu.setAttribute('aria-expanded', 'false');
      });
    }

    document.getElementById('btn-add-team').addEventListener('click', function () { openEditTeamModal(null); });
    document.getElementById('btn-save-team').addEventListener('click', saveTeamFromModal);
    document.getElementById('btn-add-player').addEventListener('click', addTeamModalPlayer);
    document.getElementById('btn-remove-player').addEventListener('click', removeTeamModalPlayer);

    document.getElementById('btn-close-edit-names').addEventListener('click', closeEditNamesModal);
    document.getElementById('modal-edit-names').addEventListener('cancel', closeEditNamesModal);

    document.getElementById('btn-confirm-delete-team-no').addEventListener('click', function () {
      document.getElementById('modal-confirm-delete-team').close();
    });
    document.getElementById('btn-confirm-delete-team-yes').addEventListener('click', function () {
      var id = document.getElementById('modal-confirm-delete-team').dataset.teamId;
      if (id) deleteTeam(id);
      document.getElementById('modal-confirm-delete-team').close();
      renderTeamsList();
      populateCreateMatchForm();
    });

    var btnOngoing = document.getElementById('btn-ongoing-match');
    if (btnOngoing) btnOngoing.addEventListener('click', function () {
      showPanel('panel-match');
      updateStartButtonState();
    });

    document.querySelectorAll('.tab-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var tab = btn.getAttribute('data-tab');
        if (tab === 'match') {
          showPanel('panel-match');
          updateStartButtonState();
        } else if (tab === 'teams') showPanel('panel-teams');
        else if (tab === 'history') { showPanel('panel-history'); renderHistoryList(); }
        else if (tab === 'stats') { showPanel('panel-stats'); renderStatsList(); }
      });
    });

    document.getElementById('btn-export-stats-csv').addEventListener('click', exportStatsToCsv);

    document.getElementById('btn-clear-all-history').addEventListener('click', function () {
      document.getElementById('modal-confirm-clear').showModal();
    });
    document.getElementById('btn-confirm-clear-no').addEventListener('click', function () {
      document.getElementById('modal-confirm-clear').close();
    });
    document.getElementById('btn-confirm-clear-yes').addEventListener('click', function () {
      clearAllMatches();
      document.getElementById('modal-confirm-clear').close();
      showPanel('panel-history');
      renderHistoryList();
      renderStatsList();
    });

    document.getElementById('btn-back-from-detail').addEventListener('click', function () {
      showPanel('panel-history');
      renderHistoryList();
    });
    document.getElementById('btn-export-csv').addEventListener('click', function () {
      var id = document.getElementById('panel-match-detail').dataset.matchId;
      var matches = loadMatches().filter(function (m) { return m.id === id; });
      if (matches.length) exportMatchToCsv(matches[0]);
    });
    document.getElementById('btn-delete-match').addEventListener('click', function () {
      var id = document.getElementById('panel-match-detail').dataset.matchId;
      if (!id) return;
      deleteMatchById(id);
      showPanel('panel-history');
      renderHistoryList();
      renderStatsList();
    });
  }

  function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) return;
    navigator.serviceWorker.register('./sw.js', { scope: './' }).catch(function () {});
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      init();
      registerServiceWorker();
    });
  } else {
    init();
    registerServiceWorker();
  }
})();
