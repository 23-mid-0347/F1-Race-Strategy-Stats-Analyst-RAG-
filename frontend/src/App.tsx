import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import Dashboard from "./pages/Dashboard";
import Standings from "./pages/Standings";
import Races from "./pages/Races";
import RaceDetail from "./pages/RaceDetail";
import ComingSoon from "./pages/ComingSoon";
import Analyst from "./pages/Analyst";

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />

        <div className="main-area">
          <TopBar />

          <main className="page-content">
            <Routes>
              <Route path="/"                element={<Dashboard />} />
              <Route path="/standings"       element={<Standings />} />
              <Route path="/races"           element={<Races />} />
              <Route path="/races/:eventId"  element={<RaceDetail />} />
              <Route path="/drivers"         element={<ComingSoon page="Drivers" />} />
              <Route path="/strategy"        element={<ComingSoon page="Strategy" />} />
              <Route path="/compare"         element={<ComingSoon page="Compare" />} />
              <Route path="/analyst"         element={<Analyst />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;