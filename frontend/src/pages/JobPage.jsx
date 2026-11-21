import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { JobResult } from "@/components/JobResult";
import { api, errorMessage } from "@/lib/api";

export default function JobPage() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/jobs/${id}`).then((r) => setJob(r.data)).catch(async (e) => setError(await errorMessage(e)));
  }, [id]);

  return (
    <div className="space-y-6">
      <Link to="/historico" className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900" data-testid="back-to-history">
        <ArrowLeft className="h-4 w-4" /> Voltar ao histórico
      </Link>
      {error && <div className="section text-red-700" data-testid="job-error">{error}</div>}
      {!job && !error && <Loader2 className="h-6 w-6 animate-spin text-slate-400" />}
      {job && <JobResult job={job} onJob={setJob} />}
    </div>
  );
}
