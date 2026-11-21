import { useState } from "react";
import { ArrowDown, ArrowUp, GripVertical, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const move = (list, from, to) => {
  const next = [...list];
  const [it] = next.splice(from, 1);
  next.splice(to, 0, it);
  return next;
};

const Row = ({ item, i, total, prefix, onChange, onMove, onRemove, drag }) => (
  <li draggable onDragStart={() => drag.start(i)} onDragOver={(e) => e.preventDefault()} onDrop={() => drag.drop(i)}
    className="flex flex-wrap items-center gap-2 bg-white px-3 py-2" data-testid={`${prefix}-item-${i}`}>
    <GripVertical className="h-4 w-4 cursor-grab text-slate-400" />
    <span className="font-data w-7 text-right text-xs text-slate-400">{i + 1}</span>
    <Input value={item.name} onChange={(e) => onChange(i, { ...item, name: e.target.value })}
      className="h-9 w-56 font-medium" data-testid={`${prefix}-name-${i}`} />
    <Input value={item.aliases.join(", ")} placeholder="Variações / abreviações separadas por vírgula"
      onChange={(e) => onChange(i, { ...item, aliases: e.target.value.split(",").map((s) => s.trimStart()) })}
      className="font-data h-9 min-w-[220px] flex-1 text-xs" data-testid={`${prefix}-aliases-${i}`} />
    <Button size="icon" variant="ghost" aria-label="Mover para cima" disabled={i === 0} onClick={() => onMove(i, i - 1)} data-testid={`${prefix}-up-${i}`}>
      <ArrowUp className="h-4 w-4" />
    </Button>
    <Button size="icon" variant="ghost" aria-label="Mover para baixo" disabled={i === total - 1} onClick={() => onMove(i, i + 1)} data-testid={`${prefix}-down-${i}`}>
      <ArrowDown className="h-4 w-4" />
    </Button>
    <Button size="icon" variant="ghost" aria-label="Remover" onClick={() => onRemove(i)} data-testid={`${prefix}-remove-${i}`}>
      <Trash2 className="h-4 w-4 text-red-600" />
    </Button>
  </li>
);

export const ListEditor = ({ items, onChange, prefix, addLabel }) => {
  const [dragFrom, setDragFrom] = useState(null);
  const [newName, setNewName] = useState("");
  const drag = { start: setDragFrom, drop: (to) => { if (dragFrom !== null) onChange(move(items, dragFrom, to)); setDragFrom(null); } };

  const add = () => {
    const name = newName.trim();
    if (!name) return;
    onChange([...items, { name, aliases: [name.toUpperCase()] }]);
    setNewName("");
  };

  return (
    <div className="space-y-3">
      <ul className="divide-y divide-slate-100 overflow-hidden rounded-lg border border-slate-200">
        {items.map((it, i) => (
          <Row key={i} item={it} i={i} total={items.length} prefix={prefix} drag={drag}
            onChange={(idx, v) => onChange(items.map((x, j) => (j === idx ? v : x)))}
            onMove={(a, b) => onChange(move(items, a, b))}
            onRemove={(idx) => onChange(items.filter((_, j) => j !== idx))} />
        ))}
      </ul>
      <div className="flex gap-2">
        <Input value={newName} onChange={(e) => setNewName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder={addLabel} className="h-10 max-w-xs" data-testid={`${prefix}-new-input`} />
        <Button variant="outline" onClick={add} data-testid={`${prefix}-add-button`}>
          <Plus className="mr-2 h-4 w-4" /> Adicionar
        </Button>
      </div>
    </div>
  );
};
