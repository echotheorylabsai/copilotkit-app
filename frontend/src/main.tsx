import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Route, Routes, useLocation } from "react-router-dom";
import { CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";
import { demonstrationCatalog } from "./catalog";
import "./globals.css";
import App from "./App";
import TodoPage from "./TodoPage";

function ThemeToggle() {
  // `.dark` on <html> is set pre-paint by the inline script in index.html; this just
  // flips it and persists the choice.
  const [dark, setDark] = useState(() =>
    document.documentElement.classList.contains("dark"),
  );
  const toggle = () => {
    const next = !dark;
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
    setDark(next);
  };
  return (
    <button className="theme-toggle" onClick={toggle} aria-label="Toggle dark mode">
      {dark ? "☀️" : "🌙"}
    </button>
  );
}

function Nav() {
  const { pathname } = useLocation();
  const link = (to: string, label: string) => (
    <Link to={to} className="app-nav-link" aria-current={pathname === to ? "page" : undefined}>
      {label}
    </Link>
  );
  return (
    <nav className="app-nav">
      {link("/", "Chat")}
      {link("/todos", "Todos")}
      <ThemeToggle />
    </nav>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <main className="h-screen w-screen">
      <CopilotKit
        runtimeUrl="/api/copilotkit"
        useSingleEndpoint={false}
        a2ui={{ catalog: demonstrationCatalog }}
      >
        <BrowserRouter>
          <Nav />
          <Routes>
            <Route path="/" element={<App />} />
            <Route path="/todos" element={<TodoPage />} />
          </Routes>
        </BrowserRouter>
      </CopilotKit>
    </main>
  </StrictMode>,
);
