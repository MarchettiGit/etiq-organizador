import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { ResultSummary } from "@/components/ResultSummary";
import { ReviewList } from "@/components/ReviewList";
import { OrderPreview } from "@/components/OrderPreview";
import { CorrectionDialog } from "@/components/CorrectionDialog";

export const JobResult = ({ job, onJob }) => {
  const [settings, setSettings] = useState(null);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    api.get("/settings").then((r) => setSettings(r.data)).catch(async (e) => toast.error(await errorMessage(e)));
  }, [job.id]);

  return (
    <div className="space-y-8" data-testid="job-result">
      <ResultSummary job={job} onJob={onJob} />
      <ReviewList labels={job.labels} onEdit={setEditing} />
      <OrderPreview labels={job.labels} onEdit={setEditing} />
      {settings && (
        <CorrectionDialog job={job} label={editing} settings={settings} onJob={onJob} onClose={() => setEditing(null)} />
      )}
    </div>
  );
};
