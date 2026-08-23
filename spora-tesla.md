# ŠPORA — TESLA Stropkov · pondelok 24.08 · 10:00 · očne
# Ing. Peter Švec (technický riaditeľ)

## 1. OTÁZKY DO CHATU (cez asistenta)
Ak položí hocijakú „hlúpu" otázku do chatu → systém buď nájde v doku, alebo povie „Neviem".
To NIE JE chyba, to je vaša výhoda.
Reakcia na každý odmietnutý off-topic:
> „Vidíte? Nehalucinuje — keď odpoveď nie je v dokumentácii, odmietne. To je presne pointa guardrails a bezpečnosti odpovedí."

ŽIADNA odpoveď systému nevyžaduje vysvetlenie. Len ukážeš na zelenú/žltú značku.

## 2. ODPOVEDE TEBE (developerské otázky)

### „Privátnosť?"
> „Embeddingy bežia lokálne, dáta nikam neodchádzajú. Generovanie vieme prepnúť aj on-premise. GDPE-safe."

### „Prečo ty, a nie LangChain/vendor?"
> „Lebo cieľ nie je predať krabicové riešenie, ale postaviť to pod vaše dáta. Musím rozumieť každej vrstve — retrieval, rerank, guardrails, loop — aby som to vedel prispôsobiť vašim procesom. LangChain je čierna skrinka, ktorú nespravíte pod seba."
> (Ak sa spýta na autorstvo kódu: „Postavil som to s pomocou AI nástrojov, ale architektúru a každé rozhodnutie som riadil a rozumiem tomu.")

### „Iné formáty?"
> „Teraz bežím na .md a .txt. Na vaše formáty (PDF/Word/výkresy) pridám parser na mieru — to je bežný deň práce. Chcem to otočiť na vaše reálne dokumenty."
> NEPOVEDÁŠ, že už všetko máš. Reálny stav: .md/.txt len.

## 3. ZLATÁ FRAZA — nevedomosť je OK
Na čokoľvek, čo nevieš: 
> „Nevedno povedať presne bez vašich vzorových dokumentov. Dajte mi 10–20 dokumentov a zajtra ukážem, ako to beží na vašich dátach."

Toto zatvára 100 % prípadov „čo keď sa spýta na XYZ a ja neviem". Nevedomé = požiadať o dáta.

## 4. OTÁZKY TECH Riaditeľa — najpravdepodobnejšie
1. rýchlosť („ako dlho odpovedá?") → stovky ms, lokálne
2. privátnosť → bod 2
3. „kde je reálny biznis prípad?" → SMT linka, technická doc, skracuje odstávky
4. „moje formáty?" → bod 2

## REÁLNY STAV (čo sme verifikovali)
- eval: 8/8 retrieval+guardrail, 3/3 LLM+source = 100 %
- UI: Streamlit, prihlásenie, chat + zdroj (akordeón), guardrail-značka (fixnutá v karte)
- ingest: .md/.txt reálne, PDF/docx v dokstringu, NIE v kóde
- upload do UI: NIE JE
- architektúra: BM25 + MiniLM embedding + mmarco cross-encoder rerank, guardrails, loop