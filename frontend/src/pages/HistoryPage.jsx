import { useCallback, useEffect, useState } from "react";
import { JobsTable } from "@/components/JobsTable";
import { api } from "@/lib/api";

export default function HistoryPage() {
  const [jobs, setJobs] = useState([]);
  const load = useCallback(() => {
    api.get("/jobs", { params: { limit: 200 } }).then((r) => setJobs(r.data)).catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-4xl font-extrabold tracking-tight text-slate-900">Histórico</h1>
        <p className="text-sm text-slate-500">
          Todos os processamentos da empresa. Clique em uma linha para ver o resultado e corrigir etiquetas.
          O PDF fica disponível para download por 24 horas; depois apenas os números são mantidos.
        </p>
      </div>
      <section className="section" data-testid="history-section">
        <JobsTable jobs={jobs} onDeleted={load} />
      </section>
    </div>
  );
}
