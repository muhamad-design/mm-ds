/* mm-ds · docs shell behavior. No dependencies. */
(function () {
  'use strict';
  var root = document.documentElement;

  /* ---- theme: light / dark / system --------------------------------- */
  var THEME_KEY = 'mmds-theme';
  function prefValue() {
    try { return localStorage.getItem(THEME_KEY) || 'system'; } catch (e) { return 'system'; }
  }
  function systemDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function applyTheme(pref) {
    var resolved = pref === 'system' ? (systemDark() ? 'dark' : 'light') : pref;
    root.setAttribute('data-theme', resolved);
    root.setAttribute('data-theme-pref', pref);
    try { localStorage.setItem(THEME_KEY, pref); } catch (e) {}
    document.querySelectorAll('.theme-switch button').forEach(function (b) {
      b.setAttribute('aria-checked', String(b.dataset.theme === pref));
    });
  }
  document.querySelectorAll('.theme-switch button').forEach(function (b) {
    b.addEventListener('click', function () { applyTheme(b.dataset.theme); });
  });
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
      if (prefValue() === 'system') applyTheme('system');
    });
  }
  applyTheme(prefValue());

  /* ---- mobile sidebar ------------------------------------------------ */
  var sidebar = document.getElementById('sidebar');
  var backdrop = document.getElementById('navBackdrop');
  var navBtn = document.getElementById('navBtn');
  function closeNav() { sidebar.classList.remove('open'); backdrop.classList.remove('show'); }
  if (navBtn) navBtn.addEventListener('click', function () {
    sidebar.classList.toggle('open'); backdrop.classList.toggle('show');
  });
  if (backdrop) backdrop.addEventListener('click', closeNav);

  /* ---- copy-to-clipboard --------------------------------------------- */
  function flash(el) {
    el.classList.add('copied');
    var prev = el.dataset.label || el.textContent;
    if (el.classList.contains('copy')) { el.dataset.label = prev; el.textContent = 'Copied'; }
    setTimeout(function () {
      el.classList.remove('copied');
      if (el.classList.contains('copy')) el.textContent = el.dataset.label;
    }, 900);
  }
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-copy]');
    if (!t) return;
    var text = t.getAttribute('data-copy');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { flash(t); });
    }
  });

  /* ---- toc scroll-spy -------------------------------------------------- */
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var byId = {};
    tocLinks.forEach(function (l) { byId[l.getAttribute('href').slice(1)] = l; });
    var current = null;
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && byId[en.target.id]) {
          if (current) current.classList.remove('active');
          current = byId[en.target.id];
          current.classList.add('active');
        }
      });
    }, { rootMargin: '-10% 0px -80% 0px' });
    document.querySelectorAll('.doc section[id]').forEach(function (s) { obs.observe(s); });
  }

  /* ---- search (Cmd/Ctrl+K) ---------------------------------------------- */
  var modal = document.getElementById('searchModal');
  var input = document.getElementById('searchInput');
  var results = document.getElementById('searchResults');
  var INDEX = window.__DS_INDEX || [];
  var sel = -1, items = [];

  function openSearch() {
    if (!modal) return;
    modal.hidden = false;
    input.value = '';
    render('');
    input.focus();
  }
  function closeSearch() { if (modal) modal.hidden = true; }

  function render(q) {
    q = q.trim().toLowerCase();
    var hits = [];
    for (var i = 0; i < INDEX.length; i++) {
      var it = INDEX[i];
      if (!q) { if (it.k === 'Page') hits.push(it); continue; }
      var hay = (it.t + ' ' + (it.v || '') + ' ' + it.k).toLowerCase();
      if (hay.indexOf(q) !== -1) hits.push(it);
      if (hits.length > 60) break;
    }
    sel = hits.length ? 0 : -1;
    items = [];
    results.innerHTML = '';
    if (!hits.length) {
      var d = document.createElement('div');
      d.className = 'search-empty';
      d.textContent = 'No results for “' + q + '”';
      results.appendChild(d);
      return;
    }
    var lastGroup = null;
    hits.forEach(function (it) {
      if (it.k !== lastGroup) {
        lastGroup = it.k;
        var g = document.createElement('div');
        g.className = 'search-group';
        g.textContent = it.k === 'Page' ? 'Pages' : it.k;
        results.appendChild(g);
      }
      var a = document.createElement('a');
      a.className = 'search-item';
      a.href = it.p;
      if (it.c) {
        var swatch = document.createElement('span');
        swatch.className = 'sw';
        swatch.style.background = it.c;
        a.appendChild(swatch);
      }
      var t = document.createElement('span');
      t.className = 't';
      t.textContent = it.t;
      a.appendChild(t);
      if (it.v) {
        var v = document.createElement('span');
        v.className = 'v';
        v.textContent = it.v;
        a.appendChild(v);
      }
      results.appendChild(a);
      items.push(a);
    });
    highlight();
  }
  function highlight() {
    items.forEach(function (el, i) { el.classList.toggle('sel', i === sel); });
    if (sel >= 0 && items[sel]) items[sel].scrollIntoView({ block: 'nearest' });
  }

  if (modal) {
    document.querySelectorAll('[data-search-open]').forEach(function (b) {
      b.addEventListener('click', openSearch);
    });
    modal.querySelector('.search-scrim').addEventListener('click', closeSearch);
    input.addEventListener('input', function () { render(input.value); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); if (items.length) { sel = (sel + 1) % items.length; highlight(); } }
      else if (e.key === 'ArrowUp') { e.preventDefault(); if (items.length) { sel = (sel - 1 + items.length) % items.length; highlight(); } }
      else if (e.key === 'Enter') { if (sel >= 0 && items[sel]) window.location.href = items[sel].getAttribute('href'); }
    });
    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); modal.hidden ? openSearch() : closeSearch(); }
      else if (e.key === 'Escape' && !modal.hidden) closeSearch();
      else if (e.key === '/' && modal.hidden && !/^(input|textarea|select)$/i.test(document.activeElement.tagName)) {
        e.preventDefault(); openSearch();
      }
    });
  }

  /* ---- RTL live demo (direction page) -------------------------------------- */
  var bidiBtn = document.getElementById('bidiBtn');
  var bidiStage = document.getElementById('bidiStage');
  if (bidiBtn && bidiStage) {
    var bidiDir = document.getElementById('bidiDir');
    var bidiLocale = document.getElementById('bidiLocale');
    bidiBtn.addEventListener('click', function () {
      var rtl = bidiStage.getAttribute('dir') !== 'rtl';
      bidiStage.setAttribute('dir', rtl ? 'rtl' : 'ltr');
      bidiDir.textContent = rtl ? 'RTL' : 'LTR';
      bidiLocale.textContent = rtl ? 'ar' : 'en';
    });
  }
})();
