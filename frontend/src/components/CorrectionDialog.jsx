import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, errorMessage } from "@/lib/api";

const Field = ({ label, value, onChange, options, testId }) => (
  <div className="space-y-1">
    <div className="label-caps">{label}</div>
    <Select value={value || ""} onValueChange={onChange}>
      <SelectTrigger data-testid={testId}><SelectValue placeholder="Selecione" /></SelectTrigger>
      <SelectContent>
        {options.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}
      </SelectContent>
    </Select>
  </div>
);

export const CorrectionDialog = ({ job, label, settings, onClose, onJob }) => {
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (label) {
      setForm({
        brand: label.brand, quality: label.quality, color: label.color,
        size_value: label.size_value ?? "", size_unit: label.size_unit || "KG",
      });
    }
  }, [label]);

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));
  const complete = form.brand && form.quality && form.color && Number(form.size_value) > 0 && form.size_unit;

  const save = async (body) => {
    setSaving(true);
    try {
      const { data } = await api.put(`/jobs/${job.id}/labels/${label.idx}`, body);
      onJob(data);
      toast.success(body.brand ? "Etiqueta corrigida" : "Correção removida");
      onClose();
    } catch (e) {
      toast.error(await errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={!!label} onOpenChange={(o) => !o && onClose()}>
      <DialogContent data-testid="correction-dialog">
        <DialogHeader>
          <DialogTitle className="font-heading">Corrigir etiqueta — página {label ? label.pages.map((p) => p + 1).join(", ") : ""}</DialogTitle>
          <DialogDescription className="font-data text-xs">
            {label?.products.map((p) => p.sku).join(" · ") || "SKU não encontrado"}
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Qualidade" value={form.quality} onChange={set("quality")} testId="correction-quality"
            options={settings.qualities.map((q) => q.name)} />
          <Field label="Cor" value={form.color} onChange={set("color")} testId="correction-color"
            options={settings.colors.map((c) => c.name)} />
          <Field label="Marca" value={form.brand} onChange={set("brand")} testId="correction-brand"
            options={settings.brands.map((b) => b.name)} />
          <div className="space-y-1">
            <div className="label-caps">Tamanho</div>
            <div className="flex gap-2">
              <Input type="number" step="0.1" min="0" value={form.size_value} data-testid="correction-size-value"
                onChange={(e) => set("size_value")(e.target.value)} />
              <Select value={form.size_unit} onValueChange={set("size_unit")}>
                <SelectTrigger className="w-24" data-testid="correction-size-unit"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {["KG", "G", "L", "ML"].map((u) => <SelectItem key={u} value={u}>{u}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
        <DialogFooter className="gap-2">
          {label?.manual && (
            <Button variant="ghost" disabled={saving} onClick={() => save({})} data-testid="correction-clear-button">
              Remover correção
            </Button>
          )}
          <Button disabled={!complete || saving} className="bg-blue-600 hover:bg-blue-700" data-testid="correction-save-button"
            onClick={() => save({ ...form, size_value: Number(form.size_value) })}>
            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Salvar correção
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
