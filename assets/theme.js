/* Light / dark theme switch. Loaded in <head> so the saved theme
   is applied before the page paints (no flash of the wrong theme). */
(function () {
  var KEY = 'theme';
  var root = document.documentElement;
  var media = window.matchMedia('(prefers-color-scheme: dark)');

  function saved() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function store(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function current() { return root.getAttribute('data-theme') || (media.matches ? 'dark' : 'light'); }

  var s = saved();
  if (s === 'light' || s === 'dark') root.setAttribute('data-theme', s);

  function sync() {
    var dark = current() === 'dark';
    document.querySelectorAll('meta[name="theme-color"]').forEach(function (m) {
      m.setAttribute('content', dark ? '#121416' : '#ffffff');
      m.removeAttribute('media');
    });
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
      btn.setAttribute('title', dark ? 'Light theme' : 'Dark theme');
      btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      store(next);
      sync();
    });
    sync();
  });
  media.addEventListener && media.addEventListener('change', function () { if (!saved()) sync(); });
})();
