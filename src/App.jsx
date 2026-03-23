import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import HomePage from "./pages/HomePage";
import InstitutePage from "./pages/InstitutePage";
import ComparePage from "./pages/ComparePage";

function App() {

  return (
    <Router>

      <Routes>

        <Route path="/" element={<HomePage />} />

        <Route path="/institute/:name" element={<InstitutePage />} />
        <Route path="/compare/:uni1/:uni2" element={<ComparePage />} />

      </Routes>

    </Router>
  );

}

export default App;