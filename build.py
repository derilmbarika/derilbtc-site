#!/usr/bin/env python3
"""Static site generator for derilbtc.com.
Reads content/raw_pages.json (WP REST dump), extracts clean content blocks
from the Elementor HTML, and renders every page through a shared dark/premium
template into dist/ with slugs preserved 1:1. Home pages are custom-composed;
all other pages use the editorial service template.
"""
import json, os, re, html as H
from html.parser import HTMLParser
from pathlib import Path

# PREVIEW=1 builds a noindexed staging copy (for preview.derilbtc.com);
# the production build (no flag) is index, follow with real canonicals.
PREVIEW = os.environ.get("PREVIEW") == "1"

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
RAW = json.load(open(ROOT / "content" / "raw_pages.json"))
# 1-1 structure extracted from the original homepage (panels, hero, CTAs).
HOME_STRUCT = json.load(open(ROOT / "content" / "home_structure.json"))

WA = "https://wa.me/237673259112"
# The derilbtc-admin service (Railway). Set once deployed; empty = the
# rates card and newsletter fall back to WhatsApp and LOGIN is hidden.
ADMIN_URL = os.environ.get("ADMIN_URL", "")

# EN slug -> FR slug (and the reverse is derived). Home pages handled apart.
LANG_MAP = {
    "buy-bitcoin-cameroon": "acheter-bitcoin-cameroun",
    "buy-usdt-cameroon": "acheter-usdt-cameroun",
    "pay-china-suppliers": "payer-fournisseur-chine",
    "pay-school-fees-abroad": "frais-de-scolarite-etranger",
    "book-flights": "reserver-vol",
    "rates": "taux",
    "safety": "securite",
    "about": "a-propos",
    "faq": "faq-2",
    "sell-gift-cards-cameroon": "vendre-cartes-cadeaux-cameroun",
    "naira-to-cfa-cameroon": "naira-en-fcfa-cameroun",
    "momo-scams-cameroon": "arnaques-momo-cameroun",
    "refer": "referer",
    "free-bitcoin-mentorship-cameroon": "mentorat-bitcoin-cameroun",
    "home": "derilbtc-accueil",
}
FR_TO_EN = {v: k for k, v in LANG_MAP.items()}

NAV = {
    "en": [("buy-bitcoin-cameroon", "Buy Bitcoin"), ("buy-usdt-cameroon", "USDT"),
            ("pay-china-suppliers", "China Payments"), ("rates", "Rates"),
            ("faq", "FAQ"), ("about", "About")],
    "fr": [("acheter-bitcoin-cameroun", "Acheter Bitcoin"), ("acheter-usdt-cameroun", "USDT"),
            ("payer-fournisseur-chine", "Paiements Chine"), ("taux", "Taux"),
            ("faq-2", "FAQ"), ("a-propos", "À propos")],
}

UI = {
    "en": {"cta": "Trade on WhatsApp", "home": "/", "tagline": "Cameroon's trusted crypto desk since 2018.",
            "footer_note": "Rates quoted live on WhatsApp. MoMo, Orange Money and bank transfers.",
            "switch": "FR", "login": "Login", "sticky": "Trade on WhatsApp"},
    "fr": {"cta": "Trader sur WhatsApp", "home": "/derilbtc-accueil/", "tagline": "Le bureau crypto de confiance du Cameroun depuis 2018.",
            "footer_note": "Taux communiqués en direct sur WhatsApp. MoMo, Orange Money et virements bancaires.",
            "switch": "EN", "login": "Login", "sticky": "Trader sur WhatsApp"},
}

