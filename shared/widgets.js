/* Shared helpers for interactive figures, loaded before a post's own
   widgets.js (components.lua adds both when the post has a widgets.js).

   A post's widgets.js looks like:

     blog.ready(function () {
       var n = blog.slider("n", { map: function (v) { return Math.round(Math.pow(2, v)); }, format: blog.int });
       var draw = blog.redraw(function () {
         var P = blog.pal(), f = blog.fit(document.getElementById("cv"));
         ...                                   // draw with P.ink, P.teal, ...
         blog.readout("ro", "n = <b>" + blog.int(n.value) + "</b>");
       });
       n.onInput(draw);
       blog.presets("presets", { "n = 4": function () { n.set(2); } }, draw);
     });
*/
(function (global) {
  "use strict";
  var blog = global.blog = global.blog || {};

  blog.FONT = '"IBM Plex Sans", system-ui, sans-serif';

  /* Colours of the current theme, read from the CSS tokens at draw time. */
  blog.pal = function () {
    var s = getComputedStyle(document.documentElement);
    var g = function (n) { return s.getPropertyValue(n).trim(); };
    return {
      bg: g("--bg"), ink: g("--ink"), muted: g("--muted"), line: g("--line"), panel: g("--panel"),
      teal: g("--teal"), orange: g("--orange"), wine: g("--wine"),
    };
  };

  /* Size a canvas to its CSS width at the device pixel ratio. The drawing
     height is the canvas's height attribute, kept in data-h. Returns the
     2-D context, cleared, in CSS pixels. */
  blog.fit = function (cv) {
    var dpr = window.devicePixelRatio || 1;
    var w = cv.clientWidth || 300;
    var h = +cv.getAttribute("data-h") || +cv.getAttribute("height") || 300;
    cv.setAttribute("data-h", h);
    cv.style.height = h + "px";
    cv.width = Math.round(w * dpr);
    cv.height = Math.round(h * dpr);
    var c = cv.getContext("2d");
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    c.clearRect(0, 0, w, h);
    c.font = "13px " + blog.FONT;
    return { c: c, w: w, h: h };
  };

  /* Numbers. A real minus sign, a fixed number of decimals, thin spaces
     between thousands; NaN and infinities spelled out. */
  var MINUS = "−", THIN = " ";
  function group(s) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, THIN); }
  blog.fmt = function (x, digits) {
    if (digits === undefined) digits = 2;
    if (x === null || x === undefined || Number.isNaN(x)) return "n/a";
    if (!Number.isFinite(x)) return (x < 0 ? MINUS : "") + "∞";
    var s = Math.abs(x).toFixed(digits).split(".");
    var out = group(s[0]) + (s.length > 1 ? "." + s[1] : "");
    return (x < 0 && Number(out.replace(/\D/g, "")) !== 0 ? MINUS : "") + out;
  };
  blog.int = function (x) { return blog.fmt(Math.round(x), 0); };
  blog.pct = function (x, digits) { return blog.fmt(100 * x, digits === undefined ? 1 : digits) + "%"; };
  /* n significant figures, switching to scientific notation outside [1e-3, 1e5). */
  blog.sig = function (x, n) {
    if (n === undefined) n = 3;
    if (x === 0 || !Number.isFinite(x)) return blog.fmt(x, 0);
    var a = Math.abs(x);
    if (a >= 1e-3 && a < 1e5) {
      var d = Math.max(0, n - 1 - Math.floor(Math.log10(a)));
      return blog.fmt(x, d);
    }
    var e = Math.floor(Math.log10(a)), m = x / Math.pow(10, e);
    return blog.fmt(m, n - 1) + "×10" + sup(e);
  };
  function sup(e) {
    var map = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
    return String(e).split("").map(function (ch) { return map[ch]; }).join("");
  }

  /* Wire a range input. `map` turns the slider position into the model value
     (e.g. a log scale), `format` writes it into the element with id
     `<id>-value` if there is one. Returns { value, set(position), onInput(fn) }. */
  blog.slider = function (id, opts) {
    opts = opts || {};
    var el = document.getElementById(id);
    if (!el) throw new Error("blog.slider: no element #" + id);
    var out = document.getElementById(id + "-value");
    var map = opts.map || Number;
    var format = opts.format || function (v) { return blog.fmt(v, 2); };
    var handlers = [];
    function read() { return map(+el.value); }
    function show() { if (out) out.textContent = format(read()); }
    el.addEventListener("input", function () {
      show();
      handlers.forEach(function (fn) { fn(read()); });
    });
    show();
    var api = {
      el: el,
      onInput: function (fn) { handlers.push(fn); return api; },
      set: function (position) {
        el.value = position;
        show();
        handlers.forEach(function (fn) { fn(read()); });
      },
    };
    Object.defineProperty(api, "value", { get: read });
    return api;
  };

  /* Preset buttons. `presets` maps a button label to a function that sets the
     sliders; the pressed button is marked with aria-pressed until a slider
     moves. Buttons are created inside the element with id `containerId`. */
  blog.presets = function (containerId, presets, after) {
    var box = document.getElementById(containerId);
    if (!box) throw new Error("blog.presets: no element #" + containerId);
    var buttons = [];
    Object.keys(presets).forEach(function (name) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = name;
      b.setAttribute("aria-pressed", "false");
      b.addEventListener("click", function () {
        presets[name]();
        buttons.forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
        if (after) after();
      });
      buttons.push(b);
      box.appendChild(b);
    });
    var fig = box.closest(".fig") || document;
    fig.addEventListener("input", function (e) {
      if (e.target && e.target.type === "range") buttons.forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
    });
    return buttons;
  };

  /* Write a readout. HTML is allowed so that numbers can be bold. */
  blog.readout = function (id, html) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = html;
  };

  /* Call draw now, and again on resize, on a theme change, and when a fold
     opens (a canvas inside a closed fold has no width). Returns a function
     that schedules a redraw, for use as a slider handler. */
  blog.redraw = function (draw) {
    var queued = false;
    function schedule() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; draw(); });
    }
    window.addEventListener("resize", schedule);
    window.addEventListener("blog:theme", schedule);
    draw();
    return schedule;
  };

  /* Run fn once the DOM is ready and the web fonts have loaded, so canvas
     text is measured in the right font. */
  blog.ready = function (fn) {
    function go() {
      var fonts = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
      fonts.then(fn);
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go);
    else go();
  };

  /* Seeded random numbers, for toys that must give the same picture every time
     (mulberry32, as in the legacy posts), and a standard normal draw. */
  blog.rng = function (seed) {
    var s = seed >>> 0;
    return function () {
      s |= 0; s = (s + 0x6D2B79F5) | 0;
      var t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  blog.gauss = function (r) {
    var u = 0;
    while (u === 0) u = r();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r());
  };
})(window);
