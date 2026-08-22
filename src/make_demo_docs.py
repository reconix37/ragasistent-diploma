# -*- coding: utf-8 -*-
"""
Демонстрационные документы на словацком (SMT-монтаж / электроника)
для прототипа RAG-ассистента. Сгенерированы для демо в TESLA Stropkov,
т.к. настоящих документов фирмы нет (будут загружены на стажировке).

Каждый документ имеет надёжный «тег-ответ» (anchor) — для eval'а:
- Чанк с точным фактом (температура, шаг, допуск) → retrieval должен найти.
- Паттерн в имени файла: manuál/smt/proces/norma + номер.
"""
import os

DOCS = {
    "manuál-smt-montáž.md": {
        "title": "Manuál: SMT montáž - postup osadenia dosiek",
        "anchors": {
            "teplota": "Teplota v mieste lepenia je 25 ± 2 °C.",
            "reflow": "Maximálna teplota reflow profilu je 245 °C po dobu 10 sekúnd.",
            "pasta": "SnAgCu (SAC305) pasta sa nanáša hrúbkou 120 ± 20 µm.",
        },
    },
    "proces-osadzovanie-smt.md": {
        "title": "Proces: Osadzovanie SMT komponentov",
        "anchors": {
            "pickplace": "Osadzovací stroj položí komponent s presnosťou ±0,05 mm.",
            "rychlost": "Presun osadzovacej hlavy je max 0,4 m/s v režime plnej presnosti.",
            "umiestnenie": "Komponenty pod 0402 sa osadzujú dvoma kamerami s kontrolou polohy.",
        },
    },
    "norma-spájkovanie-en.md": {
        "title": "Norma: Spájkovanie - kontrolné parametre",
        "anchors": {
            "teplota_pred": "Predhrievanie dosky: 150 °C, rýchlosť nábehu max 2 °C/s.",
            "spoj": "Kvalitný spájkovaný spoj má dobré zmáčanie a minimálne dutiny.",
            "check": "AOI kontrola zachytí chýbajúce komponenty, skraty a orientáciu.",
        },
    },
    "pracovny-pokyn-tlac.md": {
        "title": "Pracovný pokyn: Tlač spájkovacej pasty",
        "anchors": {
            "stierka": "Uhol stierky pri tlači je 45° - 60°.",
            "registracia": "Registrácia šablóny: presnosť ±0,05 mm voči todolky.",
            "cistenie": "Dno šablóny sa čistí po každých 25 doskách.",
        },
    },
    "norma-kontrola-kvality.md": {
        "title": "Norma: Kontrola kvality a AOI",
        "anchors": {
            "aoi": "AOI linka kontroluje 100 % dosiek po prechode pecou.",
            "vzorky": "Vzorková kontrola IWe: 5 dosák z každého bloku 100 ks.",
            "zosuv": "Kritické chyby sa evidujú v systéme QMS do 24 hodín.",
        },
    },
    "pokyn-udrzba-strojov.md": {
        "title": "Pokyn: Údržba osadzovacích strojov",
        "anchors": {
            "denne": "Denná údržba: kontrola posuvných vedení a čistenie hlavy.",
            "tyzdenne": "Týždenná údržba: mazanie vodiacich líšt a kalibrácia kamier.",
            "interval": "Generálna údržba stroja sa vykonáva každých 5 000 prevádzkových hodín.",
        },
    },
    "bezpecnost-prace.md": {
        "title": "Bezpečnosť práce na linke SMT",
        "anchors": {
            "ochranne": "Povinné ochranné pracovné prostriedky: ochranné okuliare a rukavice.",
            "pec": "Pristup k reflow peci len po vychladnutí na pod 60 °C.",
            "chemikalie": "Čistiace chemikálie sa skladujú v uzavretých nádobách s označením.",
        },
    },
    "sklad-parametre.md": {
        "title": "Skladové parametre materiálu",
        "anchors": {
            "vlhkost": "Skladovacia vlhkosť DPS: 30 - 60 % RH.",
            "teplota_sklad": "Skladovacia teplota pasty: 2 - 10 °C, chránená pred svetlom.",
            "expirace": "Pasta po otvorení sa použije do 24 hodín.",
        },
    },
}


def build_markdown(title, anchors):
    """Собирает правдоподобный тех-документ вокруг якорей."""
    lines = [f"# {title}\n"]
    intro = (
        "Tento dokument popisuje štandardné výrobné postupy a kontrolné "
        "parametre používané na linke SMT pre dosky plošných spojov. Cieľom "
        "je zabezpečiť opakovateľnú kvalitu a zhode s predpismi."
    )
    lines.append(intro + "\n")
    # Пронумерованные шаги с вставленными якорями
    steps = [
        "Príprava podkladov a vstupná kontrola materiálu.",
        "Tlač spájkovacej pasty cez šablónu (pozri pracovný pokyn TT-01).",
        "Kontrola nanesenej pasty (2D meranie).",
        "Osadzovanie komponentov automatickým osadzovacím strojom.",
        "Predbežná vizuálna kontrola polohy komponentov.",
        "Prechod spájkovacou pecou reflow, profil podľa materiálu.",
        "Kontrola AOI a prípadná oprava.",
    ]
    for i, s in enumerate(steps, 1):
        lines.append(f"{i}. {s}\n")
    # Отдельная секция «Parametre» с якорями
    lines.append("\n## Parametre a kontrolné body\n")
    lines.append("Pre dodržanie kvality sú kľúčové nasledujúce hodnoty:\n")
    # берём первые 2 якоря как «параметры», сохранённый порядок
    for key, val in list(anchors.items())[:3]:
        lines.append(f"- {val}\n")
    lines.append("\n## Poznámky\n")
    lines.append(
        "V prípade nezrovnalosti postupujte podľa nadradenej normy a "
        "kontaktujte technológov linky. Hodnoty v tomto dokumente sú "
        "orientačné a platia pre štandardný proces.\n"
    )
    return "".join(lines)


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    for fname, meta in DOCS.items():
        content = build_markdown(meta["title"], meta["anchors"])
        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ {fname} ({len(content.split())} slov)")
    print(f"\nHotovo. Dokumenty v: {out_dir}")
    print("Základné informácie pre eval:")
    for fname, meta in DOCS.items():
        print(f"  {fname}: {list(meta['anchors'].keys())}")


if __name__ == "__main__":
    main()