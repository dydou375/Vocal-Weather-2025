import re
from spacy.tokens import Span
from spacy.language import Language
from spacy.util import filter_spans
import dateparser

ordinal_to_number = {
    "premier": "1", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5",
    "six": "6", "sept": "7", "huit": "8", "neuf": "9", "dix": "10",
    "onze": "11", "douze": "12", "treize": "13", "quatorze": "14",
    "quinze": "15", "seize": "16", "dix-sept": "17", "dix-huit": "18",
    "dix-neuvième": "19", "vingt": "20", "vingt-et-un": "21", "vingt-deux": "22",
    "vingt-trois": "23", "vingt-quatre": "24", "vingt-cinq": "25", "vingt-six": "26",
    "vingt-sept": "27", "vingt-huit": "28", "vingt-neuf": "29", "trente": "30", 
    "trente-et-un": "31"
}

@Language.component("find_dates")
def find_dates(doc):
    # Définir une extension de date sur le span
    Span.set_extension("date", default=None, force=True)

    # Ordinaux
    ordinals = [
        "premier", "deux", "trois", "quatre", "cinq",
        "six", "sept", "huit", "neuf", "dix",
        "onze", "douze", "treize", "quatorze",
        "quinze", "seize", "dix-sept", "dix-huit",
        "dix-neuf", "vingt", "vingt-et-un", "vingt-deux",
        "vingt-trois", "vingt-quatre", "vingt-cinq", "vingt-six",
        "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente-et-un"  
    ]
    
    ordinal_pattern = r"\b(?:" + "|".join(ordinals) + r")\b"

    # Un modèle regex pour capturer une variété de formats de date
    date_pattern = r"""
        # Jour-Mois-Année
        (?:
            \d{1,2}(?:er|ème)?          # Jour avec suffixe optionnel er, ème
            \s+
            (?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]* # Nom du mois
            (?:                         # Année est optionnelle
                \s+
                \d{4}                   # Année
            )?
        )
        |
        # Jour/Mois/Année
        (?:
            \d{1,2}                     # Jour
            [/-]
            \d{1,2}                     # Mois
            (?:                         # Année est optionnelle
                [/-]
                \d{2,4}                 # Année
            )?
        )
        |
        # Année-Mois-Jour
        (?:
            \d{4}                       # Année
            [-/]
            \d{1,2}                     # Mois
            [-/]
            \d{1,2}                     # Jour
        )
        |
        # Mois-Jour-Année
        (?:
            (?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]* # Nom du mois
            \s+
            \d{1,2}(?:er|ème)?          # Jour avec suffixe optionnel er, ème
            (?:                         # Année est optionnelle
                ,?
                \s+
                \d{4}                   # Année
            )?
        )
        |
        # Mois-Année
        (?:
            (?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]* # Nom du mois
            \s+
            \d{4}                       # Année
        )
        |
        # Ordinal-Jour-Mois-Année
        (?:
            """ + ordinal_pattern + """
            \s+
            (?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]* # Nom du mois
            (?:                         # Année est optionnelle
                \s+
                \d{4}                   # Année
            )?
        )
        |
        (?:
            """ + ordinal_pattern + """
            \s+
            de
            \s+
            (?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]*  # Nom du mois
            (?:                         # Année est optionnelle
                \s+
                \d{4}                   # Année
            )?
        )
        |
        # Mois Ordinal
        (?:
            (?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]*  # Nom du mois
            \s+
            """ + ordinal_pattern + """
            (?:                         # Année est optionnelle
                \s+
                \d{4}                   # Année
            )?
        )
    """
    matches = list(re.finditer(date_pattern, doc.text, re.VERBOSE))
    new_ents = []
    for match in matches:
        start_char, end_char = match.span()
        # Convertir les offsets de caractères en offsets de tokens
        start_token = None
        end_token = None
        for token in doc:
            if token.idx == start_char:
                start_token = token.i
            if token.idx + len(token.text) == end_char:
                end_token = token.i
        if start_token is not None and end_token is not None:
            hit_text = doc.text[start_char:end_char]
            parsed_date = dateparser.parse(hit_text, languages=["fr"])
            if parsed_date:  # S'assurer que la chaîne correspondante est une date valide
                ent = Span(doc, start_token, end_token + 1, label="DATE")
                ent._.date = parsed_date
                new_ents.append(ent)
            else:
                # Remplacer chaque ordinal dans hit_text par sa représentation numérique
                for ordinal, number in ordinal_to_number.items():
                    hit_text = hit_text.replace(ordinal, number)

                # Supprimer le mot "de" de hit_text
                new_date = hit_text.replace(" de ", " ")

                parsed_date = dateparser.parse(new_date, languages=["fr"])
                ent = Span(doc, start_token, end_token + 1, label="DATE")
                ent._.date = parsed_date
                new_ents.append(ent)
    # Combiner les nouvelles entités avec les entités existantes, en s'assurant qu'il n'y a pas de chevauchement
    doc.ents = list(doc.ents) + new_ents
    
    return doc
