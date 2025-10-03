import csv
from typing import Dict, List, Optional, Union, Tuple
import os


class GuesstimateCard:
    """
    Klass med logik för att behålla tal som INT om de är heltal,
    men konvertera till FLOAT om de har decimaler.
    Hanterar nu icke-överlappande intervall (ex. 499 istället för 500)
    endast för heltal.
    """

    FIELDNAMES = [
        "Kategori", "Fråga", "Lägre gräns 2p", "Lägre gräns 3p",
        "Lägre gräns 4p", "Lägre gräns 6p", "Rätt svar",
        "Övre gräns 6p", "Övre gräns 4p", "Övre gräns 3p",
        "Övre gräns 2p", "Kommentar", "", "Källa"
    ]

    NYCKEL_ORDNING = ['2_l', '3_l', '4_l', '6', '4_ö', '3_ö', '2_ö']

    def __init__(self, raw_data: Dict[str, str]):
        self.raw_data: Dict[str, str] = raw_data
        self.kategori: str = raw_data.get('Kategori', '')
        self.fråga: str = raw_data.get('Fråga', '')
        self.rätt_svar: str = raw_data.get('Rätt svar', '')

        # Lagrar de 8 gränserna som int eller float
        self._gräns_värden: Dict[str, Union[int, float]] = self._process_raw_data(raw_data)

        # Den slutgiltiga dictionaryn med intervallsträngar
        self.poäng_gränser_dict: Dict[str, str] = self._generera_intervall_dict()

    def _to_num(self, value: Optional[str]) -> Optional[Union[int, float]]:
        """
        Konverterar sträng till INT om det är ett heltal, annars till FLOAT.
        """
        if value is None or value == '':
            return None
        try:
            val = float(value.replace(',', '.'))

            # Kontrollera om float-värdet är ett rent heltal
            if val == int(val):
                return int(val)  # Returnera som INT
            else:
                return val  # Returnera som FLOAT
        except ValueError:
            return None

    def _process_raw_data(self, raw_data: Dict[str, str]) -> Dict[str, Union[int, float]]:
        """Extraherar och lagrar de 8 gränserna med smart int/float-hantering."""
        processed = {}
        for p in [2, 3, 4, 6]:
            processed[f"{p}_l"] = self._to_num(raw_data.get(f"Lägre gräns {p}p"))

        for p in [6, 4, 3, 2]:
            processed[f"{p}_ö"] = self._to_num(raw_data.get(f"Övre gräns {p}p"))

        return processed

    def _generera_intervall_dict(self) -> Dict[str, str]:
        """
        Bygger dictionaryn med intervallsträngar och justerar gränserna
        för att undvika överlapp ENDAST när det rör sig om heltal.
        """
        d = self._gräns_värden
        resultat_dict = {}

        # Funktion för att hantera den villkorliga justeringen
        def get_adjusted_boundary(value: Union[int, float], delta: int) -> Union[int, float]:
            """Lägger till/subtraherar delta endast om värdet är ett heltal."""
            if isinstance(value, int):
                return value + delta
            return value

        # 1. Lägre sidans intervall (2_l, 3_l, 4_l)
        # Intervall: [nuvarande L-gräns] till [nästa L-gräns - 1 (om int)]
        poäng_par_lägre = [(2, 3, 'l', 'l', '2_l'), (3, 4, 'l', 'l', '3_l'), (4, 6, 'l', 'l', '4_l')]
        for p_nu, p_nasta, dir_nu, dir_nasta, nyckel in poäng_par_lägre:

            # Lägre gräns är alltid den råa (t.ex. 470)
            lägre = d.get(f"{p_nu}_{dir_nu}")

            # Övre gräns är nästa gräns, justerad med -1 om int (t.ex. 499)
            nasta_grans_rå = d.get(f"{p_nasta}_{dir_nasta}")
            övre = get_adjusted_boundary(nasta_grans_rå, -1) if nasta_grans_rå is not None else None

            if lägre is not None and övre is not None:
                resultat_dict[nyckel] = f"{lägre}-{övre}"
            else:
                resultat_dict[nyckel] = f"ERROR: Intervall för {nyckel} saknas"

        # 2. 6p-intervall (6)
        # Detta intervall använder alltid de råa gränserna (L-6p till Ö-6p)
        lägre_6 = d.get('6_l')
        övre_6 = d.get('6_ö')
        if lägre_6 is not None and övre_6 is not None:
            resultat_dict['6'] = f"{lägre_6}-{övre_6}"
        else:
            resultat_dict['6'] = "ERROR: Intervall för 6 saknas"

        # 3. Övre sidans intervall (4_ö, 3_ö, 2_ö)
        # Intervall: [föregående Ö-gräns + 1 (om int)] till [nuvarande Ö-gräns]
        poäng_par_övre = [('6_ö', '4_ö', '4_ö'), ('4_ö', '3_ö', '3_ö'), ('3_ö', '2_ö', '2_ö')]
        for forra_nyckel, nu_nyckel, resultat_nyckel in poäng_par_övre:

            # Lägre gräns är föregående gräns, justerad med +1 om int (t.ex. 207 + 1 = 208)
            forra_grans_rå = d.get(forra_nyckel)
            lägre = get_adjusted_boundary(forra_grans_rå, 1) if forra_grans_rå is not None else None

            # Övre gräns är alltid den råa (t.ex. 210)
            övre = d.get(nu_nyckel)

            if lägre is not None and övre is not None:
                resultat_dict[resultat_nyckel] = f"{lägre}-{övre}"
            else:
                resultat_dict[resultat_nyckel] = f"ERROR: Intervall för {resultat_nyckel} saknas"

        return resultat_dict


# --- 2. Laddningsfunktion (Oberoende) ---

def load_cards_from_file(filename: str) -> List[GuesstimateCard]:
    # ... (Samma laddningslogik som tidigare) ...
    print(f"Laddar data från: '{filename}'...")
    fråge_lista = []

    try:
        with open(filename, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                fråge_lista.append(GuesstimateCard(row))

        print(f"✅ Laddade framgångsrikt {len(fråge_lista)} kort.")
        return fråge_lista

    except FileNotFoundError:
        print(f"❌ FEL: Filen hittades inte vid '{filename}'.")
        return []
    except Exception as e:
        print(f"❌ Ett oväntat fel uppstod vid filhantering: {e}")
        return []

    #print("\n--- Transformerat Resultat (Första Kortet) ---")
    #print(f"Fråga: {first_card.fråga}")
    #print(f"Rätt Svar: {first_card.rätt_svar}")
    #print("Poäng Intervall Dictionary:")
    #print(first_card.poäng_gränser_dict)
