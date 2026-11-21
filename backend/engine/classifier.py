"""Classification rules: brand, quality, color and size from SKU (variation column as fallback)."""
import re

from .text import compact, key, norm

SIZE_RE = re.compile(
    r"(?<![\d.,])(\d+(?:[.,]\d+)?)(KILOGRAMAS|KILOS|KILO|KGS|KG|ML|LITROS|LITRO|LTS|LT|L|GR|G)(?![A-Z])"
)
UNIT_MAP = {
    "KILOGRAMAS": "KG", "KILOS": "KG", "KILO": "KG", "KGS": "KG", "KG": "KG",
    "GR": "G", "G": "G", "ML": "ML", "LITROS": "L", "LITRO": "L", "LTS": "L", "LT": "L", "L": "L",
}


def size_label(value, unit):
    return f"{value:g}".replace(".", ",") + f" {unit}"


def find_sizes(text: str):
    t = compact(text)
    sizes = []
    for m in SIZE_RE.finditer(t):
        s = (float(m.group(1).replace(",", ".")), UNIT_MAP[m.group(2)])
        if s not in sizes:
            sizes.append(s)
    return sizes, SIZE_RE.sub(" ", t)


def _alias_keys(item):
    keys = {key(item["name"])} | {key(a) for a in item.get("aliases", []) if key(a)}
    return [k for k in keys if k]


def find_colors(parts, colors):
    cands = sorted(((k, c["name"]) for c in colors for k in _alias_keys(c)), key=lambda x: -len(x[0]))
    found = []
    for part in parts:
        used = [False] * len(part)
        for k, name in cands:
            start = part.find(k)
            while start != -1:
                if not any(used[start:start + len(k)]):
                    used[start:start + len(k)] = [True] * len(k)
                    if name not in found:
                        found.append(name)
                start = part.find(k, start + 1)
    return found


def match_brand(segment, brands):
    seg = key(segment)
    for b in brands:
        for k in _alias_keys(b):
            if re.fullmatch(re.escape(k) + r"\d*", seg):
                return b["name"]
    return None


def match_quality_segment(segment, qualities):
    seg = key(segment)
    cands = sorted(((k, q["name"]) for q in qualities for k in _alias_keys(q)), key=lambda x: -len(x[0]))
    return next((name for k, name in cands if seg.startswith(k)), None)


def match_quality_text(text, qualities):
    t = norm(text)
    hits = []
    for q in qualities:
        for a in [q["name"], *q.get("aliases", [])]:
            if norm(a) and re.search(r"\b" + re.escape(norm(a)) + r"\b", t) and q["name"] not in hits:
                hits.append(q["name"])
    return hits


def classify_product(p, settings):
    """Returns (fields, reasons) for a single product row."""
    reasons = []
    sku = p.get("sku", "")
    segs = [s for s in compact(sku).split("-") if s]
    f = {"brand": None, "quality": None, "color": None, "size_value": None, "size_unit": None}
    if not segs:
        return f, ["SKU não encontrado"]

    f["brand"] = match_brand(segs[0], settings["brands"])
    if not f["brand"]:
        reasons.append(f"Marca não reconhecida (prefixo do SKU: {segs[0]})")
    rest = segs[1:]

    q_idx = None
    for i, s in enumerate(rest):
        if key(s):
            q = match_quality_segment(s, settings["qualities"])
            if q:
                f["quality"], q_idx = q, i
            break
    if not f["quality"]:
        hits = match_quality_text(p.get("description", ""), settings["qualities"])
        if len(hits) == 1:
            f["quality"] = hits[0]
        elif len(hits) > 1:
            reasons.append(f"Qualidade conflitante na descrição ({', '.join(hits)})")
        else:
            reasons.append("Qualidade não reconhecida")

    sku_sizes, _ = find_sizes("-".join(rest))
    var_sizes, var_rest = find_sizes(p.get("variation", ""))
    if len(sku_sizes) > 1:
        reasons.append("Mais de um tamanho no SKU (" + ", ".join(size_label(*s) for s in sku_sizes) + ")")
    elif sku_sizes and var_sizes and var_sizes[0] != sku_sizes[0]:
        reasons.append(f"Tamanho conflitante: SKU {size_label(*sku_sizes[0])} x variação {size_label(*var_sizes[0])}")
    else:
        chosen = sku_sizes or var_sizes[:1]
        if chosen:
            f["size_value"], f["size_unit"] = chosen[0]
        else:
            reasons.append("Tamanho não reconhecido")

    color_parts = []
    for i, s in enumerate(rest):
        if i == q_idx:
            continue
        color_parts.append(key(find_sizes(s)[1]))
    sku_colors = find_colors(color_parts, settings["colors"])
    var_colors = find_colors([key(var_rest)], settings["colors"])
    if len(sku_colors) > 1:
        reasons.append("Mais de uma cor no SKU (" + ", ".join(sku_colors) + ")")
    elif sku_colors and var_colors and set(var_colors) != set(sku_colors):
        reasons.append(f"Cor conflitante: SKU {sku_colors[0]} x variação {', '.join(var_colors)}")
    elif sku_colors or len(var_colors) == 1:
        f["color"] = (sku_colors or var_colors)[0]
    else:
        prefix = f"Marca {f['brand']} identificada, mas cor" if f["brand"] else "Cor"
        reasons.append(f"{prefix} não reconhecida")
    return f, reasons


def classify_label(label, settings):
    products = label.get("products", [])
    empty = {"brand": None, "quality": None, "color": None, "size_value": None, "size_unit": None}
    if not label.get("has_text"):
        return {**empty, "reasons": ["Página sem texto selecionável (imagem). Informe os dados manualmente."]}
    if not products:
        msg = "SKU não encontrado" if label.get("table_found") else "Tabela de produtos (SKU) não encontrada na página"
        return {**empty, "reasons": [msg]}
    distinct = []
    for p in products:
        if key(p["sku"]) not in [key(d["sku"]) for d in distinct]:
            distinct.append(p)
    fields, reasons = classify_product(distinct[0], settings)
    if len(distinct) > 1:
        reasons = [f"Mais de um produto identificado ({len(distinct)} SKUs: " + ", ".join(d["sku"] for d in distinct) + ")"] + reasons
    return {**fields, "reasons": reasons}
