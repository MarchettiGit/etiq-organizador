import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { UploadZone } from "@/components/UploadZone";
import { JobResult } from "@/components/JobResult";
import { JobsTable } from "@/components/JobsTable";
import { api, errorMessage, USER_KEY } from "@/lib/api";

const MAX_MB = 50;

export default function HomePage() {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [job, setJob] = useState(null);
  const [recent, setRecent] = useState([]);

  const loadRecent = useCallback(() => {
    api.get("/jobs", { params: { limit: 5 } }).then((r) => setRecent(r.data)).catch(() => {});
  }, []);

  useEffect(() => { loadRecent(); }, [loadRecent]);

  const pick = (f) => {
    if (f && !f.name.toLowerCase().endsWith(".pdf")) return toast.error("Envie apenas arquivos PDF");
    if (f && f.size > MAX_MB * 1024 * 1024) return toast.error(`Arquivo maior que ${MAX_MB} MB`);
    setFile(f);
  };

  const organize = async () => {
    setBusy(true);
    setProgress(0);
    const form = new FormData();
    form.append("file", file);
    form.append("user_name", localStorage.getItem(USER_KEY) || "");
    try {
      const { data } = await api.post("/jobs", form, {
        onUploadProgress: (e) => e.total && setProgress(Math.round((e.loaded / e.total) * 100)),
      });
      setJob(data);
      setFile(null);
      toast.success(`${data.classified} de ${data.labels_count} etiquetas classificadas`);
      loadRecent();
    } catch (e) {
      toast.error(await errorMessage(e, "Falha ao organizar o PDF"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="fade-up space-y-2">
        <h1 className="font-heading text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          Organizar etiquetas
        </h1>
        <p className="max-w-2xl text-base text-slate-600">
          Envie o PDF exportado pelo Up Seller. As páginas são reordenadas por
          <strong className="text-slate-900"> qualidade → cor → marca → tamanho</strong>, sem alterar nenhuma etiqueta.
        </p>
      </section>

      <section className="section fade-up space-y-5">
        <UploadZone file={file} onFile={pick} disabled={busy} />
        <div className="flex flex-wrap items-center gap-4">
          <Button onClick={organize} disabled={!file || busy} data-testid="organize-button"
            className="h-12 bg-blue-600 px-8 text-base font-semibold hover:bg-blue-700">
            {busy ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Sparkles className="mr-2 h-5 w-5" />}
            ORGANIZAR ETIQUETAS
          </Button>
          {busy && (
            <div className="flex min-w-[240px] flex-1 items-center gap-3" aria-live="polite" data-testid="processing-indicator">
              <Progress value={progress < 100 ? progress : 100} className="h-2 flex-1" />
              <span className="text-sm text-slate-600">{progress < 100 ? `Enviando ${progress}%` : "Lendo e organizando páginas..."}</span>
            </div>
          )}
        </div>
      </section>

      {job && <JobResult job={job} onJob={setJob} />}

      <section className="section space-y-4" data-testid="recent-jobs">
        <h3 className="font-heading text-lg font-bold text-slate-900">Últimos arquivos processados</h3>
        <JobsTable jobs={recent} onDeleted={loadRecent} />
      </section>
    </div>
  );
}
