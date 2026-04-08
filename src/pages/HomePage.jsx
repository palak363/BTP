import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const HomePage = () => {
  const [rankingType, setRankingType] = useState({
    csr: true,
    coreAStar: false,
    coreA: false
  });

  const [uni1, setUni1] = useState("");
  const [uni2, setUni2] = useState("");
  const navigate = useNavigate();

  const rankingData = [
    { institute: "IIT Delhi", papers: 420 },
    { institute: "IIT Bombay", papers: 410 },
    { institute: "IISc", papers: 390 },
    { institute: "IIIT Delhi", papers: 142 }
  ];

  // 🔥 COMMON HEADING STYLE
  const headingStyle = {
    fontSize: "28px",
    fontWeight: "700",
    color: "#1a202c",
    textAlign: "center",
    margin: 0,
    marginBottom: "16px"
  };

  // 🔥 Reusable button style
  const btnStyle = (active) => ({
    padding: "8px 16px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    background: active ? "#2b6cb0" : "white",
    color: active ? "white" : "black",
    cursor: "pointer"
  });

  // 🔥 Safe toggle
  const toggle = (key) => {
    setRankingType(prev => {
      const updated = { ...prev, [key]: !prev[key] };
      return updated.csr || updated.coreAStar || updated.coreA ? updated : prev;
    });
  };

  return (
    <div style={{ background: "#f5f7fa", minHeight: "100vh", padding: "40px" }}>
      <div style={{ maxWidth: "900px", margin: "auto" }}>

        {/* HEADER */}
        <div style={{
          background: "white",
          padding: "40px 30px",
          borderRadius: "12px",
          marginBottom: "20px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.06)",
          textAlign: "center"
        }}>
          
          <h1 style={{ 
            margin: 0,
            fontSize: "42px",
            fontWeight: "700",
            letterSpacing: "0.5px",
            color: "#1a202c"
          }}>
            India{" "}
            <span style={{ 
              color: "#2b6cb0",
              textDecoration: "underline",
              textDecorationThickness: "3px",
              textUnderlineOffset: "6px"
            }}>
              CS Research
            </span>
          </h1>

          <p style={{ 
            color: "#555",
            marginTop: "12px",
            fontSize: "16px"
          }}>
            Analyze computer science research output of Indian institutes
          </p>
        </div>

        {/* RANKING CRITERIA */}
        <div style={{
          background: "white",
          padding: "30px 20px",
          borderRadius: "10px",
          marginBottom: "20px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.05)"
        }}>
          <h2 style={headingStyle}>
            Ranking Criteria
          </h2>

          <p style={{
            fontSize: "14px",
            color: "#4a5568",
            marginBottom: "20px",
            textAlign: "center"
          }}>
            Select ranking sources and conference tiers
          </p>

          <div style={{
            display: "flex",
            justifyContent: "center",
            gap: "12px",
            flexWrap: "wrap"
          }}>

            <button onClick={() => toggle("csr")} style={btnStyle(rankingType.csr)}>
              CSRankings
            </button>

            <button onClick={() => toggle("coreAStar")} style={btnStyle(rankingType.coreAStar)}>
              CORE A*
            </button>

            <button onClick={() => toggle("coreA")} style={btnStyle(rankingType.coreA)}>
              CORE A
            </button>

          </div>
        </div>

        {/* COMPARE UNIVERSITIES */}
        <div style={{
          background: "white",
          padding: "30px 20px",
          borderRadius: "10px",
          marginBottom: "20px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.05)"
        }}>
          <h2 style={headingStyle}>
            Compare Universities
          </h2>

          <div style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: "12px",
            flexWrap: "wrap"
          }}>

            <select
              value={uni1}
              onChange={(e) => setUni1(e.target.value)}
              style={{
                padding: "10px",
                flex: 1,
                minWidth: "220px",
                borderRadius: "6px",
                border: "1px solid #ccc"
              }}
            >
              <option value="">Select University 1</option>
              {rankingData.map((inst, i) => (
                <option key={i} value={inst.institute}>
                  {inst.institute}
                </option>
              ))}
            </select>

            <select
              value={uni2}
              onChange={(e) => setUni2(e.target.value)}
              style={{
                padding: "10px",
                flex: 1,
                minWidth: "220px",
                borderRadius: "6px",
                border: "1px solid #ccc"
              }}
            >
              <option value="">Select University 2</option>
              {rankingData.map((inst, i) => (
                <option key={i} value={inst.institute}>
                  {inst.institute}
                </option>
              ))}
            </select>

            <button
              onClick={() => {
                if (uni1 && uni2 && uni1 !== uni2) {
                  navigate(`/compare/${uni1}/${uni2}`);
                } else {
                  alert("Select two different universities");
                }
              }}
              style={{
                padding: "10px 18px",
                background: "#2b6cb0",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: "600"
              }}
            >
              Compare
            </button>

          </div>
        </div>

        {/* TABLE */}
        <div style={{
          background: "white",
          borderRadius: "10px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
          overflow: "hidden"
        }}>
          
          <h2 style={headingStyle}>
            Institute Rankings
          </h2>

          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ background: "#eef2f7" }}>
              <tr>
                <th style={{ padding: "12px", textAlign: "left" }}>Rank</th>
                <th style={{ padding: "12px", textAlign: "left" }}>Institute</th>
                <th style={{ padding: "12px", textAlign: "left" }}>Papers</th>
              </tr>
            </thead>

            <tbody>
              {rankingData.map((inst, index) => (
                <tr key={index} style={{ borderTop: "1px solid #eee" }}>
                  <td style={{ padding: "12px", fontWeight: "500" }}>
                    {index + 1}
                  </td>

                  <td style={{ padding: "12px" }}>
                    <Link
                      to={`/institute/${inst.institute}`}
                      style={{
                        color: "#2b6cb0",
                        textDecoration: "none",
                        fontWeight: "500"
                      }}
                    >
                      {inst.institute}
                    </Link>
                  </td>

                  <td style={{ padding: "12px" }}>
                    {inst.papers}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

        </div>

      </div>
    </div>
  );
};

export default HomePage;