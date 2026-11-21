import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, RotateCcw, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ListEditor } from "@/components/settings/ListEditor";
import { SizeRulesEditor } from "@/components/settings/SizeRulesEditor";
import { api, errorMessage } from "@/lib/api";

const TABS = [
  { id: "qualities", label: "Qualidades", help: "A ordem da lista define a ordem das seções no PDF. As variações são procuradas no início do trecho do SKU após a marca (ex.: PISO2, ECON0, MANTA18KG)." },
  { id: "colors", label: "Cores", help: "Sequência operacional das cores. Arraste ou use as setas. Variações são comparadas sem acentos, espaços ou maiúsculas (ex.: PAPELPICADO = PAPEL PICADO)." },
  { id: "brands", label: "Marcas", help: "Ordem das marcas dentro de cada cor. A variação precisa ser exatamente o prefixo do SKU (ex.: NCC-..., NUANCE-...), por isso INOVALAR não é confundido com INV por semelhança." },
];

const clean = (s) => ({
  ...s,
  qualities: s.qualities.map((x) => ({ ...x, aliases: x.aliases.map((a) => a.trim()).filter(Boolean) })),
  colors: s.colors.map((x) => ({ ...x, aliases: x.aliases.map((a) => a.trim()).filter(Boolean) })),
  brands: s.brands.map((x) => ({ ...x, aliases: x.aliases.map((a) => a.trim()).filter(Boolean) })),
  size_rules: s.size_rules.map((r) => ({ ...r, value: Number(r.value), sort_value: Number(r.sort_value) })),
});

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get("/settings").then((r) => setSettings(r.data)).catch(async (e) => toast.error(await errorMessage(e)));
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      const { data } = await api.put("/settings", clean(settings));
      setSettings(data);
      toast.success("Configurações salvas. Use 'Reanalisar' em um resultado para aplicar.");
    } catch (e) {
      toast.error(await errorMessage(e, "Falha ao salvar"));
    } finally {
      setSaving(false);
    }
  };

  const reset = async () => {
    if (!window.confirm("Restaurar marcas, cores, qualidades e regras padrão?")) return;
    const { data } = await api.post("/settings/reset");
    setSettings(data);
    toast.success("Configurações padrão restauradas");
  };

  if (!settings) return <Loader2 className="h-6 w-6 animate-spin text-slate-400" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-4xl font-extrabold tracking-tight text-slate-900">Configurações</h1>
          <p className="text-sm text-slate-500">Valem para todos os usuários. Clique em Salvar após alterar.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={reset} data-testid="settings-reset-button">
            <RotateCcw className="mr-2 h-4 w-4" /> Restaurar padrão
          </Button>
          <Button onClick={save} disabled={saving} className="bg-blue-600 hover:bg-blue-700" data-testid="settings-save-button">
            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />} Salvar
          </Button>
        </div>
      </div>
      <Tabs defaultValue="qualities" className="section">
        <TabsList className="mb-4 flex-wrap">
          {TABS.map((t) => <TabsTrigger key={t.id} value={t.id} data-testid={`settings-tab-${t.id}`}>{t.label}</TabsTrigger>)}
          <TabsTrigger value="sizes" data-testid="settings-tab-sizes">Tamanhos</TabsTrigger>
        </TabsList>
        {TABS.map((t) => (
          <TabsContent key={t.id} value={t.id} className="space-y-4">
            <p className="text-sm text-slate-600">{t.help}</p>
            <ListEditor items={settings[t.id]} prefix={t.id} addLabel={`Nova ${t.label.toLowerCase().slice(0, -1)}`}
              onChange={(v) => setSettings({ ...settings, [t.id]: v })} />
          </TabsContent>
        ))}
        <TabsContent value="sizes">
          <SizeRulesEditor rules={settings.size_rules} onChange={(v) => setSettings({ ...settings, size_rules: v })} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
