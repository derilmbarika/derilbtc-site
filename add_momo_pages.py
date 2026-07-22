#!/usr/bin/env python3
"""Add the MoMo buying guide (EN + FR) to content/raw_pages.json.
Targets GSC queries: "how to buy bitcoin in cameroon with momo" (EN) and
"bitcoin cameroun" / MoMo variants (FR). Run once, then build.py."""
import json

EN_HTML = """
<h1>How to Buy Bitcoin with MTN MoMo in Cameroon</h1>
<p>Buying Bitcoin with MTN Mobile Money (MoMo) or Orange Money is the fastest way to get BTC in Cameroon: no bank account, no card, no international exchange that rejects Cameroonian users. This guide shows you the exact steps, what it costs, and how to stay safe while doing it.</p>
<h2>Why MoMo Is the Best Way to Buy Bitcoin in Cameroon</h2>
<p>Most global exchanges do not support FCFA deposits, and cards issued by Cameroonian banks are frequently declined abroad. Mobile Money works because the transaction stays local: you send FCFA from your MoMo wallet, and a trusted desk delivers Bitcoin to your wallet address minutes later. That is exactly the service we run at DerilBTC, and you can see the full process on our <a href="/buy-bitcoin-cameroon/">buy Bitcoin in Cameroon</a> page.</p>
<h2>Step by Step: From FCFA to Bitcoin</h2>
<ol>
<li><strong>Get a Bitcoin wallet.</strong> Any self-custody wallet works. Write down your recovery phrase offline and never share it with anyone, including us.</li>
<li><strong>Check the current rate.</strong> Our <a href="/rates/">live rates page</a> shows what your FCFA converts to before you commit. No hidden spread added afterward.</li>
<li><strong>Message the desk on WhatsApp.</strong> Tell us the amount in FCFA and share your wallet address. We confirm the rate and total in writing before anything moves.</li>
<li><strong>Send the MoMo payment.</strong> You transfer FCFA from your MTN MoMo or Orange Money wallet to the number we confirm in the chat, and only that number.</li>
<li><strong>Receive your Bitcoin.</strong> We send BTC to your address and share the transaction ID so you can track the confirmation on-chain yourself.</li>
</ol>
<h2>How Much Does It Cost?</h2>
<p>You pay the FCFA amount agreed in the chat, plus your operator's standard MoMo transfer fee. The rate we quote is the rate you get. Compare it any day against the parallel market on our <a href="/rates/">rates page</a>. For stable value transfers, many clients prefer USDT instead; see <a href="/buy-usdt-cameroon/">buying USDT in Cameroon</a>.</p>
<h2>Staying Safe: The Rules That Protect You</h2>
<ul>
<li>Never send MoMo to a number you found in a Facebook group or Telegram channel. Verified desk numbers only.</li>
<li>Insist on the rate and total in writing before you pay. A legitimate desk always agrees.</li>
<li>Never share your wallet recovery phrase. Buying Bitcoin never requires it.</li>
<li>Start with a small test amount on a first transaction. A real desk encourages this.</li>
<li>Read our guide to <a href="/momo-scams-cameroon/">common MoMo scams in Cameroon</a> before your first purchase, and our <a href="/safety/">safety page</a> for how we verify every transaction.</li>
</ul>
<h2>Frequently Asked Questions</h2>
<details><summary>Can I buy Bitcoin with MTN MoMo directly, without a desk?</summary><p>Not directly. MTN does not sell Bitcoin. You need a counterparty who accepts MoMo and delivers BTC, which is what an OTC desk like DerilBTC does. The desk model is faster and safer than peer-to-peer strangers when the desk is verifiable.</p></details>
<details><summary>What is the minimum amount I can buy?</summary><p>We handle everything from small first purchases of about 10,000 FCFA up to large transactions. For bigger amounts we simply split delivery for safety and confirm each leg.</p></details>
<details><summary>How long does it take to receive my Bitcoin?</summary><p>Typically minutes after your MoMo payment confirms. Network congestion can add time on-chain, which is why we always share the transaction ID so you can track it.</p></details>
<details><summary>Does Orange Money work too?</summary><p>Yes. The process is identical with Orange Money: confirm the rate in writing, send to the verified number, receive BTC to your wallet.</p></details>
<details><summary>Is buying Bitcoin legal in Cameroon?</summary><p>Owning crypto is not criminalized for individuals, but the regulatory environment (CEMAC/COBAC) is restrictive for institutions and evolving. Buy from a transparent desk, keep records of your transactions, and never let anyone hold your coins for you.</p></details>
"""

