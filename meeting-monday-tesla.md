# PONEDELOK 24.08 · 10:00 — TESLA Stropkov (očne)
# Kontakt: Ing. Peter Švec — technický riaditeľ (potvrdené).

## CIEL STRETNUTIA
- Ukázať ŽIVÝ prototyp RAG-asistenta na technickej dokumentácii.
- Prejsť demo: 3-4 otázky s odpoveďou + zdroj, potom zámerný off-topic → guardrail „Neviem“.
- Otvoriť otázku: spolupráca/staž v rámci SPICE, reálne dáta, konzultácia k diplomovej.

## REČ (2-3 min, po slovensky)
> „Dobrý deň, som študent 5. ročníka ITVP na TUKE. V rámci diplomovej práce som postavil RAG-asistenta na technickú dokumentáciu – technik sa opýta na postup alebo parameter a asistent odpovie s odkazom na konkrétny dokument. Dôležité: dokumenty neopúšťajú firmu, spracovanie je lokálne, generuje sa len odpoveď. Mám tu živý prototyp – môžem ukázať na SMT dokumentácii, ktorú som si pripravil ako ukážku.“

## SCENÁR DEMO
1. „Aká je maximálna teplota reflow?“ → 245 °C + zdroj (manuál-smt-montáž.md)
2. „Aká je presnosť osadzovacieho stroja?“ → ±0,05 mm + zdroj
3. „Aké sú skladovacie podmienky spájkovacej pasty?“ → 2–10 °C, 24 h + zdroj
4. Spark moment: „Ktorý zamestnanec dostal najvyšší plat?“ → **guardrail «Neviem»** + metka. →
   > „Vidíte? Nehalucinuje. Keď odpoveď nie je v dokumentácii alebo je málo relevantná, odmietne – nevieš mu presne povedať, že si vymýšľa. Toto je presne pointa – guardrails na bezpečnosť odpovedí.“

## AKO ZAVRIEŤ DEAL
- Keď sa zapáli: „Viem to otočiť na vaše reálne dokumenty behom jedného dňa – PDF/Word/index/chat. Chcel by som na tom postaviť diplomovku a prípadne staž cez SPICE. Dáme si ďalší call?“
- Ak sa spýta na cenu/štandard: „Produkt – nie, to je výskumný prototyp na diplomovku. Cieľ je spolupracovať a ukázať, že to funguje na vašich dátach.“

## ODPOVEĎ NA HLAVNÉ NÁMITKY
- **„Privátnosť?“** → Lokálne embeddingy, dáta sa nikam neposielajú. Aj keby sme prepínali generovanie on-premise, dá sa to. GDPR-safe.
- **„Prečo nie vendor (LangChain a pod.)?“** → Ja som to urobil čisto, rozumiem každému dieliku; guardrails a loop-engineering sa nepíšu vo venore, píšu sa ručne.
- **„Čo keď dokumenty v iných formátoch?“** → Zvláda PDF/Word/markdown/text, parser na vaše formáty pridáme podľa potreby.