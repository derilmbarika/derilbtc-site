/* DerilBTC motion + live data. Progressive enhancement only: without JS or
   with reduced motion the pages are fully readable static documents. */
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var FR = document.documentElement.lang === "fr";
  var metaApi = document.querySelector('meta[name="api-base"]');
  var API = ((metaApi && metaApi.content) || "").replace(/\/+$/, "");

  // ── cookie-free pageview beacon (no personal data, first-party only) ─────
  if (API && navigator.sendBeacon) {
    try {
      var hit = JSON.stringify({
        path: location.pathname, ref: document.referrer || "",
        lang: document.documentElement.lang || "",
        device: window.innerWidth < 700 ? "mobile" : "desktop",
      });
      navigator.sendBeacon(API + "/api/hit", new Blob([hit], { type: "text/plain" }));
    } catch (e) {}
  }

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
    var renderCoins = function (d) {
      if (!d) throw new Error("no data");
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
    };
    var directCoins = function () {
      var ids = COINS.map(function (c) { return c[0]; }).join(",");
      return fetch("https://api.coingecko.com/api/v3/simple/price?ids=" + ids + "&vs_currencies=usd&include_24hr_change=true")
        .then(function (r) { return r.json(); });
    };
    // Prefer the desk's cached market endpoint (fast, rate-limit-proof); fall
    // back to CoinGecko directly if the portal is unreachable.
    var viaApi = API
      ? fetch(API + "/api/market").then(function (r) { return r.json(); }).then(function (m) { return m && m.coins ? m.coins : null; })
      : Promise.resolve(null);
    viaApi.then(function (coins) { return coins || directCoins(); })
      .then(renderCoins)
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
    if (API) {
      fetch(API + "/api/rates")
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
      if (!API) {
        // no backend: hand off to WhatsApp rates channel
        window.open("https://wa.me/237673259112?text=" + encodeURIComponent(
          (FR ? "Bonjour! Je veux recevoir le taux du jour. Mon email: " : "Hi! I want the daily rate. My email: ") + email
        ), "_blank");
        return done(true);
      }
      fetch(API + "/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, lang: form.dataset.lang, website: form.website.value }),
      })
        .then(function (r) { return r.json(); })
        .then(function (d) { done(!!d.ok); })
        .catch(function () { done(false); });
    });
  }

  // ── lead / order forms: post to the desk, fall back to WhatsApp ──────────
  [].forEach.call(document.querySelectorAll(".lead-form"), function (lf) {
    lf.addEventListener("submit", function (e) {
      e.preventDefault();
      var msg = lf.querySelector(".lead-msg");
      var val = function (n) { var el = lf.elements[n]; return el ? (el.value || "").trim() : ""; };
      if (val("website")) return; // honeypot
      var name = val("name"), whatsapp = val("whatsapp");
      if (!name || !whatsapp) { msg.textContent = lf.dataset.err; msg.className = "lead-msg err"; return; }
      // compose the service-specific answers into one readable line for the desk
      var skip = { name: 1, whatsapp: 1, email: 1, website: 1, amount: 1, message: 1, service: 1 };
      var details = [];
      [].forEach.call(lf.elements, function (el) {
        if (!el.name || !el.dataset || !el.dataset.label || skip[el.name]) return;
        var v = (el.value || "").trim();
        if (v) details.push(el.dataset.label + ": " + v);
      });
      var note = val("message");
      if (note) details.push("Note: " + note);
      var payload = {
        type: "quote", name: name, whatsapp: whatsapp, email: val("email"),
        amount: val("amount"), message: details.join("  ·  "),
        service: val("service") || lf.dataset.service || "", page: location.pathname,
        lang: lf.dataset.lang || (FR ? "fr" : "en"), website: "",
      };
      var okMsg = function () { msg.textContent = lf.dataset.ok; msg.className = "lead-msg ok"; lf.reset(); };
      if (!API) { // no backend: hand off to WhatsApp with the details prefilled
        var text = (FR ? "Bonjour DerilBTC! " : "Hi DerilBTC! ") + name + " - " +
          (payload.service ? payload.service + " - " : "") + (payload.amount || "") +
          (payload.message ? " - " + payload.message : "");
        window.open("https://wa.me/237673259112?text=" + encodeURIComponent(text), "_blank");
        return okMsg();
      }
      lf.classList.add("busy");
      msg.textContent = lf.dataset.sending; msg.className = "lead-msg";
      fetch(API + "/api/leads", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          lf.classList.remove("busy");
          if (d && d.ok) okMsg();
          else { msg.textContent = lf.dataset.err; msg.className = "lead-msg err"; }
        })
        .catch(function () { lf.classList.remove("busy"); msg.textContent = lf.dataset.err; msg.className = "lead-msg err"; });
    });
  });

  // ── hide the floating WhatsApp button while an order form is on screen ────
  var sticky = document.querySelector(".sticky-cta");
  var leadSection = document.querySelector(".lead");
  if (sticky && leadSection && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      sticky.classList.toggle("hide", entries[0].isIntersecting);
    }, { rootMargin: "-25% 0px -25% 0px" }).observe(leadSection);
  }

  // ── GSAP: reveals + the pinned "scroll stop" on the steps ────────────────
  if (reduce || typeof gsap === "undefined") return;
  gsap.registerPlugin(ScrollTrigger);
  window.addEventListener("load", function () { ScrollTrigger.refresh(); });

  function playHeroIntro() {
    gsap.from(".hero h1 .line > span", {
      yPercent: 112, duration: 1.0, ease: "power4.out", stagger: 0.09, delay: 0.1
    });
    gsap.from(".hero-sub, .hero .rotator, .hero .btn-lg, .ticker", {
      opacity: 0, y: 16, duration: 0.8, ease: "power3.out", stagger: 0.08, delay: 0.4
    });
    gsap.from(".hero-media img", {
      opacity: 0, y: 26, rotate: 3.5, duration: 1.1, ease: "power3.out", delay: 0.35
    });
  }
  // Only run the intro when the tab is actually visible. In a background tab
  // requestAnimationFrame is paused, so gsap.from() would apply the hidden
  // start state and never tick forward, leaving the hero blank. Deferring to
  // the first "visible" keeps the headline readable no matter how the page is
  // opened. With no JS / no GSAP the hero is already visible (CSS default).
  if (document.visibilityState === "visible") {
    playHeroIntro();
  } else {
    document.addEventListener("visibilitychange", function onVisible() {
      if (document.visibilityState === "visible") {
        document.removeEventListener("visibilitychange", onVisible);
        playHeroIntro();
      }
    });
  }

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

  // WWD "scroll stop": pin the What-we-do stage while the 8 numbered panels
  // cross-fade in sequence, with the progress bar tracking (1-1 from the
  // original site's pinned wwd-stage).
  var stage = document.querySelector(".wwd-stage");
  if (stage) {
    var mm = gsap.matchMedia();
    mm.add("(min-width: 961px)", function () {
      // Mark the stage as pin-driven only now that GSAP is confirmed present.
      // The CSS keys the overlay/hidden panel state off .js-pin, so if GSAP is
      // ever blocked or fails to load the panels stay stacked and readable.
      stage.classList.add("js-pin");
      var panels = gsap.utils.toArray(".wwd-panel");
      var bar = document.getElementById("wwd-bar");
      var per = 620; // scroll px per panel
      var tl = gsap.timeline({
        scrollTrigger: {
          trigger: stage,
          start: "top top",
          end: "+=" + (panels.length * per),
          pin: true,
          scrub: 0.5,
        },
      });
      panels.forEach(function (p, i) {
        if (i === 0) return;
        tl.to(panels[i - 1], { opacity: 0, y: -26, duration: 0.45, ease: "power2.in", pointerEvents: "none" }, i)
          .fromTo(p, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.45, ease: "power2.out", pointerEvents: "auto" }, i + 0.4);
      });
      if (bar) tl.to(bar, { width: "100%", ease: "none", duration: panels.length }, 0);
      return function () { stage.classList.remove("js-pin"); };
    });
  }

  // steps: simple staggered reveal
  ScrollTrigger.batch(".steps-wrap .step", {
    start: "top 92%", once: true,
    onEnter: function (b) { gsap.from(b, { opacity: 0, y: 24, duration: 0.6, stagger: 0.08 }); },
  });

  // stats: count-up when the band enters
  gsap.utils.toArray(".stat b[data-count]").forEach(function (el) {
    var target = parseInt(el.dataset.count, 10);
    var o = { v: 0 };
    gsap.to(o, {
      v: target, duration: 1.6, ease: "power2.out",
      scrollTrigger: { trigger: el, start: "top 90%", once: true },
      onUpdate: function () { el.textContent = Math.round(o.v).toLocaleString("en-US"); },
    });
  });

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
