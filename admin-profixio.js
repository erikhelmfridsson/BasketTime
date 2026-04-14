(function () {
  'use strict';

  function apiFetch(url, opts) {
    opts = opts || {};
    var headers = opts.headers || {};
    headers['Accept'] = 'application/json';
    if (opts.body && typeof opts.body !== 'string') {
      headers['Content-Type'] = 'application/json';
    }
    return fetch(url, {
      method: opts.method || 'GET',
      headers: headers,
      body: opts.body ? (typeof opts.body === 'string' ? opts.body : JSON.stringify(opts.body)) : undefined,
      credentials: 'include',
    });
  }

  function setMsg(text, ok) {
    var el = document.getElementById('admin-msg');
    if (!el) return;
    el.hidden = !text;
    el.textContent = text || '';
    el.className = ok ? 'settings-email-msg settings-email-msg--ok' : 'settings-email-msg';
  }

  function esc(s) {
    return String(s || '').replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] || c;
    });
  }

  function loadConfigs() {
    setMsg('', false);
    var list = document.getElementById('cfg-list');
    if (list) list.innerHTML = '';
    return apiFetch('/api/profixio/admin/config').then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (data) {
        if (!r.ok) throw new Error(data.error || 'failed');
        renderConfigs(data.configs || []);
      });
    }).catch(function (e) {
      setMsg('Kunde inte ladda konfiguration. ' + (e && e.message ? e.message : ''), false);
    });
  }

  function renderConfigs(configs) {
    var list = document.getElementById('cfg-list');
    if (!list) return;
    list.innerHTML = '';
    if (!configs.length) {
      list.innerHTML = '<div class="empty-state"><p>Ingen konfiguration ännu.</p></div>';
      return;
    }
    configs.forEach(function (cfg) {
      var row = document.createElement('div');
      row.className = 'history-item';
      var title = 'Turnering ' + cfg.tournamentId + (cfg.organisationId ? (' (' + cfg.organisationId + ')') : '');
      var sub = (cfg.enabled ? 'Aktiv' : 'Avstängd') + (cfg.updatedAt ? (' • ' + cfg.updatedAt) : '');
      row.innerHTML =
        '<span class="history-item-date">' + esc(title) + '</span>' +
        '<span class="history-item-duration">' + esc(sub) + '</span>';

      var btnRun = document.createElement('button');
      btnRun.type = 'button';
      btnRun.className = 'btn btn-secondary btn-touch';
      btnRun.textContent = 'Kör nu';
      btnRun.addEventListener('click', function () {
        setMsg('Kör synk…', false);
        apiFetch('/api/profixio/admin/run-now', { method: 'POST', body: { tournamentId: cfg.tournamentId, organisationId: cfg.organisationId } })
          .then(function (r) { return r.json().catch(function () { return {}; }).then(function (data) { if (!r.ok) throw new Error(data.error || 'failed'); return data; }); })
          .then(function (data) {
            setMsg('Klart. Lag: ' + (data.teams || 0) + ', spelare: ' + (data.players || 0) + ', matcher: ' + (data.matches || 0) + '.', true);
            loadConfigs();
          })
          .catch(function (e) {
            setMsg('Kunde inte köra synk. ' + (e && e.message ? e.message : ''), false);
          });
      });

      var btnToggle = document.createElement('button');
      btnToggle.type = 'button';
      btnToggle.className = 'btn btn-outline btn-touch';
      btnToggle.textContent = cfg.enabled ? 'Stäng av' : 'Aktivera';
      btnToggle.addEventListener('click', function () {
        apiFetch('/api/profixio/admin/config', { method: 'POST', body: { tournamentId: cfg.tournamentId, organisationId: cfg.organisationId, enabled: !cfg.enabled } })
          .then(function (r) { return r.json().catch(function () { return {}; }).then(function (data) { if (!r.ok) throw new Error(data.error || 'failed'); }); })
          .then(function () { loadConfigs(); })
          .catch(function (e) { setMsg('Kunde inte uppdatera. ' + (e && e.message ? e.message : ''), false); });
      });

      var btnDelete = document.createElement('button');
      btnDelete.type = 'button';
      btnDelete.className = 'btn btn-outline btn-touch';
      btnDelete.textContent = 'Ta bort';
      btnDelete.addEventListener('click', function () {
        apiFetch('/api/profixio/admin/config?id=' + encodeURIComponent(String(cfg.id)), { method: 'DELETE' })
          .then(function (r) { return r.json().catch(function () { return {}; }).then(function (data) { if (!r.ok) throw new Error(data.error || 'failed'); }); })
          .then(function () { loadConfigs(); })
          .catch(function (e) { setMsg('Kunde inte ta bort. ' + (e && e.message ? e.message : ''), false); });
      });

      row.appendChild(btnRun);
      row.appendChild(btnToggle);
      row.appendChild(btnDelete);
      list.appendChild(row);
    });
  }

  function wire() {
    var btnAdd = document.getElementById('btn-add-config');
    var btnRefresh = document.getElementById('btn-refresh');
    if (btnRefresh) btnRefresh.addEventListener('click', loadConfigs);
    if (btnAdd) btnAdd.addEventListener('click', function () {
      var org = (document.getElementById('cfg-org') || {}).value || '';
      var tid = (document.getElementById('cfg-tournament') || {}).value || '';
      tid = tid.trim();
      org = org.trim();
      if (!tid) {
        setMsg('Ange turnering-ID.', false);
        return;
      }
      setMsg('Sparar…', false);
      apiFetch('/api/profixio/admin/config', { method: 'POST', body: { tournamentId: parseInt(tid, 10), organisationId: org, enabled: true } })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (data) { if (!r.ok) throw new Error(data.error || 'failed'); }); })
        .then(function () {
          setMsg('Sparat.', true);
          loadConfigs();
        })
        .catch(function (e) { setMsg('Kunde inte spara. ' + (e && e.message ? e.message : ''), false); });
    });
    loadConfigs();
  }

  wire();
})();