# ── Elementor content extraction ────────────────────────────────────────────
class Extract(HTMLParser):
    """Walks rendered WP HTML, keeps meaningful blocks in document order."""
    KEEP = {"h1", "h2", "h3", "h4", "p", "li", "td", "th", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self._stack, self._buf = [], [], []
        self._href = None
        self._list_mode = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("ul", "ol"):
            self._list_mode = tag
            self.blocks.append([tag, []])
        if tag in self.KEEP:
            self._stack.append(tag)
            self._buf = []
        if tag == "img" and not self._stack:
            # inline content image (e.g. the mentorship founder photos):
            # keep it, remapped to the self-hosted copy.
            src = a.get("href") or a.get("src") or ""
            local = {"deril-2018-rotated.jpg": "deril-2018.jpg",
                     "deril-today-rotated.jpg": "deril-today.jpg"}.get(src.split("/")[-1], src.split("/")[-1])
            if src:
                self.blocks.append(["img", (f"/assets/img/{local}", a.get("alt", ""))])
        if tag == "a":
            href = a.get("href", "") or ""
            cls = a.get("class", "") or ""
            if self._stack:
                # inline link inside a kept block: preserve it
                if href and not href.startswith("#"):
                    ext = ' target="_blank" rel="noopener"' if href.startswith("http") and "derilbtc.com" not in href else ""
                    href = re.sub(r"^https?://(www\.)?derilbtc\.com", "", href)  # internal links stay relative
                    self._buf.append(f'<a href="{href}"{ext}>')
                    self._open_a = True
            elif ("button" in cls or "wa.me" in href) and href:
                # standalone CTA (Elementor button or bare WhatsApp link)
                self._pending_btn = href
                self._stack.append("btn")
                self._buf = []

    def handle_endtag(self, tag):
        if not self._stack:
            return
        if tag == "a" and getattr(self, "_open_a", False):
            self._buf.append("</a>")
            self._open_a = False
            return
        cur = self._stack[-1]
        if tag == cur or (cur == "btn" and tag == "a"):
            self._stack.pop()
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if not text:
                return
            if cur == "li" and self.blocks and self.blocks[-1][0] in ("ul", "ol"):
                self.blocks[-1][1].append(text)
            elif cur == "btn":
                self.blocks.append(["btn", (getattr(self, "_pending_btn", WA), text)])
            elif cur in ("td", "th"):
                pass  # tables flattened out; rates live in the ticker now
            else:
                self.blocks.append([cur, text])

    def handle_data(self, data):
        if self._stack:
            self._buf.append(data)


def extract(html_src: str):
    src = re.sub(r"<style.*?</style>", "", html_src, flags=re.S)
    src = re.sub(r"<script.*?</script>", "", src, flags=re.S)
    # house style: no long typographic dashes anywhere (raw + entity forms)
    for bad in ("—", "&mdash;", "&#8212;", "&#x2014;"):
        src = src.replace(bad, " - ")
    for bad in ("–", "&ndash;", "&#8211;", "&#x2013;"):
        src = src.replace(bad, "-")
    src = src.replace("  ", " ")
    p = Extract()
    p.feed(src)
    # de-duplicate consecutive identical blocks (Elementor repeats for mobile)
    out, seen_prev = [], None
    for b in p.blocks:
        key = json.dumps(b, ensure_ascii=False)
        if key != seen_prev:
            out.append(b)
        seen_prev = key
    return [b for b in out if not _is_widget_artifact(b)]


# Copy that belonged to the old page's embedded form / JS price-converter
# widgets. The widgets themselves don't exist here, so their copy must go too.
_DROP_RX = re.compile(
    r"thank you! we|we.ve received your request|fill this in|by submitting"
    r"|loading price|use the quote form|quote form below"
    r"|merci ! nous|nous avons bien re|remplissez|en soumettant"
    r"|chargement du prix|formulaire de demande|formulaire ci-dessous"
    r"|xaf converter|convertisseur", re.I)

def _is_widget_artifact(b):
    if b[0] in ("ul", "ol"):
        return False
    text = b[1][1] if b[0] == "btn" else b[1]
    if not isinstance(text, str):
        return False
    return bool(_DROP_RX.search(re.sub(r"<[^>]+>", "", text)))


def footer_cols(lang):
    cols = []
    for heading, links in FOOTER[lang]:
        lis = "".join(f'<li><a href="/{slug}/">{label}</a></li>' for slug, label in links)
        cols.append(f"<div><h4>{heading}</h4><ul>{lis}</ul></div>")
    return "".join(cols)


# ── shared page shell ───────────────────────────────────────────────────────
def shell(lang, title, desc, canonical_path, alt_path, body, extra_head=""):
    ui = UI[lang]
    nav_links = "".join(
        f'<a href="/{slug}/">{label}</a>' for slug, label in NAV[lang])
    alt_lang = "fr" if lang == "en" else "en"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{H.escape(desc, quote=True)}">
{'<meta name="robots" content="noindex, nofollow">' if PREVIEW else '<meta name="robots" content="index, follow">'}
<link rel="canonical" href="https://derilbtc.com{canonical_path}">
<link rel="alternate" hreflang="{alt_lang}" href="https://derilbtc.com{alt_path}">
<link rel="alternate" hreflang="{lang}" href="https://derilbtc.com{canonical_path}">
<meta property="og:title" content="{H.escape(title, quote=True)}">
<meta property="og:description" content="{H.escape(desc, quote=True)}">
<meta property="og:type" content="website">
<link rel="icon" href="/assets/img/derilbtc-icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/derilbtc-icon-512.png">
<link rel="preload" href="/assets/fonts/space-grotesk-var-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/dist/tabler-icons.min.css">
<link rel="stylesheet" href="/assets/css/site.css">
{extra_head}
</head>
<body>
<header class="nav">
  <a class="nav-name" href="{ui['home']}"><img src="/assets/img/derilbtc-logo-light.png" alt="DerilBTC" height="34" width="145"></a>
  <nav class="nav-links" aria-label="Site">{nav_links}</nav>
  <div class="nav-side">
    {f'<a class="nav-login" href="{ADMIN_URL}/admin" target="_blank" rel="noopener">{ui["login"]}</a>' if ADMIN_URL else ''}
    <a class="nav-lang" href="{alt_path}">{ui['switch']}</a>
    <a class="nav-cta" href="{WA}" target="_blank" rel="noopener">{ui['cta']}</a>
  </div>
</header>
{body}
<footer class="footer">
  <div class="footer-grid">{footer_cols(lang)}</div>
  <div class="footer-base">
    <p><strong>DerilBTC</strong>. {ui['tagline']}</p>
    <p>{ui['footer_note']}</p>
    <p><a href="{WA}" target="_blank" rel="noopener">WhatsApp: +237 673 259 112</a> &nbsp;|&nbsp; <a href="mailto:info@derilbtc.com">info@derilbtc.com</a></p>
  </div>
</footer>
<a class="sticky-cta" href="{WA}" target="_blank" rel="noopener">{ui['sticky']}</a>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js" defer></script>
<script src="/assets/js/site.js" defer></script>
</body>
</html>"""


# ── editorial/service template ──────────────────────────────────────────────
def render_blocks(blocks, lang):
    out, h1_done = [], False
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            h1_done = True
            continue  # h1 rendered in the hero band
        if kind in ("h2", "h3", "h4"):
            out.append(f"<{kind}>{b[1]}</{kind}>")
        elif kind == "p":
            out.append(f"<p>{b[1]}</p>")
        elif kind == "blockquote":
            out.append(f"<blockquote>{b[1]}</blockquote>")
        elif kind in ("ul", "ol"):
            items = "".join(f"<li>{i}</li>" for i in b[1])
            out.append(f"<{kind}>{items}</{kind}>")
        elif kind == "btn":
            href, label = b[1]
            out.append(f'<a class="btn" href="{H.escape(href, quote=True)}" target="_blank" rel="noopener">{label}</a>')
        elif kind == "img":
            src, alt = b[1]
            out.append(f'<figure class="prose-img"><img src="{H.escape(src, quote=True)}" alt="{H.escape(alt, quote=True)}" loading="lazy"></figure>')
    return "\n".join(out)


def first_paragraph(blocks):
    for b in blocks:
        if b[0] == "p" and len(b[1]) > 60:
            return re.sub(r"<[^>]+>", "", b[1])[:158]
    return "DerilBTC: Cameroon's trusted desk for Bitcoin, USDT and cross-border payments. Fair rates, MoMo and bank payout."


def scrub(s: str) -> str:
    return s.replace("—", " - ").replace("–", "-").replace("  ", " ")


def page_html(slug, page, lang):
    blocks = extract(page["html"])
    title = scrub(H.unescape(page["title"]))
    h1 = next((b[1] for b in blocks if b[0] == "h1"), title)
    desc = first_paragraph(blocks)
    alt_slug = LANG_MAP.get(slug) or FR_TO_EN.get(slug)
    alt_path = f"/{alt_slug}/" if alt_slug else ("/" if lang == "fr" else "/derilbtc-accueil/")
    hero_img = PAGE_HERO.get(slug) or PAGE_HERO.get(FR_TO_EN.get(slug, ""), "derilbtc-hero.jpg")
    hero_style = f' style="background-image: linear-gradient(rgba(10,19,48,.82), rgba(10,19,48,.94)), url(/assets/img/{hero_img})"'
    body = f"""
<main>
  <section class="page-hero page-hero-img"{hero_style}>
    <h1>{h1}</h1>
  </section>
  <article class="prose" data-reveal>
    {render_blocks(blocks, lang)}
  </article>
</main>"""
    return shell(lang, f"{title} | DerilBTC", desc, f"/{slug}/", alt_path, body)


# ── homepage ────────────────────────────────────────────────────────────────
SERVICES = {
    "en": [
        ("buy-bitcoin-cameroon", "Buy & sell Bitcoin", "Fair public rate, paid to MoMo or bank in minutes.", "ti-currency-bitcoin"),
        ("buy-usdt-cameroon", "Buy & sell USDT", "Stable dollars for savings and payments.", "ti-currency-dollar"),
        ("pay-china-suppliers", "Pay China suppliers", "Alipay, WeChat and 1688, settled same day.", "ti-ship"),
        ("pay-school-fees-abroad", "Pay school fees abroad", "Canada, USA, France and beyond.", "ti-school"),
        ("book-flights", "Book flights", "International tickets paid from Cameroon.", "ti-plane-tilt"),
        ("sell-gift-cards-cameroon", "Sell gift cards", "iTunes, Amazon, Steam and more, for cash.", "ti-gift"),
        ("naira-to-cfa-cameroon", "Exchange Naira", "Naira to FCFA both ways, fast.", "ti-arrows-exchange"),
        ("momo-scams-cameroon", "Avoid MoMo scams", "Spot fraud before it costs you.", "ti-shield-check"),
    ],
    "fr": [
        ("acheter-bitcoin-cameroun", "Acheter et vendre du Bitcoin", "Taux public équitable, payé sur MoMo ou en banque en quelques minutes.", "ti-currency-bitcoin"),
        ("acheter-usdt-cameroun", "Acheter et vendre de l'USDT", "Des dollars stables pour épargner et payer.", "ti-currency-dollar"),
        ("payer-fournisseur-chine", "Payer un fournisseur en Chine", "Alipay, WeChat et 1688, réglés le jour même.", "ti-ship"),
        ("frais-de-scolarite-etranger", "Payer les frais de scolarité", "Canada, USA, France et au-delà.", "ti-school"),
        ("reserver-vol", "Réserver un vol", "Billets internationaux payés depuis le Cameroun.", "ti-plane-tilt"),
        ("vendre-cartes-cadeaux-cameroun", "Vendre des cartes-cadeaux", "iTunes, Amazon, Steam et plus, contre du cash.", "ti-gift"),
        ("naira-en-fcfa-cameroun", "Échanger des Naira", "Naira vers FCFA dans les deux sens, rapidement.", "ti-arrows-exchange"),
        ("arnaques-momo-cameroun", "Éviter les arnaques MoMo", "Repérez la fraude avant qu'elle ne vous coûte.", "ti-shield-check"),
    ],
}

# Per-page header art (real brand images pulled from the WP media library,
# self-hosted). FR pages inherit their EN twin's image via FR_TO_EN.
PAGE_HERO = {
    "buy-bitcoin-cameroon": "derilbtc-bitcoin-instant.jpg",
    "buy-usdt-cameroon": "derilbtc-usdt-instant.jpg",
    "pay-china-suppliers": "derilbtc-rmb.jpg",
    "pay-school-fees-abroad": "derilbtc-fees-flags.jpg",
    "book-flights": "derilbtc-flights-plane.jpg",
    "rates": "derilbtc-buysell.jpg",
    "safety": "derilbtc-safety.jpg",
    "about": "derilbtc-about.jpg",
    "faq": "derilbtc-hero.jpg",
    "sell-gift-cards-cameroon": "derilbtc-giftcards.jpg",
    "naira-to-cfa-cameroon": "derilbtc-naira.jpg",
    "momo-scams-cameroon": "derilbtc-momo-scams.jpg",
    "refer": "derilbtc-hero.jpg",
    "free-bitcoin-mentorship-cameroon": "derilbtc-buysell.jpg",
}

CARD_IMG = {
    "buy-bitcoin-cameroon": "deril-btc.jpg", "acheter-bitcoin-cameroun": "deril-btc.jpg",
    "buy-usdt-cameroon": "deril-usdt.jpg", "acheter-usdt-cameroun": "deril-usdt.jpg",
    "pay-china-suppliers": "deril-china.jpg", "payer-fournisseur-chine": "deril-china.jpg",
    "pay-school-fees-abroad": "deril-fees.jpg", "frais-de-scolarite-etranger": "deril-fees.jpg",
    "book-flights": "deril-flights.jpg", "reserver-vol": "deril-flights.jpg",
    "sell-gift-cards-cameroon": "deril-gift.jpg", "vendre-cartes-cadeaux-cameroun": "deril-gift.jpg",
    "naira-to-cfa-cameroon": "deril-naira.jpg", "naira-en-fcfa-cameroun": "deril-naira.jpg",
    "momo-scams-cameroon": "deril-scam.jpg", "arnaques-momo-cameroun": "deril-scam.jpg",
}

# Full footer directory: every real page, grouped, per language.
FOOTER = {
    "en": [
        ("Trade", [("buy-bitcoin-cameroon", "Buy & sell Bitcoin"), ("buy-usdt-cameroon", "Buy & sell USDT"),
                    ("naira-to-cfa-cameroon", "Naira to FCFA"), ("sell-gift-cards-cameroon", "Sell gift cards"),
                    ("rates", "Today's rates")]),
        ("Payments & travel", [("pay-china-suppliers", "Pay China suppliers"), ("pay-school-fees-abroad", "School fees abroad"),
                                ("book-flights", "Book flights")]),
        ("Learn & safety", [("safety", "Bitcoin scams guide"), ("momo-scams-cameroon", "MoMo scam guide"),
                             ("faq", "FAQ"), ("free-bitcoin-mentorship-cameroon", "1-on-1 mentorship")]),
        ("DerilBTC", [("about", "About us"), ("refer", "Refer & earn")]),
    ],
    "fr": [
        ("Trader", [("acheter-bitcoin-cameroun", "Acheter du Bitcoin"), ("acheter-usdt-cameroun", "Acheter de l'USDT"),
                     ("naira-en-fcfa-cameroun", "Naira en FCFA"), ("vendre-cartes-cadeaux-cameroun", "Vendre des cartes-cadeaux"),
                     ("taux", "Taux du jour")]),
        ("Paiements & voyage", [("payer-fournisseur-chine", "Payer un fournisseur en Chine"), ("frais-de-scolarite-etranger", "Frais de scolarité"),
                                 ("reserver-vol", "Réserver un vol")]),
        ("Guides & sécurité", [("securite", "Arnaques Bitcoin"), ("arnaques-momo-cameroun", "Arnaques MoMo"),
                                ("faq-2", "FAQ"), ("mentorat-bitcoin-cameroun", "Mentorat 1-à-1")]),
        ("DerilBTC", [("a-propos", "À propos"), ("referer", "Parrainer & gagner")]),
    ],
}

# WWD panels: EN comes 1-1 from the original page (home_structure.json);
# FR is a faithful translation (the original FR home was untranslated English).
WWD_FR = [
    {"kick": "Bitcoin", "h2": "Acheter et vendre du Bitcoin", "p": "Un taux public équitable, payé sur votre MoMo ou en banque en quelques minutes. Le bureau de confiance du Cameroun depuis 2018.", "cta_label": "Commencer à trader →", "cta_href": "/acheter-bitcoin-cameroun/", "img": "deril-btc.jpg"},
    {"kick": "Stablecoin", "h2": "Acheter et vendre de l'USDT", "p": "Des dollars qui ne bougent pas. Achetez ou vendez du Tether au taux du jour, réglé directement sur le mobile money.", "cta_label": "Acheter de l'USDT →", "cta_href": "/acheter-usdt-cameroun/", "img": "deril-usdt.jpg"},
    {"kick": "Imports", "h2": "Payer les fournisseurs en Chine", "p": "Payez les usines et les fournisseurs 1688/Alibaba en RMB, sans les délais bancaires. Votre marchandise part à temps.", "cta_label": "Payer un fournisseur →", "cta_href": "/payer-fournisseur-chine/", "img": "deril-china.jpg"},
    {"kick": "Éducation", "h2": "Payer les frais de scolarité à l'étranger", "p": "Frais de scolarité vers les USA, le Canada, le Royaume-Uni, la Chine et au-delà, payés correctement et à temps.", "cta_label": "Payer la scolarité →", "cta_href": "/frais-de-scolarite-etranger/", "img": "deril-fees.jpg"},
    {"kick": "Voyage", "h2": "Réserver des vols", "p": "Dites-nous où et quand. Nous trouvons et émettons le billet, vous payez en XAF. Pas besoin de carte.", "cta_label": "Réserver un vol →", "cta_href": "/reserver-vol/", "img": "deril-flights.jpg"},
    {"kick": "Cartes-cadeaux", "h2": "Vendre des cartes-cadeaux", "p": "Transformez iTunes, Amazon, Steam et plus en cash instantané sur MoMo, à des taux honnêtes.", "cta_label": "Vendre maintenant →", "cta_href": "/vendre-cartes-cadeaux-cameroun/", "img": "deril-gift.jpg"},
    {"kick": "Devises", "h2": "Échanger des Naira", "p": "Convertissez le Naira nigérian en CFA, USD ou USDT instantanément, avec un taux en direct que vous voyez.", "cta_label": "Échanger maintenant →", "cta_href": "/naira-en-fcfa-cameroun/", "img": "deril-naira.jpg"},
    {"kick": "Sécurité", "h2": "Éviter les arnaques MoMo", "p": "Connaissez les pièges avant qu'ils ne vous atteignent. Un guide gratuit pour trader et envoyer de l'argent en sécurité.", "cta_label": "Rester protégé →", "cta_href": "/arnaques-momo-cameroun/", "img": "deril-scam.jpg"},
]

STATS = {
    "en": {"eyebrow": "Why us", "h2": "A desk Cameroon already trusts.", "tiles": [
        {"b": "2018", "count": None, "s": "Trading since"},
        {"b": "300", "count": 300, "s": "clients on WhatsApp"},
        {"b": "Minutes", "count": None, "s": "not days, to get paid"},
        {"b": "8", "count": 8, "s": "services, one trusted desk"}]},
    "fr": {"eyebrow": "Pourquoi nous", "h2": "Un bureau auquel le Cameroun fait déjà confiance.", "tiles": [
        {"b": "2018", "count": None, "s": "En activité depuis"},
        {"b": "300", "count": 300, "s": "clients sur WhatsApp"},
        {"b": "Minutes", "count": None, "s": "pas des jours, pour être payé"},
        {"b": "8", "count": 8, "s": "services, un seul bureau"}]},
}

RATES_COPY = {
    "en": {"h": "We buy at premium rates.", "p": "These are our live buying rates, set by the desk and updated through the day. Lock yours on WhatsApp.",
            "btc": "We buy Bitcoin", "usdt": "We buy USDT", "per": "XAF per USD", "lock": "Lock this rate",
            "upd": "Updated"},
    "fr": {"h": "Nous achetons à des taux premium.", "p": "Voici nos taux d'achat en direct, fixés par le bureau et mis à jour dans la journée. Verrouillez le vôtre sur WhatsApp.",
            "btc": "Nous achetons le Bitcoin", "usdt": "Nous achetons l'USDT", "per": "XAF par USD", "lock": "Verrouiller ce taux",
            "upd": "Mis à jour"},
}

NEWS_COPY = {
    "en": {"h": "Get today's BTC rate every morning.", "p": "One short email with the day's rate. No spam, unsubscribe anytime.",
            "ph": "Your email address", "btn": "Subscribe", "ok": "You're in. Watch your inbox tomorrow morning.",
            "err": "That email doesn't look right. Try again."},
    "fr": {"h": "Recevez le taux BTC du jour chaque matin.", "p": "Un court email avec le taux du jour. Pas de spam, désinscription à tout moment.",
            "ph": "Votre adresse email", "btn": "S'abonner", "ok": "C'est fait. Surveillez votre boîte mail demain matin.",
            "err": "Cet email ne semble pas correct. Réessayez."},
}

HOME_COPY = {
    "en": {
        "h1a": "Your money,", "h1b": "moving at the speed of trust.",
        "sub": "Bitcoin, USDT and cross-border payments for Cameroon. Fair rates, MoMo or bank payout, on WhatsApp.",
        "services_h": "Everything the desk does",
        "trust_h": "A desk Cameroon already trusts.",
        "trust_p": "Since 2018 we have settled thousands of trades for students, importers and savers. No app, no account. You message, we quote, you get paid.",
        "steps_h": "Three steps. No app, no account.",
        "steps": [("Message us", "Say what you want to trade on WhatsApp."),
                   ("Lock your rate", "We quote a fair public rate and confirm."),
                   ("Get paid", "MoMo, Orange Money or bank, usually in minutes.")],
        "explore": "Explore services ↓",
        "cta_h": "Ready to move your money the smart way?",
        "cta_btn": "Trade on WhatsApp",
        "refer_h": "Invite a friend. You both get cash.",
        "refer_p": "Share your link, they trade, you both earn a bonus.",
        "refer_link": "refer",
        "refer_label": "How referrals work",
    },
    "fr": {
        "h1a": "Votre argent,", "h1b": "à la vitesse de la confiance.",
        "sub": "Bitcoin, USDT et paiements internationaux pour le Cameroun. Taux équitables, paiement MoMo ou banque, sur WhatsApp.",
        "services_h": "Tout ce que fait le bureau",
        "trust_h": "Un bureau auquel le Cameroun fait déjà confiance.",
        "trust_p": "Depuis 2018, nous avons réglé des milliers de transactions pour des étudiants, importateurs et épargnants. Pas d'application, pas de compte. Vous écrivez, nous cotons, vous êtes payé.",
        "steps_h": "Trois étapes. Sans application, sans compte.",
        "steps": [("Écrivez-nous", "Dites ce que vous voulez trader sur WhatsApp."),
                   ("Bloquez votre taux", "Nous cotons un taux public équitable et confirmons."),
                   ("Recevez l'argent", "MoMo, Orange Money ou banque, souvent en quelques minutes.")],
        "explore": "Découvrir les services ↓",
        "cta_h": "Prêt à déplacer votre argent intelligemment ?",
        "cta_btn": "Trader sur WhatsApp",
        "refer_h": "Invitez un ami. Vous gagnez tous les deux.",
        "refer_p": "Partagez votre lien, il trade, vous touchez chacun un bonus.",
        "refer_link": "referer",
        "refer_label": "Comment ça marche",
    },
}


def wwd_panel(i, total, kick, h2, p, cta_href, cta_label, img, external=False):
    tgt = ' target="_blank" rel="noopener"' if external else ""
    return f"""
      <article class="wwd-panel" data-panel="{i}">
        <div class="wwd-content">
          <div class="wwd-num"><b>{i:02d}</b> / {total:02d}</div>
          <span class="wwd-kick">{kick}</span>
          <h3>{h2}</h3>
          <p>{p}</p>
          <a class="btn" href="{cta_href}"{tgt}>{cta_label}</a>
        </div>
        <div class="wwd-media"><img src="/assets/img/{img}" alt="" loading="{'eager' if i == 1 else 'lazy'}" width="800" height="447"></div>
      </article>"""


def home_html(lang):
    c = HOME_COPY[lang]
    rc = RATES_COPY[lang]
    nc = NEWS_COPY[lang]
    ui = UI[lang]
    canonical = "/" if lang == "en" else "/derilbtc-accueil/"
    alt = "/derilbtc-accueil/" if lang == "en" else "/"
    rotator_items = "".join(f'<span class="rot-item">{label}</span>' for _, label, _, _ in SERVICES[lang])

    # WWD pinned stage: EN 1-1 from the original page, FR faithful translation.
    if lang == "en":
        panels_src = [{"kick": p["kick"], "h2": p["h2"], "p": p["p"],
                        "cta_href": p["cta_href"], "cta_label": p["cta_label"], "img": p["img"]}
                       for p in HOME_STRUCT["panels"]]
    else:
        panels_src = WWD_FR
    wwd_panels = "".join(
        wwd_panel(i + 1, len(panels_src), s["kick"], s["h2"], s["p"], s["cta_href"], s["cta_label"], s["img"])
        for i, s in enumerate(panels_src))

    hero_sub = (scrub(H.unescape(HOME_STRUCT.get("hero_p", c["sub"]))) if lang == "en"
                else "Achetez et vendez Bitcoin et USDT, payez fournisseurs et frais de scolarité à l'étranger, réservez des vols, vendez des cartes-cadeaux et échangez des Naira. Tout au Cameroun, tout payé sur MoMo en quelques minutes.")

    stat_tiles = "".join(
        f"""<div class="stat"><b{f' data-count="{t["count"]}"' if t["count"] else ''}>{'0' if t["count"] else t["b"]}</b><span>{t["s"]}</span></div>"""
        for t in STATS[lang]["tiles"])

    steps = "".join(f"""
    <div class="step" data-reveal><h3>{t}</h3><p>{p}</p></div>""" for t, p in c["steps"])
    title = ("Buy & Sell Bitcoin, USDT & More in Cameroon | DerilBTC" if lang == "en"
             else "Acheter et Vendre Bitcoin, USDT et Plus au Cameroun | DerilBTC")
    body = f"""
<main>
  <section class="hero">
    <div class="hero-inner hero-split">
      <div>
        <p class="ticker" id="ticker" aria-live="off"><img src="/assets/img/btc.svg" alt="" width="15" height="15">BTC <span id="t-btc">...</span><img src="/assets/img/usdt.svg" alt="" width="15" height="15">USDT <span id="t-usdt">...</span></p>
        <h1><span class="line"><span>{c['h1a']}</span></span><span class="line"><span>{c['h1b']}</span></span></h1>
        <p class="hero-sub">{hero_sub}</p>
        <div class="rotator" aria-hidden="true"><span class="rot-label"></span>{rotator_items}</div>
        <div class="hero-ctas">
          <a class="btn btn-lg" href="{WA}?text=Hi%20DerilBTC%21%20I%20want%20to%20trade." target="_blank" rel="noopener">{c['cta_btn']}</a>
          <a class="btn-ghost" href="#what-we-do">{c['explore']}</a>
        </div>
      </div>
      <div class="hero-media">
        <img src="/assets/img/derilbtc-hero.jpg" alt="DerilBTC: Bitcoin and money services in Cameroon" width="1400" height="781" fetchpriority="high">
      </div>
    </div>
    <div class="scrollcue" aria-hidden="true"><span class="mouse"></span></div>
  </section>

  <div class="coin-ticker" aria-hidden="true"><div class="coin-track" id="coin-track"></div></div>

  <section class="wwd" id="what-we-do">
    <div class="wwd-stage">
      <div class="wwd-head"><h2>{c['services_h']}</h2></div>
      {wwd_panels}
      <div class="wwd-prog"><i id="wwd-bar"></i></div>
    </div>
  </section>

  <section class="our-rates" data-admin="{ADMIN_URL}">
    <div class="rates-card">
      <div>
        <h2>{rc['h']}</h2>
        <p class="rates-lead">{rc['p']}</p>
        <a class="btn" href="{WA}?text={'Hi%21%20I%20want%20to%20lock%20today%27s%20rate.' if lang == 'en' else 'Bonjour!%20Je%20veux%20bloquer%20le%20taux%20du%20jour.'}" target="_blank" rel="noopener">{rc['lock']}</a>
      </div>
      <div class="rates-tiles">
        <div class="rate-tile"><span>{rc['btc']}</span><b><em id="r-btc">...</em> XAF</b><small>{rc['per']}</small></div>
        <div class="rate-tile"><span>{rc['usdt']}</span><b><em id="r-usdt">...</em> XAF</b><small>{rc['per']}</small></div>
      </div>
    </div>
  </section>

  <section class="stats">
    <h2>{STATS[lang]['h2']}</h2>
    <div class="stats-grid">{stat_tiles}</div>
  </section>

  <section class="steps-wrap">
    <h2>{c['steps_h']}</h2>
    <div class="steps">{steps}</div>
  </section>

  <section class="refer" data-reveal>
    <h2>{c['refer_h']}</h2>
    <p>{c['refer_p']} <a href="/{c['refer_link']}/">{c['refer_label']}</a></p>
  </section>

  <section class="newsletter">
    <h2>{nc['h']}</h2>
    <p>{nc['p']}</p>
    <form id="nl-form" data-lang="{lang}" data-ok="{nc['ok']}" data-err="{nc['err']}">
      <input type="email" name="email" required placeholder="{nc['ph']}" aria-label="{nc['ph']}">
      <input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" class="hp">
      <button class="btn" type="submit">{nc['btn']}</button>
    </form>
    <p id="nl-msg" role="status"></p>
  </section>

  <section class="cta-band">
    <h2>{c['cta_h']}</h2>
    <a class="btn btn-lg" href="{WA}" target="_blank" rel="noopener">{c['cta_btn']}</a>
  </section>
</main>"""
    desc = c["sub"]
    return shell(lang, title, desc, canonical, alt, body)


# ── build ───────────────────────────────────────────────────────────────────
def write(path, content):
    p = DIST / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def main():
    n = 0
    write("index.html", home_html("en")); n += 1
    write("derilbtc-accueil/index.html", home_html("fr")); n += 1
    for slug, page in RAW.items():
        if slug in ("home", "derilbtc-accueil"):
            continue
        write(f"{slug}/index.html", page_html(slug, page, page["lang"])); n += 1
    write("404.html", shell("en", "Page not found | DerilBTC",
        "That page does not exist.", "/404.html", "/",
        '<main><section class="page-hero"><h1>Page not found.</h1></section>'
        '<article class="prose"><p><a href="/">Back to the homepage</a></p></article></main>'))
    # sitemap (production URLs; harmless in preview because preview is noindexed)
    slugs = ["", "derilbtc-accueil/"] + sorted(
        f"{s}/" for s in RAW if s not in ("home", "derilbtc-accueil"))
    urls = "".join(f"<url><loc>https://derilbtc.com/{s}</loc></url>" for s in slugs)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: https://derilbtc.com/sitemap.xml\n" if not PREVIEW
          else "User-agent: *\nDisallow: /\n")
    print(f"built {n} pages + 404 into dist/")

if __name__ == "__main__":
    main()
