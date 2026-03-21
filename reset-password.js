/**
 * BasketTime – återställ lösenord (token i URL).
 */
(function () {
  'use strict';

  function t(key) {
    return window.i18n && window.i18n.t ? window.i18n.t(key) : key;
  }

  function apiFetch(path, opts) {
    var base = (typeof window.BASKETTIME_API_BASE !== 'undefined' && window.BASKETTIME_API_BASE) ? window.BASKETTIME_API_BASE : '';
    var url = base + path;
    var options = { credentials: 'include', headers: opts && opts.headers || {} };
    if (opts) {
      if (opts.method) options.method = opts.method;
      if (opts.body) options.body = opts.body;
      if (opts.headers) options.headers = opts.headers;
    }
    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData) && typeof options.body !== 'string') {
      options.body = JSON.stringify(options.body);
      if (!options.headers['Content-Type']) options.headers['Content-Type'] = 'application/json';
    }
    return fetch(url, options);
  }

  function getToken() {
    var params = new URLSearchParams(window.location.search);
    return (params.get('token') || '').trim();
  }

  function whenDom(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  whenDom(function () {
    var form = document.getElementById('reset-form');
    var passEl = document.getElementById('reset-password-input');
    var msg = document.getElementById('reset-msg');
    var submitBtn = form ? form.querySelector('[type="submit"]') : null;

    function showMsg(text, ok) {
      if (!msg) return;
      msg.hidden = !text;
      msg.textContent = text || '';
      msg.className = ok ? 'login-error login-error--ok' : 'login-error';
    }

    var token = getToken();
    if (!token || token.length < 10) {
      showMsg(t('reset.errorToken'), false);
      if (form) form.style.display = 'none';
      return;
    }

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var pw = passEl ? passEl.value : '';
        if (!pw || pw.length < 6) {
          showMsg(t('login.errorPasswordLength'), false);
          return;
        }
        showMsg('');
        if (submitBtn) submitBtn.disabled = true;
        apiFetch('/api/auth/reset-password', { method: 'POST', body: { token: token, password: pw } }).then(function (r) {
          return r.json().catch(function () { return {}; }).then(function (data) {
            if (r.ok) {
              showMsg(t('reset.success'), true);
              if (form) form.style.display = 'none';
              return;
            }
            showMsg(data.error || t('reset.error'), false);
          });
        }).catch(function () {
          showMsg(t('login.errorNetwork'), false);
        }).finally(function () {
          if (submitBtn) submitBtn.disabled = false;
        });
      });
    }
  });

  document.addEventListener('i18n-ready', function () {
    if (window.i18n && window.i18n.apply) window.i18n.apply();
  });
})();
