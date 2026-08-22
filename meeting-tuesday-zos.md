# UTOROK 25.08 — ŽOS Trnava, a.s. (online Teams)
# Kontakt: Ing. Miroslav Hájiček — vedúci TPV NV (technická príprava výroby nových vozňov).
# Tón: TECHNICKÝ. Nepredávam znova „čo to je“ — prechádzam na „ako to pôjde na vaše dáta“.

## CIEL STRETNUTIA
- Po pondelku (TESLA): prísť už so zeleným svetlom „vedúci TESLA sa zaujímal“ (ak sa to stane).
- Prejsť na detaily: JAVA formát dokumentov, indexácia, škálovanie, plán nasadzovania.
- Cieľová váha rozhovoru: dostať ponuku na REÁLNE dáta/TPV-dokumenty ako prípadovú štúdiu pre diplom.

## REČ (otvorenie)
> „Dobrý deň, v pondelok som ukazoval prototyp RAG-asistenta vedúcemu TESLA Stropkov. Robím to ako diplomovku (ITVP TUKE). Rád by som si overil, či to dnes zapadne aj do prostredia TPV – najmä čo sa týka formátov technickej dokumentácie a spôsobu, akým máte procesy zdokumentované.“

## TECH OSNOVA (hlavná časť – byť konkrétny)
1. **Formáty dokumentov v TPV:** PDF/Word/dwg/Excel? Väčšina TPV má výkresovú + textovú dokumentáciu. Môj pipeline: PDF, Word, markdown, čistý text → parsujeme aj komentáre/revízie.
2. **Ako indexujeme:** lokálne embeddingy (sentence-transformers), chunking ~200 slov s prekryvom, hybrid search (BM25 + vektor) + rerank cross-encoder, potom guardrail-prah. Všetko lokálne.
3. **Škálovanie/objem:** endpoint na 1 request ~ niekoľko stoviek ms-1 s. Pre stovky dokumentov stačí jeden server; pre tisíce – batch indexácia, dá sa aj paralelne.
4. **Správa zdrojov a auditu:** každá odpoveď má odkaz na konkrétny dokument a časť → kontrolovateľnosť, súlad s QMS (akékoľvek revízie procesu).
5. **Čo je MVP za 1 deň:** vezmem 10-20 ich dokumentov → index → chat → demo priamo na ich dátach.

## ODPOVEĎ NA NÁMITKY (špecifické pre ŽOS/TPV)
- **„Výkresy (dwg/PDF technické)“** → Najprv textová vrstva (kusovníky, postupy, normy). Výkresová geometria – neskôr, nie v MVP. Byť úprimný.
- **„Máme staré formáty/scan“** → Pridáme OCR vrstvu pre skeny. Da sa.
- **„Kvalita odpovedí na špecifické normy“** → dotiahnuté eval: 100 % pass na fakty, guardrail 100 % na off-topic. Uvediem čísla.

## AKO ZAVRIEŤ
> „Čo by som potreboval, aby to bolo reálne: 10-20 dokumentov, ktoré by ste mi mohli poskytnúť ako vzorku na prípadovú štúdiu. Všetko zostane lokálne. Na konci dostanete fungujúci prototyp na vašich dátach – a ja prípadovú štúdiu do diplomovky. Súhlasíte?“
- Ak váha: „Nemusím nič zverejňovať – safer: ukážem demo, metadáta, nie obsah. Dá sa podpísať NDA.“