"""Konsolowa ewidencja konta firmy i magazynu. Uruchom: python firma.py."""

from decimal import Decimal, InvalidOperation, localcontext
import json
from pathlib import Path


KOMENDY = "saldo, sprzedaż, zakup, konto, lista, magazyn, przegląd, koniec"
GROSZ = Decimal("0.01")
PLIK_DANYCH = Path(__file__).resolve().parent / "dane.txt"


def wczytaj_dane():
    if not PLIK_DANYCH.exists():
        return Decimal("0.00"), {}, []
    with open(PLIK_DANYCH, "r", encoding="utf-8") as plik:
        dane = json.load(plik)
    saldo = Decimal(dane["saldo"])
    magazyn = dane["magazyn"]
    for produkt in magazyn.values():
        produkt["cena"] = Decimal(produkt["cena"])
    return saldo, magazyn, dane["historia"]


def zapisz_dane(saldo, magazyn, historia):
    dane = {"saldo": str(saldo), "magazyn": {}, "historia": historia}
    for nazwa, produkt in magazyn.items():
        dane["magazyn"][nazwa] = {
            "cena": str(produkt["cena"]), "ilosc": produkt["ilosc"]
        }
    # Najpierw zapisujemy nowy plik, aby nie utracić poprzednich danych.
    plik_tymczasowy = PLIK_DANYCH.with_suffix(".tmp")
    with open(plik_tymczasowy, "w", encoding="utf-8") as plik:
        json.dump(dane, plik, ensure_ascii=False, indent=4)
    plik_tymczasowy.replace(PLIK_DANYCH)


def wczytaj_kwote(komunikat):
    tekst = input(komunikat).strip().replace(",", ".")
    try:
        kwota = Decimal(tekst)
    except InvalidOperation:
        raise ValueError("Podaj poprawną kwotę, np. 125,50.") from None
    if not kwota.is_finite() or abs(kwota) > Decimal("999999999999.99"):
        raise ValueError("Kwota musi być skończona i nie przekraczać 999999999999,99.")
    if kwota != kwota.quantize(GROSZ):
        raise ValueError("Kwota może mieć najwyżej dwa miejsca po przecinku.")
    return kwota.quantize(GROSZ)


def wczytaj_nazwe():
    nazwa = input("Nazwa produktu: ").strip().casefold()
    if not nazwa:
        raise ValueError("Nazwa produktu nie może być pusta.")
    return nazwa


def wczytaj_ilosc():
    try:
        ilosc = int(input("Liczba sztuk: ").strip())
    except ValueError:
        raise ValueError("Liczba sztuk musi być liczbą całkowitą.") from None
    if not 1 <= ilosc <= 1_000_000_000:
        raise ValueError("Liczba sztuk musi być dodatnia i nie większa niż 1000000000.")
    return ilosc


def pieniadze(kwota):
    return f"{kwota:.2f} zł".replace(".", ",")


def pokaz_produkt(nazwa, produkt):
    print(f"{nazwa}: {produkt['ilosc']} szt., cena jednostkowa: "
          f"{pieniadze(produkt['cena'])}")


def pokaz_historie(historia):
    od = input("Od indeksu (Enter = początek): ").strip()
    do = input("Do indeksu (Enter = koniec, włącznie): ").strip()
    liczba = len(historia)
    informacja = f"Liczba zapisanych komend: {liczba}."
    if liczba:
        informacja += f" Dostępne indeksy: 0–{liczba - 1}."
    try:
        poczatek = int(od) if od else 0
        koniec = int(do) if do else liczba - 1
    except ValueError:
        print("Indeksy muszą być liczbami całkowitymi. " + informacja)
        return
    if not liczba and not od and not do:
        print("Historia jest pusta. " + informacja)
        return
    if not 0 <= poczatek <= koniec < liczba:
        print("Nieprawidłowy zakres. " + informacja)
        return
    for indeks in range(poczatek, koniec + 1):
        print(f"[{indeks}] {historia[indeks]}")


