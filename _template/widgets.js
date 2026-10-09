/* Interactive figures for this post. shared/widgets.js is loaded first and
   provides blog.pal, blog.fit, blog.slider, blog.presets, blog.readout,
   blog.redraw and blog.fmt. Replace the example with the post's own toys. */

/* ---------- Figure: spread of the mean of n draws ---------- */
blog.ready(function () {
  var cv = document.getElementById("toy-canvas");
  if (!cv) return;
  var REPS = 4000, LO = -3, HI = 3, BINS = 60;
  var n = blog.slider("toy-n", {
    map: function (v) { return Math.round(Math.pow(2, v)); },
    format: blog.int,
  });

  var draw = blog.redraw(function () {
    var P = blog.pal(), f = blog.fit(cv), c = f.c, w = f.w, h = f.h;
    var N = n.value, r = blog.rng(7), means = new Float64Array(REPS), s1 = 0, s2 = 0;
    for (var i = 0; i < REPS; i++) {
      var s = 0;
      for (var j = 0; j < N; j++) s += blog.gauss(r);
      means[i] = s / N;
      s1 += means[i];
      s2 += means[i] * means[i];
    }
    var sd = Math.sqrt((s2 - s1 * s1 / REPS) / (REPS - 1));

    var counts = new Array(BINS).fill(0), bw = (HI - LO) / BINS;
    for (var k = 0; k < REPS; k++) {
      var b = Math.floor((means[k] - LO) / bw);
      if (b >= 0 && b < BINS) counts[b]++;
    }
    var pad = { l: 8, r: 8, t: 22, b: 26 };
    var X = function (x) { return pad.l + (x - LO) / (HI - LO) * (w - pad.l - pad.r); };
    var dens = function (count) { return count / (REPS * bw); };
    var top = 1.15 * Math.max(Math.sqrt(N / (2 * Math.PI)), dens(Math.max.apply(null, counts)));
    var Y = function (d) { return h - pad.b - d / top * (h - pad.t - pad.b); };

    c.fillStyle = P.teal;
    c.globalAlpha = 0.55;
    for (var q = 0; q < BINS; q++) {
      var x0 = X(LO + q * bw), x1 = X(LO + (q + 1) * bw);
      c.fillRect(x0, Y(dens(counts[q])), Math.max(1, x1 - x0 - 1), Y(0) - Y(dens(counts[q])));
    }
    c.globalAlpha = 1;

    c.strokeStyle = P.orange;
    c.lineWidth = 2;
    c.beginPath();
    for (var t = 0; t <= 200; t++) {
      var x = LO + t / 200 * (HI - LO), d = Math.sqrt(N / (2 * Math.PI)) * Math.exp(-N * x * x / 2);
      t ? c.lineTo(X(x), Y(d)) : c.moveTo(X(x), Y(d));
    }
    c.stroke();

    c.strokeStyle = P.line;
    c.lineWidth = 1;
    c.beginPath();
    c.moveTo(pad.l, Y(0));
    c.lineTo(w - pad.r, Y(0));
    c.stroke();
    c.fillStyle = P.muted;
    c.textAlign = "center";
    [-3, -2, -1, 0, 1, 2, 3].forEach(function (v) { c.fillText(blog.fmt(v, 0), X(v), h - 8); });
    c.textAlign = "left";
    c.fillText("means of n draws", pad.l, 14);
    c.fillStyle = P.orange;
    c.textAlign = "right";
    c.fillText("normal, sd 1/√n", w - pad.r, 14);
    c.textAlign = "left";

    blog.readout("toy-readout",
      "n = <b>" + blog.int(N) + "</b> draws per mean, " + blog.int(REPS) + " means.<br>" +
      "Measured spread: <b>" + blog.fmt(sd, 3) + "</b>.<br>" +
      "Prediction 1/√n: <b>" + blog.fmt(1 / Math.sqrt(N), 3) + "</b>.");
  });

  n.onInput(draw);
  blog.presets("toy-presets", {
    "n = 1": function () { n.set(0); },
    "n = 4": function () { n.set(2); },
    "n = 16": function () { n.set(4); },
    "n = 64": function () { n.set(6); },
  });
});
