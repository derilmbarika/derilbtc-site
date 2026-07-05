/* DerilBTC motion + live data. Progressive enhancement only: without JS or
   with reduced motion the pages are fully readable static documents. */
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var FR = document.documentElement.lang === "fr";
  var ADMIN = (document.querySelector(".our-rates") || {}).dataset
    ? document.querySelector(".our-rates").dataset.admin : "";

  // ── hero mini ticker (BTC/USDT reference price) ─────────────────────────
  var tb = document.getElementById("t-btc");
  var tu = document.getElementById("t-usdt");

  // ── scrolling coin marquee: major coins, live, moves left to right ──────
  var track = document.getElementById("coin-track");
  var COINS = [
    ["bitcoin", "BTC"], ["ethereum", "ETH"], ["tether", "USDT"],
    ["binancecoin", "BNB"], ["solana", "SOL"], ["ripple", "XRP"],
    ["cardano", "ADA"], ["dogecoin", "DOGE"], ["tron", "TRX"], ["litecoin", "LTC"],
  ];
  if (track || (tb && tu)) {
    var ids = COINS.map(function (c) { return c[0]; }).join(",");
    fetch("https://api.coingecko.com/api/v3/simple/price?ids=" + ids + "&vs_currencies=usd&include_24hr_change=true")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (tb && d.bitcoin) tb.textContent = "$" + Math.round(d.bitcoin.usd).toLocaleString("en-US");
        if (tu && d.tether) tu.textContent = "$" + d.tether.usd.toFixed(2);
        if (!track) return;
        var items = COINS.map(function (c) {
          var coin = d[c[0]];
          if (!coin) return "";
          var price = coin.usd >= 100 ? Math.round(coin.usd).toLocaleString("en-US") : coin.usd.toFixed(2);
          var ch = coin.usd_24h_change || 0;
          var cls = ch >= 0 ? "up" : "dn";
          var arrow = ch >= 0 ? "▲" : "▼";
          return '<span class="ci"><b>' + c[1] + "</b> $" + price +
                 ' <i class="' + cls + '">' + arrow + " " + Math.abs(ch).toFixed(1) + "%</i></span>";
        }).join("");
        track.innerHTML = items + items; // duplicated for a seamless loop
        track.classList.add("run");
      })
      .catch(function () {
        if (tb) tb.textContent = FR ? "en direct sur WhatsApp" : "live on WhatsApp";
        if (tu) tu.textContent = "";
        if (track) track.parentElement.style.display = "none";
      });
  }

  // ── the desk's own buying rates (from the admin service) ────────────────
  var rb = document.getElementById("r-btc");
  var ru = document.getElementById("r-usdt");
  if (rb && ru) {
    var fallback = function () {
      var msg = FR ? "sur WhatsApp" : "on WhatsApp";
      rb.textContent = msg; ru.textContent = msg;
      document.querySelectorAll(".rate-tile b").forEach(function (b) { b.style.fontSize = "20px"; });
      document.querySelectorAll(".rate-tile small").forEach(function (s) { s.remove(); });
    };
    if (ADMIN) {
      fetch(ADMIN + "/api/rates")
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.btc_buy_xaf) return fallback();
          rb.textContent = Math.round(d.btc_buy_xaf).toLocaleString("en-US");
          ru.textContent = Math.round(d.usdt_buy_xaf).toLocaleString("en-US");
        })
        .catch(fallback);
    } else { fallback(); }
  }

  // ── newsletter signup ────────────────────────────────────────────────────
  var form = document.getElementById("nl-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var msg = document.getElementById("nl-msg");
      var email = form.email.value.trim();
      var done = function (ok) {
        msg.textContent = ok ? form.dataset.ok : form.dataset.err;
        msg.className = ok ? "ok" : "err";
        if (ok) form.reset();
      };
      if (!ADMIN) {
        // no backend yet: hand off to WhatsApp rates channel
        window.open("https://wa.me/237673259112?text=" + encodeURIComponent(
          (FR ? "Bonjour! Je veux recevoir le taux du jour. Mon email: " : "Hi! I want the daily rate. My email: ") + email
        ), "_blank");
        return done(true);
      }
      fetch(ADMIN + "/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, lang: form.dataset.lang, website: form.website.value }),
      })
        .then(function (r) { return r.json(); })
        .then(function (d) { done(!!d.ok); })
        .catch(function () { done(false); });
    });
  }

  // ── GSAP: reveals + the pinned "scroll stop" on the steps ────────────────
  if (reduce || typeof gsap === "undefined") return;
  gsap.registerPlugin(ScrollTrigger);
  window.addEventListener("load", function () { ScrollTrigger.refresh(); });

  gsap.from(".hero h1 .line > span", {
    yPercent: 112, duration: 1.0, ease: "power4.out", stagger: 0.09, delay: 0.1
  });
  gsap.from(".hero-sub, .hero .rotator, .hero .btn-lg, .ticker", {
    opacity: 0, y: 16, duration: 0.8, ease: "power3.out", stagger: 0.08, delay: 0.4
  });
  gsap.from(".hero-media img", {
    opacity: 0, y: 26, rotate: 3.5, duration: 1.1, ease: "power3.out", delay: 0.35
  });

  // rotating service line
  var items = document.querySelectorAll(".rot-item");
  if (items.length) {
    var i = 0;
    items[0].classList.add("on");
    setInterval(function () {
      items[i].classList.remove("on");
      i = (i + 1) % items.length;
      items[i].classList.add("on");
    }, 2600);
  }

  // scroll stop: pin the steps section while the three steps land in turn
  var stepsWrap = document.querySelector(".steps-wrap");
  if (stepsWrap && window.innerWidth > 960) {
    var steps = gsap.utils.toArray(".steps-wrap .step");
    gsap.set(steps, { opacity: 0, y: 46 });
    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stepsWrap,
        start: "top top",
        end: "+=" + (steps.length * 320),
        pin: true,
        scrub: 0.6,
      },
    });
    steps.forEach(function (s) {
      tl.to(s, { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" });
    });
  } else if (stepsWrap) {
    ScrollTrigger.batch(".steps-wrap .step", {
      start: "top 92%", once: true,
      onEnter: function (b) { gsap.from(b, { opacity: 0, y: 24, duration: 0.6, stagger: 0.08 }); },
    });
  }

  gsap.utils.toArray("[data-reveal], .services h2, .cta-band h2, .our-rates .rates-card, .newsletter").forEach(function (el) {
    gsap.from(el, {
      opacity: 0, y: 22, duration: 0.7, ease: "power3.out",
      scrollTrigger: { trigger: el, start: "top 88%", once: true }
    });
  });
  ScrollTrigger.batch(".svc", {
    start: "top 92%", once: true,
    onEnter: function (batch) {
      gsap.from(batch, { opacity: 0, y: 22, duration: 0.6, ease: "power3.out", stagger: 0.06 });
    }
  });
})();