def uruchom():
    try:
        saldo, magazyn, historia = wczytaj_dane()
        zapisz_dane(saldo, magazyn, historia)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, InvalidOperation) as blad:
        print(f"Nie można odczytać lub przygotować pliku danych: {blad}")
        return
    print("Ewidencja firmy. Dane są zapisywane w pliku dane.txt.")
    while True:
        print(f"\nDostępne komendy: {KOMENDY}")
        try:
            komenda = input("Wprowadź komendę: ").strip().casefold()
            komenda = {"sprzedaz": "sprzedaż", "przeglad": "przegląd"}.get(
                komenda, komenda
            )
            if komenda == "koniec":
                print("Zakończono program.")
                break
            if komenda == "saldo":
                kwota = wczytaj_kwote("Kwota do dodania lub odjęcia (ze znakiem minus): ")
                saldo += kwota
                historia.append(f"saldo: {pieniadze(kwota)}; stan konta: {pieniadze(saldo)}")
                print(f"Stan konta: {pieniadze(saldo)}")
            elif komenda in ("zakup", "sprzedaż"):
                nazwa = wczytaj_nazwe()
                cena = wczytaj_kwote("Cena jednostkowa: ")
                if cena <= 0:
                    raise ValueError("Cena produktu musi być większa od zera.")
                ilosc = wczytaj_ilosc()
                wartosc = cena * ilosc
                if komenda == "zakup":
                    if saldo < wartosc:
                        raise ValueError(
                            f"Brak środków: zakup kosztuje {pieniadze(wartosc)}, "
                            f"stan konta wynosi {pieniadze(saldo)}."
                        )
                    poprzednia_ilosc = magazyn.get(nazwa, {}).get("ilosc", 0)
                    magazyn[nazwa] = {"cena": cena, "ilosc": poprzednia_ilosc + ilosc}
                    saldo -= wartosc
                else:
                    if nazwa not in magazyn:
                        raise ValueError("Tego produktu nie ma w magazynie.")
                    if magazyn[nazwa]["ilosc"] < ilosc:
                        raise ValueError(
                            f"Za mało sztuk. Dostępne: {magazyn[nazwa]['ilosc']}."
                        )
                    magazyn[nazwa]["ilosc"] -= ilosc
                    saldo += wartosc
                historia.append(
                    f"{komenda}: {nazwa}, {ilosc} szt. po {pieniadze(cena)}; "
                    f"wartość: {pieniadze(wartosc)}; stan konta: {pieniadze(saldo)}"
                )
                print(f"Wykonano {komenda}. Stan konta: {pieniadze(saldo)}")
            elif komenda == "konto":
                print(f"Stan konta: {pieniadze(saldo)}")
            elif komenda == "lista":
                if not magazyn:
                    print("Magazyn jest pusty.")
                for nazwa, produkt in sorted(magazyn.items()):
                    pokaz_produkt(nazwa, produkt)
            elif komenda == "magazyn":
                nazwa = wczytaj_nazwe()
                if nazwa in magazyn:
                    pokaz_produkt(nazwa, magazyn[nazwa])
                else:
                    print("Tego produktu nie ma w magazynie.")
            elif komenda == "przegląd":
                pokaz_historie(historia)
            else:
                print("Nieznana komenda. Wybierz jedną z dostępnych komend.")
            if komenda in ("saldo", "zakup", "sprzedaż"):
                zapisz_dane(saldo, magazyn, historia)
        except OSError as blad:
            print(f"Nie udało się zapisać ostatniej operacji: {blad}")
            print("Program zostanie zakończony. Sprawdź dostęp do pliku dane.txt.")
            break
        except ValueError as blad:
            print(f"Nie wykonano operacji: {blad}")
        except (EOFError, KeyboardInterrupt):
            print("\nPrzerwano program.")
            break


if __name__ == "__main__":
    # Większa precyzja chroni obliczenia kwot i liczby sztuk przed zaokrąglaniem.
    with localcontext() as kontekst:
        kontekst.prec = 60
        uruchom()
