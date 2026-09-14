import { Link, useParams } from "react-router-dom";

const data = {
  "IIT Delhi": { papers: 420, citations: 12000, hIndex: 80 },
  "IIT Bombay": { papers: 410, citations: 11000, hIndex: 78 },
  "IISc": { papers: 390, citations: 13000, hIndex: 85 },
  "IIIT Delhi": { papers: 142, citations: 4000, hIndex: 45 },
};

export default function ComparePage() {
  const { uni1, uni2 } = useParams();
  const first = data[uni1], second = data[uni2];
  return <div className="page"><Link className="back-link" to="/">← All institutes</Link>
    <p className="eyebrow">Side by side / Sample data</p><h1>Compare institutes</h1>
    <p className="notice">This comparison uses placeholders. Values are not research results.</p>
    {!first || !second || uni1 === uni2 ? <section className="panel"><h2>Select two different institutes</h2><Link to="/">Return to selection →</Link></section> :
      <section className="panel"><div className="table-scroll"><table>
        <thead><tr><th scope="col">Sample metric</th><th scope="col">{uni1}</th><th scope="col">{uni2}</th></tr></thead>
        <tbody>{[["papers","Papers"],["citations","Citations"],["hIndex","H-index"]].map(([key,label]) => <tr key={key}><th scope="row">{label}</th><td>{first[key].toLocaleString()}</td><td>{second[key].toLocaleString()}</td></tr>)}</tbody>
      </table></div></section>}
  </div>;
}
