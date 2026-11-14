// Light and dark theme switch. The choice is remembered; until one is made,
// the site follows the device setting.
(function () {
  var button = document.getElementById('theme-toggle');
  if (!button) return;
  button.addEventListener('click', function () {
    var root = document.documentElement;
    var current =
      root.dataset.theme ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = current === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try {
      localStorage.setItem('theme', next);
    } catch (error) {
      // Private browsing: the theme still changes for this visit.
    }
  });
})();
