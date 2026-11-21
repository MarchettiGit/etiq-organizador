import { useRef, useState } from "react";
import { FileText, UploadCloud, X } from "lucide-react";

export const UploadZone = ({ file, onFile, disabled }) => {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (!disabled && e.dataTransfer.files?.[0]) onFile(e.dataTransfer.files[0]);
  };

  return (
    <div
      className={`drop-zone flex cursor-pointer flex-col items-center justify-center gap-3 px-6 py-14 text-center ${dragging ? "dragging" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      data-testid="upload-zone"
    >
      <input ref={inputRef} type="file" accept="application/pdf,.pdf" className="hidden"
        data-testid="upload-input"
        onChange={(e) => { if (e.target.files?.[0]) onFile(e.target.files[0]); e.target.value = ""; }} />
      {file ? (
        <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3" data-testid="selected-file">
          <FileText className="h-6 w-6 text-blue-600" />
          <div className="text-left">
            <div className="font-medium text-slate-900">{file.name}</div>
            <div className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
          </div>
          {!disabled && (
            <button type="button" aria-label="Remover arquivo" data-testid="remove-file-button"
              className="ml-2 rounded p-1 text-slate-500 hover:bg-slate-200"
              onClick={(e) => { e.stopPropagation(); onFile(null); }}>
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      ) : (
        <>
          <UploadCloud className="h-14 w-14 text-slate-400" />
          <div className="font-heading text-lg font-bold text-slate-900">Arraste o PDF do Up Seller aqui</div>
          <div className="text-sm text-slate-500">ou clique para selecionar o arquivo (somente PDF)</div>
        </>
      )}
    </div>
  );
};
