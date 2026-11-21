"""Reads Up Seller label PDFs: finds the DANFE product table (SKU / Descrição / Variação / QTD) on each page."""
import re
import pymupdf

from .text import norm

QTY_RE = re.compile(r"^[\(（]?(\d{1,4})[\)）]?$")
LABEL_NO_RE = re.compile(r"^(\d{1,5})/(\d{1,5})$")
HEADER_KEYS = {"SKU": "sku", "DESCRICAO": "desc", "VARIAC": "var", "QTD": "qtd", "TOTAL": "total"}


def _axes(sku, qtd):
    if abs(sku[1] - qtd[1]) < 3:
        return (0, 2), (1, 3)  # columns along x, rows along y
    if abs(sku[0] - qtd[0]) < 3:
        return (1, 3), (0, 2)  # rotated text: columns along y, rows along x
    return None


def _span(w, axis, sign):
    a, b = sign * w[axis[0]], sign * w[axis[1]]
    return min(a, b), max(a, b)


def _find_table(words):
    skus = [w for w in words if w[4] == "SKU"]
    qtds = [w for w in words if norm(w[4]) == "QTD"]
    for sku in skus:
        for qtd in qtds:
            axes = _axes(sku, qtd)
            if axes:
                return sku, qtd, axes
    return None


def _lines(words, col_axis, cs, row_axis, rs):
    rows = []
    for w in sorted(words, key=lambda w: (_span(w, row_axis, rs)[0], _span(w, col_axis, cs)[0])):
        r = _span(w, row_axis, rs)[0]
        if rows and abs(rows[-1][0] - r) < 2:
            rows[-1][1].append(w)
        else:
            rows.append([r, [w]])
    return [" ".join(x[4] for x in sorted(ws, key=lambda w: _span(w, col_axis, cs)[0])) for _, ws in rows]


def _parse_products(words):
    found = _find_table(words)
    if not found:
        return None
    sku_h, qtd_h, (col_axis, row_axis) = found
    line_words = [w for w in words if abs(_span(w, row_axis, 1)[0] - _span(sku_h, row_axis, 1)[0]) < 3]
    heads = {}
    for w in line_words:
        k = norm(w[4])
        if k in HEADER_KEYS and HEADER_KEYS[k] not in heads:
            heads[HEADER_KEYS[k]] = w
    if not {"sku", "desc", "var", "qtd"} <= heads.keys():
        return None
    cs = 1 if _span(heads["desc"], col_axis, 1)[0] > _span(heads["sku"], col_axis, 1)[0] else -1
    hc = {k: _span(w, col_axis, cs)[0] for k, w in heads.items()}
    q_end = hc.get("total", hc["qtd"] + 25)

    def col_center(w):
        a, b = _span(w, col_axis, cs)
        return (a + b) / 2

    totals = [w for w in words if w[4] == "Total" and abs(_span(w, col_axis, cs)[0] - hc["sku"]) < 6]
    raw_h = _span(sku_h, row_axis, 1)[0]
    if totals:
        rs = 1 if _span(totals[0], row_axis, 1)[0] > raw_h else -1
    else:
        qty_side = [w for w in words if hc["qtd"] - 2 <= col_center(w) < q_end and QTY_RE.match(w[4])]
        rs = 1 if any(_span(w, row_axis, 1)[0] > raw_h for w in qty_side) else -1
    hr = _span(sku_h, row_axis, rs)[1]
    tr = min((_span(w, row_axis, rs)[0] for w in totals if _span(w, row_axis, rs)[0] > hr), default=float("inf"))

    body = [w for w in words if hr < _span(w, row_axis, rs)[0] < tr - 1]
    anchors = sorted(
        _span(w, row_axis, rs)[0] for w in body
        if hc["qtd"] - 2 <= col_center(w) < q_end and QTY_RE.match(w[4])
    )
    products = []
    for i, a in enumerate(anchors):
        end = anchors[i + 1] - 4 if i + 1 < len(anchors) else tr - 1
        rw = [w for w in body if a - 4 <= _span(w, row_axis, rs)[0] < end]

        def cell(lo, hi):
            return _lines([w for w in rw if lo <= col_center(w) < hi], col_axis, cs, row_axis, rs)

        sku_lines = cell(hc["sku"] - 15, hc["desc"] - 1)
        qty_words = [w for w in rw if hc["qtd"] - 2 <= col_center(w) < q_end and QTY_RE.match(w[4])]
        products.append({
            "sku": "".join(sku_lines).replace(" ", ""),
            "description": " ".join(cell(hc["desc"] - 1, hc["var"] - 1)),
            "variation": " ".join(cell(hc["var"] - 1, hc["qtd"] - 2)),
            "qty": int(QTY_RE.match(qty_words[0][4]).group(1)) if qty_words else 1,
        })
    return products


def read_pdf(data: bytes) -> list[dict]:
    doc = pymupdf.open(stream=data, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        words = page.get_text("words")
        label_no = next((w[4] for w in words if LABEL_NO_RE.match(w[4])), None)
        products = _parse_products(words) if words else None
        pages.append({
            "page": i,
            "has_text": bool(words),
            "label_no": label_no,
            "table_found": products is not None,
            "products": products or [],
        })
    doc.close()
    return pages


def group_labels(pages: list[dict]) -> list[dict]:
    """Keeps physical pages of one label together (same n/N marker, or an unmarked page following a marked one)."""
    labels = []
    for p in pages:
        prev = labels[-1] if labels else None
        same = prev and p["label_no"] and p["label_no"] == prev["label_no"]
        continuation = prev and not p["label_no"] and prev["label_no"]
        if same or continuation:
            prev["pages"].append(p["page"])
            prev["products"].extend(p["products"])
            prev["has_text"] = prev["has_text"] or p["has_text"]
            prev["table_found"] = prev["table_found"] or p["table_found"]
        else:
            labels.append({
                "pages": [p["page"]],
                "label_no": p["label_no"],
                "products": list(p["products"]),
                "has_text": p["has_text"],
                "table_found": p["table_found"],
            })
    return labels
