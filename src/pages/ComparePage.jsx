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
          <h1 style={{
            margin: 0,
            fontSize: "32px",
            fontWeight: "700",
            color: "#1a202c"   // dark visible color
            }}>
            {uni1} vs {uni2}
            </h1>
          <p style={{ color: "#4a5568" }}>
            University Comparison
            </p>
        </div>

        <div style={{
          background: "white",
          borderRadius: "10px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
          overflow: "hidden"
        }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ background: "#eef2f7", color: "#2d3748" }}>
              <tr>
                <th style={{ padding: "12px" }}>Metric</th>
                <th style={{ padding: "12px" }}>{uni1}</th>
                <th style={{ padding: "12px" }}>{uni2}</th>
              </tr>
            </thead>

            <tbody>
              <tr style={row}>
                <td>Total Papers</td>
                <td>{u1.papers}</td>
                <td>{u2.papers}</td>
              </tr>

              <tr style={row}>
                <td>Citations</td>
                <td>{u1.citations}</td>
                <td>{u2.citations}</td>
              </tr>

              <tr style={row}>
                <td>H-Index</td>
                <td>{u1.hIndex}</td>
                <td>{u2.hIndex}</td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
};

const row = {
  borderTop: "1px solid #eee",
  textAlign: "center",
  color: "#2d3748",   // makes all row text visible
};

<td style={{ fontWeight: "600", color: "#2b6cb0" }}>
  {u1.papers}
</td>

export default ComparePage;