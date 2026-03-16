import { useState } from "react";
import { Link } from "react-router-dom";

const HomePage = () => {

  const [rankingType, setRankingType] = useState("csr");

  const rankingData = [
    { institute: "IIT Delhi", papers: 420 },
    { institute: "IIT Bombay", papers: 410 },
    { institute: "IISc", papers: 390 },
    { institute: "IIIT Delhi", papers: 142 }
  ];

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>

      <h1>India CS Research Rankings</h1>

      <p>
        A platform to analyze computer science research output of Indian institutes.
      </p>

      <h3>Ranking Criteria</h3>

      <label>
        <input
          type="radio"
          checked={rankingType === "csr"}
          onChange={() => setRankingType("csr")}
        />
        CSRankings
      </label>

      <br />

      <label>
        <input
          type="radio"
          checked={rankingType === "core"}
          onChange={() => setRankingType("core")}
        />
        CORE Ranking
      </label>

      <h2 style={{ marginTop: "30px" }}>Institute Rankings</h2>

      <table border="1" cellPadding="10">

        <thead>
          <tr>
            <th>Rank</th>
            <th>Institute</th>
            <th>Papers</th>
          </tr>
        </thead>

        <tbody>

          {rankingData.map((inst, index) => (
            <tr key={index}>

              <td>{index + 1}</td>

              <td>
                <Link to={`/institute/${inst.institute}`}>
                  {inst.institute}
                </Link>
              </td>

              <td>{inst.papers}</td>

            </tr>
          ))}

        </tbody>

      </table>

    </div>
  );
};

export default HomePage;