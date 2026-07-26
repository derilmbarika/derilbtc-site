# DerilBTC Daily Blog Rules

Read this whole file before writing any post. These rules exist so the daily
cadence NEVER turns into scaled thin content (a Google spam violation). One
genuinely helpful post per day, or nothing.

## Where posts live and how they publish

- One markdown file per post: `content/blog/<slug>.md` in this repo
  (`~/Downloads/derilbtc-next/`).
- `python3 build.py` renders them to `dist/blog/<slug>/` plus the `/blog/`
  index, nav/footer links, sitemap lastmod, BlogPosting + FAQPage schema.
- Deploy = rsync `dist/` to `docs/` (keep `CNAME` + `.nojekyll`), commit, push.
  GitHub Pages redeploys in about a minute.
- Python is 3.9: build.py has no f-string backslashes. Do not "modernize" it.

## File format

```
---
title: Post Title Here (55-60 chars, primary keyword near the front)
description: Meta description, 140-158 chars, includes primary keyword and a reason to click.
date: YYYY-MM-DD
slug: url-slug-with-primary-keyword
keywords: primary keyword, secondary 1, secondary 2
---

Body in markdown...
```

Supported markdown ONLY: `##` and `###` headings, paragraphs, `-` lists,
`1.` lists, `> ` quotes, `**bold**`, `*italic*`, `[text](url)` links,
`| tables |` with a `|---|` separator row. No HTML, no code fences, no
nested lists, no images unless the asset already exists in `assets/img/`.

## Content quality bar (non-negotiable)

1. **1,200-1,800 words** of substance. Never pad. If a topic honestly needs
   900, merge it with a sibling topic instead.
2. **Front-load the answer**: the first 2 paragraphs (before any H2) must
   directly and completely answer the title's question. AI Overviews and
   featured snippets weight opening content heavily.
3. **Question-style H2s** that mirror real searches ("How much does it cost
   to...", "Is it safe to...").
4. **First-hand desk experience in every post.** Write as the DerilBTC desk:
   real workflows, real numbers, real client situations (anonymized), what we
   see go wrong on WhatsApp every week. This is the E-E-A-T moat no generic
   crypto blog can copy. Never write a post a US content farm could have
   written.
5. **Cameroon-specific always**: XAF amounts, MoMo/Orange Money mechanics,
   local city references, CEMAC context. That is the niche.
6. **A comparison table** where the topic allows one (methods, fees, rates).
7. **FAQ section**: end with `## FAQ` + 3-5 `### question` / paragraph-answer
   pairs. The build turns these into accordions + FAQPage schema
   automatically. Answers must be plain text (no links inside FAQ answers).
8. **No invented facts, rates or statistics.** Only cite numbers you can
   source or that are desk-internal ("our desk typically..."). Fees and
   limits change: say "as of <month year>" and link the source.
9. **NEVER use em dashes or en dashes.** Rewrite with commas, colons or two
   sentences. (The build scrubs them as a safety net, but do not rely on it.)
10. Sentences short. Grade-8 reading level. The audience includes first-time
    crypto users on phones.

## Linking rules (every post)

- **3-5 internal links to money pages**, contextual, descriptive anchors:
  `/buy-bitcoin-cameroon/`, `/buy-bitcoin-momo-cameroon/`,
  `/buy-usdt-cameroon/`, `/pay-china-suppliers/`, `/pay-school-fees-abroad/`,
  `/book-flights/`, `/rates/`, `/safety/`, `/sell-gift-cards-cameroon/`,
  `/naira-to-cfa-cameroon/`, `/momo-scams-cameroon/`, `/refer/`,
  `/free-bitcoin-mentorship-cameroon/`, `/about/`, `/faq/`.
- **2+ links to other blog posts** once they exist (check `content/blog/` for
  live slugs; link as `/blog/<slug>/`). Also go back and add a link FROM one
  older related post TO the new post at least twice a week (update its
  `updated:` frontmatter field when you do).
- **1-2 external links to authoritative non-competitor sources** (BEAC, GSMA,
  Chainalysis, CoinGecko, official MTN/Orange pages, government/visa sites).
  The build automatically makes external links `nofollow`. Never link to
  competing exchanges' signup/landing pages.
- **One WhatsApp CTA** mid-post where it fits naturally, as a plain link to
  https://wa.me/237673259112 with action anchor text ("get a live quote on
  WhatsApp"). The author box adds the closing CTA automatically; do not
  duplicate it at the end.

## Keyword rules

- One primary keyword per post (from CONTENT-PLAN.md). It appears in: title,
  slug, description, first 100 words, exactly one H2, and naturally 3-6 more
  times. Do NOT stuff.
- Secondary keywords: work each into an H2/H3 or body sentence once or twice.
- Never target a keyword that an existing service page already targets; the
  blog post supports that page and links to it instead of competing with it.

## Daily workflow

1. Open `content/blog/CONTENT-PLAN.md`. Find today's row (and any earlier
   rows still marked `pending`: catch up, max 3 posts per run, oldest first;
   keep each post's planned `date:`).
2. **Trend check (every run, 5 minutes):** web-search current Bitcoin/crypto
   news. Only act on a trend if it has REAL value for Cameroonian readers:
   a major price move, a CEMAC/BEAC/Cameroon regulatory development, an
   MTN/Orange Money policy change, a big exchange collapse/hack, or a scam
   wave actually circulating locally. If (and only if) such a trend exists:
   either weave it into today's planned post with a dated paragraph, or
   replace today's topic with a trend post (add a new row to the plan, push
   the displaced topic to the end of the calendar so no day is lost). A
   generic "bitcoin went up 2%" story is NOT a trend post. Never force it.
3. Research 10-15 minutes max per post (web search for current fees, rates,
   news hooks). Verify anything time-sensitive.
4. Write the post per the rules above. Read it once as a skeptical Cameroonian
   reader; cut anything generic.
5. `cd ~/Downloads/derilbtc-next && python3 build.py` and confirm it prints
   the page count with no traceback, and `dist/blog/<slug>/index.html` exists.
6. Deploy: `rsync -a --delete --exclude CNAME --exclude .nojekyll dist/ docs/`
   then `git add -A && git commit -m "Blog: <title>" && git pull --rebase && git push`.
7. Verify `https://derilbtc.com/blog/<slug>/` returns 200 (allow ~2 min for
   Pages). If the push fails, resolve and retry; never leave the day unposted.
8. Mark the row `done` in CONTENT-PLAN.md (same commit or a follow-up).
9. Do NOT touch anything outside `content/blog/`, `CONTENT-PLAN.md` status
   cells, and the build/deploy outputs. Never edit service pages, build.py,
   or CSS as part of a daily run.
