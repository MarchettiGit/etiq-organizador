import { useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { Tags, UserRound } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";
import { Input } from "@/components/ui/input";
import { USER_KEY } from "@/lib/api";
import HomePage from "@/pages/HomePage";
import HistoryPage from "@/pages/HistoryPage";
import SettingsPage from "@/pages/SettingsPage";
import JobPage from "@/pages/JobPage";

const links = [
  { to: "/", label: "Início", id: "nav-home" },
  { to: "/historico", label: "Histórico", id: "nav-history" },
  { to: "/configuracoes", label: "Configurações", id: "nav-settings" },
];

const Header = () => {
  const [name, setName] = useState(() => localStorage.getItem(USER_KEY) || "");
  const onName = (v) => {
    setName(v);
    localStorage.setItem(USER_KEY, v);
  };
  return (
    <header className="app-header" data-testid="app-header">
      <div className="flex items-center gap-3">
        <div className="brand-mark"><Tags className="h-5 w-5" /></div>
        <span className="font-heading text-lg font-extrabold tracking-tight text-slate-900" data-testid="app-title">
          Organizador de Etiquetas
        </span>
      </div>
      <nav className="flex items-center gap-1">
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} end data-testid={l.id}
            className={({ isActive }) => `nav-link ${isActive ? "nav-link-active" : ""}`}>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <label className="flex items-center gap-2 text-sm text-slate-600">
        <UserRound className="h-4 w-4" />
        <Input value={name} onChange={(e) => onName(e.target.value)} placeholder="Seu nome"
          className="h-9 w-40 bg-white" data-testid="user-name-input" />
      </label>
    </header>
  );
};

function App() {
  return (
    <BrowserRouter>
      <Header />
      <main className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/historico" element={<HistoryPage />} />
          <Route path="/configuracoes" element={<SettingsPage />} />
          <Route path="/resultado/:id" element={<JobPage />} />
        </Routes>
      </main>
      <Toaster richColors position="bottom-right" />
    </BrowserRouter>
  );
}

export default App;
