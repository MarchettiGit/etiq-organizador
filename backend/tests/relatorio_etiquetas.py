"""Relatório de teste do motor: python tests/relatorio_etiquetas.py <arquivo.pdf> [saida.md]"""
import sys
from collections import Counter
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.defaults import default_settings  # noqa: E402
from engine.extractor import group_labels, read_pdf  # noqa: E402
from engine.organizer import build_pdf, finalize_label, order_labels, page_order  # noqa: E402


def main(src_path, out_md):
    data = Path(src_path).read_bytes()
    settings = default_settings()
    pages = read_pdf(data)
    labels = group_labels(pages)
    for i, l in enumerate(labels):
        l["idx"], l["manual"] = i, None
        finalize_label(l, settings)
    ordered = order_labels(labels, settings)
    order = page_order(ordered)
    out = build_pdf(data, order)

    src, dst = pymupdf.open(stream=data, filetype="pdf"), pymupdf.open(stream=out, filetype="pdf")
    identical = sum(
        1 for i, p in enumerate(order)
        if src[p].get_text() == dst[i].get_text() and src[p].get_pixmap(dpi=72).samples == dst[i].get_pixmap(dpi=72).samples
    )
    ok = [l for l in ordered if l["status"] == "ok"]
    rev = [l for l in ordered if l["status"] != "ok"]

    qi = {q["name"]: i for i, q in enumerate(settings["qualities"])}
    ci = {c["name"]: i for i, c in enumerate(settings["colors"])}
    seq_ok = all((qi[a["quality"]], ci[a["color"]]) <= (qi[b["quality"]], ci[b["color"]]) for a, b in zip(ok, ok[1:]))
    blocks = [(l["quality"], l["color"], l["brand"]) for l in ok]
    grouped = len(set(blocks)) == len([b for i, b in enumerate(blocks) if i == 0 or blocks[i - 1] != b])

    lines = [
        f"# Relatório de teste — {Path(src_path).name}", "",
        f"- Páginas lidas: {len(pages)} (com texto: {sum(p['has_text'] for p in pages)})",
        f"- Etiquetas: {len(labels)} | classificadas: {len(ok)} | revisar: {len(rev)} | {100 * len(ok) / len(labels):.1f}%",
        f"- Páginas no PDF final: {dst.page_count} (original {src.page_count})",
        f"- Páginas idênticas ao original (texto + imagem renderizada, inclui códigos de barras): {identical}/{len(order)}",
        f"- Sequência qualidade→cor respeitada: {'SIM' if seq_ok else 'NÃO'}",
        f"- Marcas agrupadas dentro de qualidade/cor: {'SIM' if grouped else 'NÃO'}",
        f"- Marcas encontradas: {dict(Counter(l['brand'] for l in labels if l['brand']))}",
        f"- Qualidades: {dict(Counter(l['quality'] for l in ok))}", "",
        "## Ordem final", "", "| Pos | Pág. orig. | SKU | Qualidade | Cor | Marca | Tamanho |", "|---|---|---|---|---|---|---|",
    ]
    for l in ok:
        sku = ", ".join(p["sku"] for p in l["products"])
        lines.append(f"| {l['position'] + 1} | {l['pages'][0] + 1} | {sku} | {l['quality']} | {l['color']} | {l['brand']} | {l['size_label']} |")
    lines += ["", "## Revisar (padrões a ajustar)", ""]
    for l in rev:
        sku = ", ".join(p["sku"] for p in l["products"]) or "-"
        lines.append(f"- Página {l['pages'][0] + 1} — {'; '.join(l['reasons'])} (SKU: {sku})")
    Path(out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "relatorio_teste.md")
