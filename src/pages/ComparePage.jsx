import React from "react";
import { useParams, Link } from "react-router-dom";

const ComparePage = () => {
  const { uni1, uni2 } = useParams();

  const data = {
    "IIT Delhi": { papers: 420, citations: 12000, hIndex: 80 },
    "IIT Bombay": { papers: 410, citations: 11000, hIndex: 78 },
    "IISc": { papers: 390, citations: 13000, hIndex: 85 },
    "IIIT Delhi": { papers: 142, citations: 4000, hIndex: 45 },
  };

  const u1 = data[uni1];
  const u2 = data[uni2];

  // ✅ safety check
  if (!u1 || !u2) {
    return (
      <div style={{ padding: "40px" }}>
        <h2>Invalid comparison</h2>
        <Link to="/">Go Back</Link>
      </div>
    );
  }

  return (
    <div style={{ background: "#f5f7fa", minHeight: "100vh", padding: "40px" }}>
      <div style={{ maxWidth: "900px", margin: "auto" }}>

        <Link to="/" style={{ color: "#2b6cb0", textDecoration: "none" }}>
          ← Back to Rankings
        </Link>

        <div style={{
          background: "white",
          padding: "30px",
          borderRadius: "10px",
          marginTop: "20px",
          marginBottom: "20px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
          textAlign: "center"
        }}>
          <h1 style={{ fontSize: "32px", color: "#1a202c" }}>
            {uni1} vs {uni2}
          </h1>
        </div>

        <table style={{ width: "100%", background: "white" }}>
          <thead>
            <tr>
              <th>Metric</th>
              <th>{uni1}</th>
              <th>{uni2}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Total Papers</td>
              <td>{u1.papers}</td>
              <td>{u2.papers}</td>
            </tr>
            <tr>
              <td>Citations</td>
              <td>{u1.citations}</td>
              <td>{u2.citations}</td>
            </tr>
            <tr>
              <td>H-Index</td>
              <td>{u1.hIndex}</td>
              <td>{u2.hIndex}</td>
            </tr>
          </tbody>
        </table>

      </div>
    </div>
  );
};

export default ComparePage;