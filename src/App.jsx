import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import HomePage from "./pages/HomePage";
import InstitutePage from "./pages/InstitutePage";

function App() {

  return (
    <Router>

      <Routes>

        <Route path="/" element={<HomePage />} />

        <Route path="/institute/:name" element={<InstitutePage />} />

      </Routes>

    </Router>
  );

}

export default App;