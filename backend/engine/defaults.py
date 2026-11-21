def _items(pairs):
    return [{"name": n, "aliases": a} for n, a in pairs]


DEFAULT_QUALITIES = _items([
    ("ECON", ["ECON", "ECONOMICA", "ECONOMICO"]),
    ("PISO PREMIUM / STANDARD", ["PISO", "PREM", "PREMIUM", "STANDARD", "STD"]),
    ("MANTA EMB / SUPERLAV", ["MANTA", "EMBO", "EMB", "EMBORRACHADA", "SUPER", "SUPERLAV", "SUPERLAVAVEL"]),
])

DEFAULT_COLORS = _items([
    ("Branco Neve", ["BRANCO NEVE", "NEVE", "BRANCO"]),
    ("Erva Doce", ["ERVA DOCE"]),
    ("Rosa BB", ["ROSA BB", "ROSA BEBE"]),
    ("Azul BB", ["AZUL BB", "AZUL BEBE"]),
    ("Azul Céu", ["AZUL CEU"]),
    ("Lilás", ["LILAS"]),
    ("Pink", ["PINK"]),
    ("Gelo", ["GELO"]),
    ("Palha", ["PALHA"]),
    ("Marfim", ["MARFIM"]),
    ("Pérola", ["PEROLA"]),
    ("Baunilha", ["BAUNILHA"]),
    ("Amarelo", ["AMARELO"]),
    ("Areia", ["AREIA"]),
    ("Bege", ["BEGE"]),
    ("Algodão Egípcio", ["ALGODAO EGIPCIO"]),
    ("Papel Picado", ["PAPEL PICADO"]),
    ("Ovelha", ["OVELHA"]),
    ("Vermelho", ["VERMELHO"]),
    ("Coloridas", ["CAMURCA", "VERDE MUSGO", "VERDE AGUA", "MARSALA", "TELHA", "TERRA", "MARROM", "PETROLEO"]),
    ("Grafite", ["GRAFITE", "CINZA GRAFITE"]),
    ("Asfalto", ["ASFALTO"]),
    ("Inox", ["INOX"]),
    ("Cinza", ["CINZA"]),
    ("Nanquim", ["NANQUIM"]),
    ("Elefante", ["ELEFANTE"]),
    ("Crômio", ["CROMIO"]),
])

DEFAULT_BRANDS = _items([
    ("CMC", ["CMC"]),
    ("DMC", ["DMC"]),
    ("INV", ["INV", "INOVALAR"]),
    ("MAGMA", ["MAGMA"]),
    ("MAISON", ["MAISON"]),
    ("MORALAR", ["MORALAR"]),
    ("NUANCE", ["NUANCE", "NCC"]),
    ("NVL", ["NVL"]),
    ("VERTICE", ["VERTICE", "VERT"]),
])

DEFAULT_SIZE_RULES = [
    {"value": 3.6, "unit": "L", "sort_value": 5, "sort_unit": "KG", "note": "3,6 L ordena junto com 5 kg"},
]


def default_settings() -> dict:
    return {
        "qualities": [dict(q) for q in DEFAULT_QUALITIES],
        "colors": [dict(c) for c in DEFAULT_COLORS],
        "brands": [dict(b) for b in DEFAULT_BRANDS],
        "size_rules": [dict(r) for r in DEFAULT_SIZE_RULES],
    }
