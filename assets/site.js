// Behaviour for the portfolio site. No libraries and no build step.
//
// Every page is complete without this file: it adds motion (evidence that
// draws itself when it comes into view) and controls (the hero examples, the
// skill filter, the monitoring chart). Each part looks for its own markup and
// does nothing when that markup is absent.
(function () {
  'use strict';

  var root = document.documentElement;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  // The page head hides things that are about to animate in. This tells it
  // the script arrived, so nothing is left hidden.
  window.siteReady = true;

  function all(selector, scope) {
    return Array.prototype.slice.call((scope || document).querySelectorAll(selector));
  }

  // Runs a change inside a view transition where the browser supports one.
  function withTransition(change) {
    if (reduced || !document.startViewTransition) {
      change();
      return null;
    }
    return document.startViewTransition(change);
  }

  // ---- Theme switch -------------------------------------------------------
  // The choice is remembered; until one is made the site follows the device.

  (function theme() {
    var button = document.getElementById('theme-toggle');
    if (!button) return;
    button.addEventListener('click', function () {
      var current =
        root.dataset.theme ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = current === 'dark' ? 'light' : 'dark';
      function apply() {
        root.dataset.theme = next;
      }
      try {
        localStorage.setItem('theme', next);
      } catch (error) {
        // Private browsing: the theme still changes for this visit.
      }

      root.classList.add('theme-switch');
      var transition = withTransition(apply);
      if (!transition) {
        root.classList.remove('theme-switch');
        return;
      }
      // The new theme spreads outward from the button.
      var box = button.getBoundingClientRect();
      var x = box.left + box.width / 2;
      var y = box.top + box.height / 2;
      var radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
      transition.ready
        .then(function () {
          root.animate(
            {
              clipPath: [
                'circle(0px at ' + x + 'px ' + y + 'px)',
                'circle(' + radius + 'px at ' + x + 'px ' + y + 'px)',
              ],
            },
            { duration: 550, easing: 'ease-in-out', pseudoElement: '::view-transition-new(root)' },
          );
        })
        .catch(function () {});
      transition.finished.then(
        function () {
          root.classList.remove('theme-switch');
        },
        function () {
          root.classList.remove('theme-switch');
        },
      );
    });
  })();

  // ---- Numbers that count up ----------------------------------------------

  function countUp(element) {
    var final = element.dataset.final || (element.dataset.final = element.textContent);
    var match = final.match(/\d[\d,]*(\.\d+)?/);
    if (reduced || !match) {
      element.textContent = final;
      return;
    }
    var target = parseFloat(match[0].replace(/,/g, ''));
    if (!target) return;
    var decimals = match[1] ? match[1].length - 1 : 0;
    var grouped = match[0].indexOf(',') !== -1;
    var before = final.slice(0, match.index);
    var after = final.slice(match.index + match[0].length);
    var started = null;
    var duration = 1000;

    function frame(now) {
      if (started === null) started = now;
      var t = Math.min((now - started) / duration, 1);
      var value = target * (1 - Math.pow(1 - t, 3));
      var text = value.toFixed(decimals);
      if (grouped) text = Number(text).toLocaleString('en-US');
      element.textContent = t < 1 ? before + text + after : final;
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  function draw(element) {
    element.classList.add('in');
    if (element.matches('.bars')) all('.bar-value', element).forEach(countUp);
    if (element.matches('.stats')) all('dd', element).forEach(countUp);
  }

  // ---- Things that appear as they scroll into view -------------------------

  (function reveal() {
    var targets = all('[data-reveal], .bars, .stats, .matrix, .monitor').filter(function (element) {
      return !element.closest('[data-slides]');
    });
    if (reduced || !('IntersectionObserver' in window)) {
      targets.forEach(draw);
      return;
    }
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          observer.unobserve(entry.target);
          draw(entry.target);
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -6% 0px' },
    );
    targets.forEach(function (element) {
      observer.observe(element);
    });
  })();

  // ---- Hero: one example per tab -------------------------------------------

  (function slides() {
    var figure = document.querySelector('[data-slides]');
    if (!figure) return;
    var tablist = figure.querySelector('[role="tablist"]');
    var tabs = all('[role="tab"]', figure);
    var panels = all('.slide', figure);
    var current = 0;
    var advances = 0;
    var limit = panels.length * 2; // Two rounds on its own, then it rests.

    panels.forEach(function (panel, index) {
      panel.hidden = false;
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', 'tab-' + index);
    });
    tablist.hidden = false;
    panels[0].classList.add('active');
    figure.querySelector('.slides').classList.add('ready');

    function redraw(panel) {
      var bars = panel.querySelector('.bars');
      bars.classList.add('reset');
      bars.classList.remove('in');
      void bars.offsetWidth;
      bars.classList.remove('reset');
      draw(bars);
    }

    function show(index, byPerson) {
      current = index;
      tabs.forEach(function (tab, i) {
        tab.setAttribute('aria-selected', i === index ? 'true' : 'false');
        tab.tabIndex = i === index ? 0 : -1;
      });
      panels.forEach(function (panel, i) {
        panel.classList.toggle('active', i === index);
      });
      redraw(panels[index]);
      if (byPerson) figure.classList.remove('autoplay');
    }

    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () {
        show(index, true);
      });
      tab.addEventListener('keydown', function (event) {
        var step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
        if (!step) return;
        event.preventDefault();
        var next = (index + step + tabs.length) % tabs.length;
        show(next, true);
        tabs[next].focus();
      });
    });

    // The first example draws once the card has arrived.
    setTimeout(
      function () {
        draw(panels[0].querySelector('.bars'));
        if (!reduced) figure.classList.add('autoplay');
      },
      reduced ? 0 : 900,
    );

    figure.addEventListener('animationend', function (event) {
      if (event.animationName !== 'tick' || !figure.classList.contains('autoplay')) return;
      advances += 1;
      if (advances >= limit) {
        figure.classList.remove('autoplay');
        if (current !== 0) show(0, false);
        return;
      }
      show((current + 1) % panels.length, false);
    });

    function pause() {
      figure.classList.add('paused');
    }
    function resume() {
      figure.classList.remove('paused');
    }
    figure.addEventListener('pointerenter', pause);
    figure.addEventListener('pointerleave', resume);
    figure.addEventListener('focusin', pause);
    figure.addEventListener('focusout', resume);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        figure.classList.toggle('paused', !entries[0].isIntersecting);
      }).observe(figure);
    }
  })();

  // ---- Hero: the graph paper follows the pointer ---------------------------

  (function paper() {
    var hero = document.querySelector('.hero-home');
    if (!hero || reduced || !finePointer) return;
    var waiting = false;
    hero.addEventListener('pointermove', function (event) {
      if (waiting) return;
      waiting = true;
      requestAnimationFrame(function () {
        var box = hero.getBoundingClientRect();
        hero.style.setProperty('--mx', event.clientX - box.left + 'px');
        hero.style.setProperty('--my', event.clientY - box.top + 'px');
        waiting = false;
      });
    });
  })();

  // ---- Selected work: filter by skill --------------------------------------

  (function filter() {
    var bar = document.querySelector('[data-filter]');
    if (!bar) return;
    var chips = all('.chip', bar);
    var rows = all('.work-row');
    var status = bar.querySelector('[data-filter-status]');
    bar.hidden = false;

    function apply(skill) {
      var showing = 0;
      chips.forEach(function (chip) {
        chip.setAttribute('aria-pressed', chip.dataset.skill === skill ? 'true' : 'false');
      });
      rows.forEach(function (row) {
        var match = !skill || row.dataset.skills.split('|').indexOf(skill) !== -1;
        row.hidden = !match;
        row.classList.add('in');
        if (match) showing += 1;
      });
      status.textContent = skill
        ? showing + ' of ' + rows.length + ' projects use ' + skill
        : rows.length + ' projects';
    }

    function choose(skill) {
      withTransition(function () {
        apply(skill);
      });
    }

    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        // Choosing the chip that is already on goes back to everything.
        var on = chip.getAttribute('aria-pressed') === 'true';
        choose(on ? '' : chip.dataset.skill);
      });
    });

    // A skill name in the skills table filters the work and goes to it.
    all('.matrix [data-skill]').forEach(function (link) {
      link.addEventListener('click', function (event) {
        event.preventDefault();
        choose(link.dataset.skill);
        document.getElementById('work').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' });
        var chip = chips.filter(function (c) {
          return c.dataset.skill === link.dataset.skill;
        })[0];
        if (chip) chip.focus({ preventScroll: true });
      });
    });
  })();

  // ---- Home: mark the section you are in -----------------------------------

  (function sections() {
    if (root.dataset.page !== 'home') return;
    var links = {};
    all('.top nav a').forEach(function (link) {
      var hash = link.getAttribute('href').split('#')[1];
      if (hash) links[hash] = link;
    });
    // "More on GitHub" is still work, so it keeps Work marked.
    var owner = { work: 'work', more: 'work', skills: 'skills', about: 'about' };
    var parts = Object.keys(owner)
      .map(function (id) {
        return document.getElementById(id);
      })
      .filter(Boolean);
    var waiting = false;

    function update() {
      waiting = false;
      var middle = window.innerHeight * 0.4;
      var name = null;
      parts.forEach(function (part) {
        var box = part.getBoundingClientRect();
        if (box.top <= middle && box.bottom > middle) name = owner[part.id];
      });
      Object.keys(links).forEach(function (key) {
        if (key === name) links[key].setAttribute('aria-current', 'true');
        else links[key].removeAttribute('aria-current');
      });
    }

    window.addEventListener(
      'scroll',
      function () {
        if (waiting) return;
        waiting = true;
        requestAnimationFrame(update);
      },
      { passive: true },
    );
    update();
  })();

  // ---- Case study: reading progress and the section you are in -------------

  (function reading() {
    var bar = document.querySelector('.progress span');
    var toc = document.querySelector('[data-toc]');
    if (!bar && !toc) return;
    var headings = all('.case-main h2[id]');
    var links = toc ? all('a', toc) : [];
    var waiting = false;

    function update() {
      waiting = false;
      var scrollable = document.documentElement.scrollHeight - window.innerHeight;
      if (bar) bar.style.setProperty('--p', scrollable > 0 ? Math.min(window.scrollY / scrollable, 1) : 0);
      var active = null;
      headings.forEach(function (heading) {
        if (heading.getBoundingClientRect().top < window.innerHeight * 0.35) active = heading.id;
      });
      // At the very bottom the last section is the one being read.
      if (headings.length && scrollable > 0 && window.scrollY >= scrollable - 2) {
        active = headings[headings.length - 1].id;
      }
      links.forEach(function (link) {
        if (link.getAttribute('href') === '#' + active) link.setAttribute('aria-current', 'true');
        else link.removeAttribute('aria-current');
      });
    }

    window.addEventListener(
      'scroll',
      function () {
        if (waiting) return;
        waiting = true;
        requestAnimationFrame(update);
      },
      { passive: true },
    );
    window.addEventListener('resize', update);
    update();
  })();

  // ---- Case study: charts and screenshots open larger ----------------------

  (function zoom() {
    var images = all('.case-main .fig img');
    if (!images.length || !window.HTMLDialogElement) return;
    var dialog = document.createElement('dialog');
    dialog.className = 'zoom';
    dialog.innerHTML = '<img alt=""><button type="button">Close</button>';
    document.body.appendChild(dialog);
    var large = dialog.querySelector('img');
    dialog.addEventListener('click', function () {
      dialog.close();
    });

    images.forEach(function (image) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'zoomable';
      button.setAttribute('aria-label', 'Enlarge: ' + image.alt);
      image.parentNode.insertBefore(button, image);
      button.appendChild(image);
      button.addEventListener('click', function () {
        large.src = image.currentSrc || image.src;
        large.alt = image.alt;
        dialog.showModal();
      });
    });
  })();

  // ---- Case study: copy a command ------------------------------------------

  (function copy() {
    if (!navigator.clipboard) return;
    all('.case-main pre').forEach(function (block) {
      var holder = document.createElement('div');
      holder.className = 'code';
      block.parentNode.insertBefore(holder, block);
      holder.appendChild(block);
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy';
      button.textContent = 'Copy';
      holder.appendChild(button);
      button.addEventListener('click', function () {
        navigator.clipboard.writeText(block.textContent).then(function () {
          button.textContent = 'Copied';
          setTimeout(function () {
            button.textContent = 'Copy';
          }, 1600);
        });
      });
    });
  })();

  // ---- Monitoring chart: choose a month, or replay the year ----------------

  (function monitor() {
    var figure = document.querySelector('[data-monitor]');
    if (!figure) return;
    var data = JSON.parse(figure.querySelector('[data-monitor-data]').textContent);
    var months = all('.month', figure);
    var detail = figure.querySelector('[data-detail]');
    var replay = figure.querySelector('[data-replay]');
    var fields = {};
    all('[data-f]', detail).forEach(function (element) {
      fields[element.dataset.f] = element;
    });
    var timer = null;
    var selected = -1;

    function select(index) {
      if (index === selected) return;
      selected = index;
      var entry = data[index];
      months.forEach(function (month, i) {
        month.setAttribute('aria-pressed', i === index ? 'true' : 'false');
      });
      fields.pill.className = 'pill s-' + entry.status;
      ['statusLabel', 'name', 'note', 'auc', 'aucLabel', 'caught', 'psi', 'csi', 'feature'].forEach(
        function (key) {
          fields[key].textContent = entry[key];
        },
      );
      if (!reduced) {
        detail.classList.remove('swap');
        void detail.offsetWidth;
        detail.classList.add('swap');
      }
    }

    function stop() {
      if (timer === null) return;
      clearInterval(timer);
      timer = null;
      replay.textContent = 'Replay the year';
      detail.setAttribute('aria-live', 'polite');
    }

    months.forEach(function (month, index) {
      if (month.getAttribute('aria-pressed') === 'true') selected = index;
      month.addEventListener('click', function () {
        stop();
        select(index);
      });
      if (finePointer) {
        month.addEventListener('pointerenter', function () {
          if (timer === null) select(index);
        });
      }
      month.addEventListener('keydown', function (event) {
        var step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
        if (!step) return;
        event.preventDefault();
        stop();
        var next = Math.max(0, Math.min(months.length - 1, index + step));
        select(next);
        months[next].focus();
      });
    });

    replay.hidden = false;
    replay.addEventListener('click', function () {
      if (timer !== null) {
        stop();
        return;
      }
      var index = 0;
      replay.textContent = 'Stop';
      detail.setAttribute('aria-live', 'off');
      select(0);
      timer = setInterval(function () {
        index += 1;
        if (index >= months.length) {
          stop();
          return;
        }
        select(index);
      }, 900);
    });
  })();
})();
