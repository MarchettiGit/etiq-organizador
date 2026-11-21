import { ListOrdered, Pencil } from "lucide-react";

const groupBy = (items, fn) => {
  const out = [];
  items.forEach((it) => {
    const k = fn(it);
    if (!out.length || out[out.length - 1].key !== k) out.push({ key: k, items: [] });
    out[out.length - 1].items.push(it);
  });
  return out;
};

const LabelRow = ({ l, onEdit }) => (
  <li className="flex items-center gap-3 py-1 text-sm">
    <span className="font-data w-10 text-right text-slate-400">#{l.position + 1}</span>
    <span className="font-data w-16 font-medium text-slate-900">{l.size_label}</span>
    <span className="font-data truncate text-xs text-slate-500">pág. {l.pages.map((p) => p + 1).join(",")} · {l.products.map((p) => p.sku).join(" · ")}</span>
    <button type="button" aria-label="Corrigir etiqueta" onClick={() => onEdit(l)} data-testid={`order-edit-${l.idx}`}
      className="ml-auto rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700">
      <Pencil className="h-3.5 w-3.5" />
    </button>
  </li>
);

export const OrderPreview = ({ labels, onEdit }) => {
  const ordered = [...labels].filter((l) => l.status === "ok").sort((a, b) => a.position - b.position);
  const reviewCount = labels.length - ordered.length;

  return (
    <section className="section fade-up space-y-5" data-testid="order-preview">
      <div className="flex items-center gap-2">
        <ListOrdered className="h-5 w-5 text-blue-600" />
        <h3 className="font-heading text-lg font-bold text-slate-900">Ordem do PDF organizado</h3>
      </div>
      {groupBy(ordered, (l) => l.quality).map((q) => (
        <div key={q.key} className="space-y-3" data-testid={`order-quality-${q.key}`}>
          <div className="rounded-lg bg-slate-900 px-4 py-2 font-heading text-sm font-bold uppercase tracking-wider text-white">
            Qualidade {q.key} <span className="font-normal text-slate-400">· {q.items.length} etiquetas</span>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {groupBy(q.items, (l) => l.color).map((c) => (
              <div key={c.key} className="rounded-lg border border-slate-200 p-3">
                <div className="mb-2 font-heading font-bold text-slate-900">{c.key}</div>
                {groupBy(c.items, (l) => l.brand).map((b) => (
                  <div key={b.key} className="mb-2 border-l-2 border-amber-400 pl-3">
                    <div className="label-caps">{b.key}</div>
                    <ul>{b.items.map((l) => <LabelRow key={l.idx} l={l} onEdit={onEdit} />)}</ul>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      ))}
      {reviewCount > 0 && (
        <div className="rounded-lg bg-amber-100 px-4 py-2 font-heading text-sm font-bold uppercase tracking-wider text-amber-900">
          REVISAR · {reviewCount} etiquetas no final do PDF
        </div>
      )}
    </section>
  );
};
