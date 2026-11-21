import { AlertTriangle, CheckCircle2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export const ReviewList = ({ labels, onEdit }) => {
  const review = labels.filter((l) => l.status !== "ok");
  const corrected = labels.filter((l) => l.manual && l.status === "ok");

  return (
    <section className="section fade-up space-y-4" data-testid="review-section">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-amber-500" />
        <h3 className="font-heading text-lg font-bold text-slate-900">Etiquetas para revisão ({review.length})</h3>
      </div>
      <p className="text-sm text-slate-500">
        Estas páginas ficam no final do PDF, na seção REVISAR. Corrija os dados para que entrem na ordem certa.
      </p>
      {review.length === 0 && (
        <div className="flex items-center gap-2 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800" data-testid="review-empty">
          <CheckCircle2 className="h-4 w-4" /> Nenhuma etiqueta precisa de revisão.
        </div>
      )}
      <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">
        {[...review, ...corrected].map((l) => (
          <li key={l.idx} className="flex flex-wrap items-center gap-4 px-4 py-3" data-testid={`review-item-${l.idx}`}>
            <div className="font-heading w-24 shrink-0 font-bold text-slate-900">
              Página {l.pages.map((p) => p + 1).join(", ")}
            </div>
            <div className="min-w-0 flex-1 space-y-1">
              <div className="font-data truncate text-xs text-slate-500">{l.products.map((p) => p.sku).join(" · ") || "—"}</div>
              {l.status === "ok" ? (
                <Badge className="border-emerald-200 bg-emerald-100 text-emerald-800 hover:bg-emerald-100">
                  Corrigida manualmente · {l.quality} · {l.color} · {l.brand} · {l.size_label}
                </Badge>
              ) : (
                <div className="text-sm text-slate-800" data-testid={`review-reason-${l.idx}`}>{l.reasons.join("; ")}</div>
              )}
            </div>
            <Button variant="outline" size="sm" onClick={() => onEdit(l)} data-testid={`review-edit-${l.idx}`}>
              <Pencil className="mr-2 h-3.5 w-3.5" /> Corrigir
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
};
