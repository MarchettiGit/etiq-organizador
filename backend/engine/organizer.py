"""Sorting (QUALIDADE → COR → MARCA → TAMANHO) and PDF assembly by page reordering only."""
import pymupdf

from .classifier import classify_label, size_label
from .text import key

FIELDS = ("brand", "quality", "color", "size_value", "size_unit")


def finalize_label(label, settings):
    auto = classify_label(label, settings)
    manual = label.get("manual")
    final = {k: (manual or {}).get(k) or auto.get(k) for k in FIELDS} if manual else {k: auto.get(k) for k in FIELDS}
    known = {
        "brand": {b["name"] for b in settings["brands"]},
        "quality": {q["name"] for q in settings["qualities"]},
        "color": {c["name"] for c in settings["colors"]},
    }
    if manual:
        missing = [k for k in FIELDS if not final.get(k)]
        unknown = [k for k in ("brand", "quality", "color") if final.get(k) and final[k] not in known[k]]
        reasons = (["Correção manual incompleta"] if missing else []) + [f"{k} '{final[k]}' não existe nas configurações" for k in unknown]
    else:
        reasons = auto["reasons"]
    label.update(final)
    label["auto_reasons"] = auto["reasons"]
    label["reasons"] = reasons
    label["status"] = "ok" if not reasons else "revisar"
    label["size_label"] = size_label(final["size_value"], final["size_unit"]) if final.get("size_value") else None
    return label


def size_sort_key(value, unit, rules):
    for r in rules:
        if abs(float(r["value"]) - value) < 1e-6 and key(r["unit"]) == key(unit):
            value, unit = float(r["sort_value"]), r["sort_unit"]
            break
    unit = key(unit)
    if unit == "G":
        value, unit = value / 1000, "KG"
    if unit == "ML":
        value, unit = value / 1000, "L"
    return (0 if unit == "KG" else 1, value)


def order_labels(labels, settings):
    qi = {q["name"]: i for i, q in enumerate(settings["qualities"])}
    ci = {c["name"]: i for i, c in enumerate(settings["colors"])}
    bi = {b["name"]: i for i, b in enumerate(settings["brands"])}
    ok = [l for l in labels if l["status"] == "ok"]
    rev = [l for l in labels if l["status"] != "ok"]
    ok.sort(key=lambda l: (
        qi.get(l["quality"], 999), ci.get(l["color"], 999), bi.get(l["brand"], 999),
        size_sort_key(l["size_value"], l["size_unit"], settings.get("size_rules", [])), l["pages"][0],
    ))
    rev.sort(key=lambda l: l["pages"][0])
    ordered = ok + rev
    for pos, l in enumerate(ordered):
        l["position"] = pos
    return ordered


def page_order(ordered_labels):
    return [p for l in ordered_labels for p in l["pages"]]


def build_pdf(src: bytes, order: list[int]) -> bytes:
    doc = pymupdf.open(stream=src, filetype="pdf")
    n = doc.page_count
    if sorted(order) != list(range(n)):
        raise ValueError("A ordem final não contém exatamente todas as páginas do PDF original")
    doc.select(order)
    out = doc.tobytes()
    doc.close()
    check = pymupdf.open(stream=out, filetype="pdf")
    if check.page_count != n:
        raise ValueError(f"PDF final com {check.page_count} páginas, original com {n}")
    check.close()
    return out
