import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const UNITS = ["KG", "G", "L", "ML"];

const UnitSelect = ({ value, onChange, testId }) => (
  <select value={value} onChange={(e) => onChange(e.target.value)} data-testid={testId}
    className="h-9 rounded-md border border-slate-200 bg-white px-2 text-sm">
    {UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
  </select>
);

export const SizeRulesEditor = ({ rules, onChange }) => {
  const set = (i, k, v) => onChange(rules.map((r, j) => (j === i ? { ...r, [k]: v } : r)));

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        Os tamanhos são ordenados do menor para o maior: primeiro os em KG (G é convertido para KG), depois os em L (ML para L).
        Peso e volume nunca são convertidos entre si automaticamente. Para que um volume seja ordenado junto de um peso,
        cadastre uma regra abaixo (ex.: 3,6 L ordena como 5 KG).
      </p>
      <ul className="space-y-2">
        {rules.map((r, i) => (
          <li key={i} className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2" data-testid={`size-rule-${i}`}>
            <Input type="number" step="0.1" value={r.value} onChange={(e) => set(i, "value", e.target.value)} className="h-9 w-24" data-testid={`size-rule-value-${i}`} />
            <UnitSelect value={r.unit} onChange={(v) => set(i, "unit", v)} testId={`size-rule-unit-${i}`} />
            <span className="text-sm text-slate-500">ordena como</span>
            <Input type="number" step="0.1" value={r.sort_value} onChange={(e) => set(i, "sort_value", e.target.value)} className="h-9 w-24" data-testid={`size-rule-sort-value-${i}`} />
            <UnitSelect value={r.sort_unit} onChange={(v) => set(i, "sort_unit", v)} testId={`size-rule-sort-unit-${i}`} />
            <Input value={r.note || ""} placeholder="Observação" onChange={(e) => set(i, "note", e.target.value)} className="h-9 min-w-[180px] flex-1" data-testid={`size-rule-note-${i}`} />
            <Button size="icon" variant="ghost" aria-label="Remover regra" onClick={() => onChange(rules.filter((_, j) => j !== i))} data-testid={`size-rule-remove-${i}`}>
              <Trash2 className="h-4 w-4 text-red-600" />
            </Button>
          </li>
        ))}
      </ul>
      <Button variant="outline" data-testid="size-rule-add-button"
        onClick={() => onChange([...rules, { value: 1, unit: "L", sort_value: 1.5, sort_unit: "KG", note: "" }])}>
        <Plus className="mr-2 h-4 w-4" /> Adicionar regra
      </Button>
    </div>
  );
};
