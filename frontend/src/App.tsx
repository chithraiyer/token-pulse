import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Link, Route, Routes } from "react-router-dom";

import { DemoBanner } from "./components/DemoBanner";
import { useMeta } from "./api/hooks";
import { Overview } from "./pages/Overview";
import { MemberDetail } from "./pages/MemberDetail";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } },
});

function Footer() {
  const { data } = useMeta();
  if (!data) return null;
  return (
    <footer className="footer">
      TokenPulse v{data.tool_version} · spike ×{data.spike_multiple} · retention{" "}
      {data.retention_days}d
    </footer>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        <DemoBanner />
        <header className="topbar">
          <Link to="/" className="brand">
            TokenPulse
          </Link>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/members/:memberId" element={<MemberDetail />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </QueryClientProvider>
  );
}
