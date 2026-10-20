import { Link, useParams } from "react-router-dom";
import { availableSources, defaultWindow, instituteByName } from "../data";
import { sourceNames } from "../publications";

const format = value => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 }).format(value);
const metrics = [
  ["Faculty with a DBLP profile", institute => institute.faculty],
  ...availableSources.map(source => [`Unique ${sourceNames[source] || source} papers`, institute => institute.totals[source].papers]),
  ["Unique papers, all sources", institute => institute.totals.all.papers],
  ["Faculty paper count, all sources", institute => institute.totals.all.faculty_papers],
  ["Adjusted credit, CSRankings", institute => institute.totals.csrankings.adjusted],
  ["CSRankings papers per faculty", institute => institute.faculty ? institute.totals.csrankings.papers / institute.faculty : 0],
];

export default function ComparePage() {
  const { uni1, uni2 } = useParams();
  const first = instituteByName(uni1), second = instituteByName(uni2);
  return <div className="page"><Link className="back-link" to="/">← All institutes</Link>
    <p className="eyebrow">Side by side / {defaultWindow[0]}–{defaultWindow[1]} inclusive</p><h1>Compare institutes</h1>
    {!first || !second || uni1 === uni2 ? <section className="panel"><div className="panel-heading"><h2>Select two different institutes</h2><Link to="/#institutes">Return to selection →</Link></div></section> :
      <section className="panel"><div className="table-scroll"><table>
        <thead><tr><th scope="col">Metric</th>{[first, second].map(institute => <th scope="col" className="numeric" key={institute.slug}><Link to={`/institute/${encodeURIComponent(institute.name)}`}>{institute.name}</Link></th>)}</tr></thead>
        <tbody>{metrics.map(([label, value]) => <tr key={label}><th scope="row">{label}</th>{[first, second].map(institute => <td className="numeric" key={institute.slug}>{format(value(institute))}</td>)}</tr>)}</tbody>
      </table></div>
      <div className="table-footer">Unique papers count each DBLP paper once per institute. Faculty paper count credits each faculty author. Adjusted credit sums 1/N per faculty author on N-author papers.</div></section>}
  </div>;
}