FR_HTML = """
<h1>Acheter du Bitcoin avec MTN MoMo au Cameroun</h1>
<p>Acheter du Bitcoin avec MTN Mobile Money (MoMo) ou Orange Money est le moyen le plus rapide d'obtenir du BTC au Cameroun : pas de compte bancaire, pas de carte, pas de plateforme internationale qui rejette les utilisateurs camerounais. Ce guide montre les etapes exactes, le cout reel, et comment rester en securite.</p>
<h2>Pourquoi MoMo est le meilleur moyen d'acheter du Bitcoin au Cameroun</h2>
<p>La plupart des plateformes mondiales n'acceptent pas les depots en FCFA, et les cartes des banques camerounaises sont souvent refusees. Le Mobile Money fonctionne parce que la transaction reste locale : vous envoyez des FCFA depuis votre portefeuille MoMo, et un bureau de confiance livre le Bitcoin a votre adresse en quelques minutes. C'est exactement le service DerilBTC ; voyez le processus complet sur notre page <a href="/fr/acheter-bitcoin-cameroun/">acheter du Bitcoin au Cameroun</a>.</p>
<h2>Etape par etape : du FCFA au Bitcoin</h2>
<ol>
<li><strong>Creez un portefeuille Bitcoin.</strong> N'importe quel portefeuille en auto-garde convient. Notez votre phrase de recuperation hors ligne et ne la partagez jamais, meme avec nous.</li>
<li><strong>Verifiez le taux du jour.</strong> Notre page <a href="/fr/taux/">taux en direct</a> montre ce que vos FCFA valent avant de vous engager.</li>
<li><strong>Ecrivez au bureau sur WhatsApp.</strong> Indiquez le montant en FCFA et votre adresse de portefeuille. Nous confirmons le taux et le total par ecrit avant tout transfert.</li>
<li><strong>Envoyez le paiement MoMo.</strong> Vous transferez les FCFA depuis MTN MoMo ou Orange Money vers le numero confirme dans la discussion, et uniquement ce numero.</li>
<li><strong>Recevez votre Bitcoin.</strong> Nous envoyons le BTC a votre adresse et partageons l'identifiant de transaction pour que vous puissiez suivre la confirmation vous-meme.</li>
</ol>
<h2>Combien ca coute ?</h2>
<p>Vous payez le montant FCFA convenu dans la discussion, plus les frais de transfert standard de votre operateur. Le taux annonce est le taux applique. Comparez-le chaque jour sur notre page <a href="/fr/taux/">taux</a>. Pour une valeur stable, beaucoup de clients preferent l'USDT ; voir <a href="/fr/acheter-usdt-cameroun/">acheter de l'USDT au Cameroun</a>.</p>
<h2>Securite : les regles qui vous protegent</h2>
<ul>
<li>N'envoyez jamais de MoMo a un numero trouve dans un groupe Facebook ou un canal Telegram. Numeros verifies uniquement.</li>
<li>Exigez le taux et le total par ecrit avant de payer. Un bureau legitime accepte toujours.</li>
<li>Ne partagez jamais votre phrase de recuperation. Un achat de Bitcoin ne la demande jamais.</li>
<li>Commencez par un petit montant test lors d'une premiere transaction.</li>
<li>Lisez notre guide des <a href="/fr/arnaques-momo-cameroun/">arnaques MoMo au Cameroun</a> avant votre premier achat, et notre page <a href="/fr/securite/">securite</a>.</li>
</ul>
<h2>Questions frequentes</h2>
<details><summary>Puis-je acheter du Bitcoin directement avec MTN MoMo, sans bureau ?</summary><p>Non, pas directement. MTN ne vend pas de Bitcoin. Il faut une contrepartie qui accepte le MoMo et livre le BTC : c'est le role d'un bureau OTC comme DerilBTC, plus rapide et plus sur que des inconnus en pair-a-pair.</p></details>
<details><summary>Quel est le montant minimum ?</summary><p>Nous traitons aussi bien les premiers achats d'environ 10 000 FCFA que les grosses transactions, que nous fractionnons pour la securite.</p></details>
<details><summary>Combien de temps pour recevoir mon Bitcoin ?</summary><p>En general quelques minutes apres confirmation de votre paiement MoMo. La congestion du reseau peut ajouter du delai on-chain, d'ou le partage systematique de l'identifiant de transaction.</p></details>
<details><summary>Orange Money fonctionne aussi ?</summary><p>Oui. Le processus est identique : taux confirme par ecrit, envoi au numero verifie, reception du BTC dans votre portefeuille.</p></details>
<details><summary>Acheter du Bitcoin est-il legal au Cameroun ?</summary><p>La detention par les particuliers n'est pas criminalisee, mais le cadre reglementaire CEMAC/COBAC est restrictif pour les institutions et evolue. Achetez aupres d'un bureau transparent et gardez une trace de vos transactions.</p></details>
"""

RAW = "content/raw_pages.json"
raw = json.load(open(RAW))
raw["buy-bitcoin-momo-cameroon"] = {
    "id": 90001, "lang": "en",
    "title": "How to Buy Bitcoin with MTN MoMo in Cameroon (Step by Step)",
    "html": EN_HTML.strip(), "link": "https://derilbtc.com/buy-bitcoin-momo-cameroon/",
}
raw["acheter-bitcoin-momo-cameroun"] = {
    "id": 90002, "lang": "fr",
    "title": "Acheter du Bitcoin avec MTN MoMo au Cameroun (Guide Complet)",
    "html": FR_HTML.strip(), "link": "https://derilbtc.com/fr/acheter-bitcoin-momo-cameroun/",
}
json.dump(raw, open(RAW, "w"), ensure_ascii=False, indent=1)
print("raw_pages.json now", len(raw), "pages")
