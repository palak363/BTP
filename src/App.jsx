import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import InstitutePage from "./pages/InstitutePage";
import ComparePage from "./pages/ComparePage";

export default function App() {
  return <BrowserRouter>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header">
      <Link to="/" className="brand"><span className="brand-mark">iR</span>India Research<span className="beta">BETA</span></Link>
      <nav aria-label="Main navigation"><NavLink to="/" end>Overview</NavLink><NavLink to="/institute/IIIT%20Delhi">IIIT Delhi</NavLink></nav>
      <span className="header-note"><span className="status-dot" />IIITD pilot</span>
    </header>
    <main id="main"><Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/institute/:name" element={<InstitutePage />} />
      <Route path="/compare/:uni1/:uni2" element={<ComparePage />} />
      <Route path="*" element={<div className="page"><h1>Page not found</h1><Link to="/">Back to overview</Link></div>} />
    </Routes></main>
    <footer className="site-footer"><span>India Research / Computer science</span><span>Explore the work behind the numbers.</span></footer>
  </BrowserRouter>;
}
