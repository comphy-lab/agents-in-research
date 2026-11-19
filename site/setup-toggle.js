/*
 * Human/agent switch for the setup section, and copy buttons.
 *
 * Without JavaScript both setup versions stay visible one after the other and
 * the switch and copy buttons stay hidden. With it, the switch becomes an ARIA
 * tablist (arrow keys, Home, End) and shows one version at a time. The link
 * #setup-agent opens the agent version. No storage is used.
 */
(function () {
  'use strict';

  function initTabs(list) {
    var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
    var panels = tabs.map(function (tab) {
      return document.getElementById(tab.getAttribute('aria-controls'));
    });
    if (!tabs.length || panels.some(function (p) { return !p; })) {
      return;
    }

    function select(index, focus) {
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.setAttribute('aria-selected', on ? 'true' : 'false');
        tab.tabIndex = on ? 0 : -1;
        panels[i].hidden = !on;
      });
      if (focus) {
        tabs[index].focus();
      }
    }

    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { select(i, false); });
      tab.addEventListener('keydown', function (event) {
        var next = null;
        if (event.key === 'ArrowRight') { next = (i + 1) % tabs.length; }
        else if (event.key === 'ArrowLeft') { next = (i - 1 + tabs.length) % tabs.length; }
        else if (event.key === 'Home') { next = 0; }
        else if (event.key === 'End') { next = tabs.length - 1; }
        if (next !== null) {
          event.preventDefault();
          select(next, true);
        }
      });
    });

    function fromHash() {
      var hash = window.location.hash.slice(1);
      var index = panels.findIndex(function (p) { return p.id === hash; });
      if (index >= 0) {
        select(index, false);
        panels[index].scrollIntoView();
      }
    }

    // A panel starts with prose, so make it focusable: Tab from the tab
    // then lands on the start of the instructions (WAI-ARIA tabs pattern).
    panels.forEach(function (panel) { panel.tabIndex = 0; });
    list.hidden = false;
    list.parentNode.classList.add('has-mode-switch');
    var initial = panels.findIndex(function (p) { return p.id === window.location.hash.slice(1); });
    select(initial >= 0 ? initial : 0, false);
    window.addEventListener('hashchange', fromHash);
  }

  function initCopy(button) {
    var target = document.getElementById(button.getAttribute('data-copy-target'));
    if (!target || !navigator.clipboard || !window.isSecureContext) {
      return;
    }
    var label = button.textContent;
    var status = document.getElementById(button.getAttribute('data-copy-status'));
    var timer = null;
    button.hidden = false;
    button.addEventListener('click', function () {
      navigator.clipboard.writeText(target.textContent).then(function () {
        button.textContent = 'Copied';
        if (status) { status.textContent = 'Prompt copied to the clipboard.'; }
      }, function () {
        button.textContent = 'Copy failed';
        if (status) { status.textContent = 'Copy failed. Select the prompt text and copy it by hand.'; }
      }).then(function () {
        window.clearTimeout(timer);
        timer = window.setTimeout(function () { button.textContent = label; }, 2500);
      });
    });
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll('.mode-switch[role="tablist"]'), initTabs);
    Array.prototype.forEach.call(document.querySelectorAll('[data-copy-target]'), initCopy);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());
