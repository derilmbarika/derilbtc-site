/* DerilBTC motion + live ticker. Progressive enhancement only: without JS
   or with reduced motion the pages are fully readable static documents. */
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ── live BTC/USDT ticker (client-side, no key) ──────────────────────────
  var tb = document.getElementById("t-btc");
  var tu = document.getElementById("t-usdt");
  if (tb && tu) {
    fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,tether&vs_currencies=usd")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.bitcoin) tb.textContent = "$" + Math.round(d.bitcoin.usd).toLocaleString("en-US");
        if (d.tether) tu.textContent = "$" + d.tether.usd.toFixed(2);
      })
      .catch(function () {
        tb.textContent = "live on WhatsApp";
        tu.textContent = "live on WhatsApp";
      });
  }

  // ── rotating service line in the hero ───────────────────────────────────
  var items = document.querySelectorAll(".rot-item");
  if (items.length && !reduce) {
    var i = 0;
    items[0].classList.add("on");
    setInterval(function () {
      items[i].classList.remove("on");
      i = (i + 1) % items.length;
      items[i].classList.add("on");
    }, 2600);
  } else if (items.length) {
    items[0].classList.add("on");
  }

  // ── GSAP reveals ─────────────────────────────────────────────────────────
  if (reduce || typeof gsap === "undefined") return;
  gsap.registerPlugin(ScrollTrigger);
  window.addEventListener("load", function () { ScrollTrigger.refresh(); });

  gsap.from(".hero h1 .line > span", {
    yPercent: 112, duration: 1.0, ease: "power4.out", stagger: 0.09, delay: 0.1
  });
  gsap.from(".hero-sub, .hero .rotator, .hero .btn-lg, .ticker", {
    opacity: 0, y: 16, duration: 0.8, ease: "power3.out", stagger: 0.08, delay: 0.4
  });

  gsap.utils.toArray("[data-reveal], .steps-wrap h2, .services h2, .cta-band h2").forEach(function (el) {
    gsap.from(el, {
      opacity: 0, y: 22, duration: 0.7, ease: "power3.out",
      scrollTrigger: { trigger: el, start: "top 88%", once: true }
    });
  });
  ScrollTrigger.batch(".svc, .step", {
    start: "top 92%", once: true,
    onEnter: function (batch) {
      gsap.from(batch, { opacity: 0, y: 22, duration: 0.6, ease: "power3.out", stagger: 0.06 });
    }
  });
})();
