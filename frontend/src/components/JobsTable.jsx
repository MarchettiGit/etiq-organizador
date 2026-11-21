import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Download, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, downloadJob, errorMessage, formatDate } from "@/lib/api";

export const JobsTable = ({ jobs, onDeleted, showActions = true }) => {
  const navigate = useNavigate();

  const download = async (e, job) => {
    e.stopPropagation();
    try {
      await downloadJob(job);
    } catch (err) {
      toast.error(await errorMessage(err, "Falha ao baixar"));
    }
  };

  const remove = async (e, job) => {
    e.stopPropagation();
    if (!window.confirm(`Excluir o registro de "${job.filename}"?`)) return;
    try {
      await api.delete(`/jobs/${job.id}`);
      toast.success("Registro excluído");
      onDeleted?.(job.id);
    } catch (err) {
      toast.error(await errorMessage(err));
    }
  };

  if (!jobs.length) {
    return <div className="py-6 text-sm text-slate-500" data-testid="jobs-empty">Nenhum arquivo processado ainda.</div>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <Table className="zebra" data-testid="jobs-table">
        <TableHeader className="bg-slate-50">
          <TableRow>
            <TableHead>Arquivo</TableHead>
            <TableHead>Usuário</TableHead>
            <TableHead>Data e hora</TableHead>
            <TableHead className="text-right">Páginas</TableHead>
            <TableHead className="text-right">Classificadas</TableHead>
            <TableHead className="text-right">Revisão</TableHead>
            {showActions && <TableHead className="text-right">Ações</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {jobs.map((j) => (
            <TableRow key={j.id} className="cursor-pointer" onClick={() => navigate(`/resultado/${j.id}`)} data-testid={`job-row-${j.id}`}>
              <TableCell className="font-medium text-slate-900">{j.filename}</TableCell>
              <TableCell>{j.user_name}</TableCell>
              <TableCell className="font-data text-xs">{formatDate(j.created_at)}</TableCell>
              <TableCell className="font-data text-right">{j.total_pages}</TableCell>
              <TableCell className="font-data text-right text-emerald-700">{j.classified}</TableCell>
              <TableCell className={`font-data text-right ${j.review ? "text-amber-600" : ""}`}>{j.review}</TableCell>
              {showActions && (
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button size="icon" variant="ghost" aria-label="Baixar PDF" disabled={!j.file_available}
                      title={j.file_available ? "Baixar PDF organizado" : "Arquivo expirado no servidor"}
                      onClick={(e) => download(e, j)} data-testid={`job-download-${j.id}`}>
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button size="icon" variant="ghost" aria-label="Excluir" onClick={(e) => remove(e, j)} data-testid={`job-delete-${j.id}`}>
                      <Trash2 className="h-4 w-4 text-red-600" />
                    </Button>
                  </div>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
