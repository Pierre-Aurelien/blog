/* Page behaviour for the blog components. Loaded in <head> on every page.
   - Theme: follow prefers-color-scheme unless <html data-theme> is set; the
     navbar switch sets it and remembers the choice. Widgets redraw on the
     "blog:theme" event.
   - Folds: "Unfold all" / "Fold all", open the fold that holds a linked
     anchor, and let widgets re-measure when a fold opens. */
(function () {
  var root = document.documentElement;
  var KEY = "blog-theme";
  var dark = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function apply(mode) {
    if (mode === "light" || mode === "dark") root.setAttribute("data-theme", mode);
    else root.removeAttribute("data-theme");
    window.dispatchEvent(new Event("blog:theme"));
  }
  // Before first paint, so a remembered choice does not flash.
  var initial = stored();
  if (initial === "light" || initial === "dark") root.setAttribute("data-theme", initial);
  if (dark && dark.addEventListener) {
    dark.addEventListener("change", function () { window.dispatchEvent(new Event("blog:theme")); });
  }
  // A page can also be switched from outside (an embedding viewer, a test).
  new MutationObserver(function () { window.dispatchEvent(new Event("blog:theme")); })
    .observe(root, { attributes: true, attributeFilter: ["data-theme"] });

  function themeButton() {
    var host = document.querySelector(".quarto-navbar-tools") || document.querySelector("#navbarCollapse");
    if (!host || document.getElementById("blog-theme-toggle")) return;
    var order = ["auto", "light", "dark"];
    var b = document.createElement("button");
    b.type = "button";
    b.id = "blog-theme-toggle";
    b.className = "quarto-navigation-tool px-1 blog-theme-toggle";
    function current() {
      var t = root.getAttribute("data-theme");
      return t === "light" || t === "dark" ? t : "auto";
    }
    function label() {
      var mode = current();
      b.innerHTML = '<i class="bi bi-' + (mode === "auto" ? "circle-half" : mode === "dark" ? "moon" : "sun") + '"></i>';
      b.setAttribute("aria-label", "Colour theme: " + mode + ". Switch theme.");
      b.title = "Theme: " + mode;
    }
    b.addEventListener("click", function () {
      var next = order[(order.indexOf(current()) + 1) % order.length];
      try {
        if (next === "auto") localStorage.removeItem(KEY); else localStorage.setItem(KEY, next);
      } catch (e) {}
      apply(next);
      label();
    });
    label();
    host.appendChild(b);
  }

  function folds() {
    var all = function () {
      return Array.prototype.slice.call(document.querySelectorAll("details.tog, details.code-fold"));
    };
    Array.prototype.forEach.call(document.querySelectorAll("[data-fold]"), function (b) {
      b.addEventListener("click", function () {
        var open = b.getAttribute("data-fold") === "open";
        all().forEach(function (d) { d.open = open; });
      });
    });
    var t;
    document.addEventListener("toggle", function (e) {
      var d = e.target;
      if (d && d.tagName === "DETAILS" && d.open) {
        clearTimeout(t);
        t = setTimeout(function () { window.dispatchEvent(new Event("resize")); }, 40);
      }
    }, true);
    function reveal() {
      var id = "";
      try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) {}
      if (!id) return;
      var el = document.getElementById(id);
      for (var d = el && el.closest("details"); d; d = d.parentElement ? d.parentElement.closest("details") : null) d.open = true;
    }
    window.addEventListener("hashchange", reveal);
    reveal();
  }

  // "Figure 1:" in bold ink at the start of a caption, as in the legacy posts.
  function captions() {
    Array.prototype.forEach.call(document.querySelectorAll("figcaption.quarto-float-caption"), function (fc) {
      var t = fc.firstChild;
      while (t && t.nodeType === 3 && !t.textContent.trim()) t = t.nextSibling;
      if (!t || t.nodeType !== 3) return;
      var m = /^\s*((?:Figure|Table|Listing)\s+[\w.]+:)\s*/.exec(t.textContent);
      if (!m) return;
      var b = document.createElement("b");
      b.textContent = m[1];
      t.textContent = " " + t.textContent.slice(m[0].length);
      fc.insertBefore(b, t);
    });
  }

  function init() { themeButton(); folds(); captions(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
