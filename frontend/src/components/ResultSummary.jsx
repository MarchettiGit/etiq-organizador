import { useState } from "react";
import { toast } from "sonner";
import { Download, Loader2, RefreshCw, ShieldCheck, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, downloadJob, errorMessage, formatDate } from "@/lib/api";

const Stat = ({ label, value, tone = "text-slate-900", testId }) => (
  <div className="rounded-xl border border-slate-200 bg-white p-4">
    <div className="label-caps">{label}</div>
    <div className={`font-heading mt-1 text-3xl font-extrabold ${tone}`} data-testid={testId}>{value}</div>
  </div>
);

export const ResultSummary = ({ job, onJob }) => {
  const [downloading, setDownloading] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);

  const download = async () => {
    setDownloading(true);
    try {
      await downloadJob(job);
      toast.success("PDF organizado baixado");
    } catch (e) {
      toast.error(await errorMessage(e, "Falha ao baixar o PDF"));
    } finally {
      setDownloading(false);
    }
  };

  const reanalyze = async () => {
    setReanalyzing(true);
    try {
      const { data } = await api.post(`/jobs/${job.id}/reanalyze`);
      onJob(data);
      toast.success("Etiquetas reanalisadas com as configurações atuais");
    } catch (e) {
      toast.error(await errorMessage(e));
    } finally {
      setReanalyzing(false);
    }
  };

  return (
    <section className="section fade-up space-y-5" data-testid="result-summary">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="label-caps">Resultado da organização</div>
          <h2 className="font-heading mt-1 text-xl font-bold text-slate-900" data-testid="result-filename">{job.filename}</h2>
          <div className="text-sm text-slate-500">{job.user_name} · {formatDate(job.created_at)}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={reanalyze} disabled={reanalyzing} data-testid="reanalyze-button">
            {reanalyzing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            Reanalisar
          </Button>
          <Button onClick={download} disabled={downloading || !job.file_available}
            className="h-11 bg-blue-600 px-6 font-semibold hover:bg-blue-700" data-testid="download-button">
            {downloading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
            BAIXAR PDF ORGANIZADO
          </Button>
        </div>
      </div>
      {!job.file_available && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800" data-testid="file-expired-alert">
          O PDF original não está mais no servidor (arquivos temporários são apagados automaticamente). Envie o arquivo novamente para baixar.
        </div>
      )}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <Stat label="Páginas" value={job.total_pages} testId="stat-pages" />
        <Stat label="Etiquetas" value={job.labels_count} testId="stat-labels" />
        <Stat label="Identificadas" value={job.identified} testId="stat-identified" />
        <Stat label="Classificadas" value={job.classified} tone="text-emerald-700" testId="stat-classified" />
        <Stat label="Para revisão" value={job.review} tone={job.review ? "text-amber-600" : "text-slate-900"} testId="stat-review" />
        <Stat label="Classificação" value={`${job.percent}%`} tone="text-blue-700" testId="stat-percent" />
      </div>
      {job.integrity && (
        <div className={`flex items-center gap-2 text-sm ${job.integrity.ok ? "text-emerald-700" : "text-red-700"}`} data-testid="integrity-info">
          {job.integrity.ok ? <ShieldCheck className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          {job.integrity.final_pages} de {job.integrity.original_pages} páginas preservadas no PDF final — apenas a ordem foi alterada.
        </div>
      )}
    </section>
  );
};
