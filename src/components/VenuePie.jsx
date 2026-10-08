import { venueDistribution } from "../publications";

const colors = ["#126c53", "#369b83", "#75b89c", "#a6cc78", "#d7b456", "#bb8466", "#6589b4", "#9ba7a2"];
export default function VenuePie({ papers, compact = false }) {
  const distribution = venueDistribution(papers);
  const slices = distribution.length > 8
    ? [...distribution.slice(0, 7), { name: `Other (${distribution.length - 7} venues)`, count: distribution.slice(7).reduce((sum, item) => sum + item.count, 0) }]
    : distribution;
  const total = slices.reduce((sum, item) => sum + item.count, 0);
  if (!total) return <p className="empty">No loaded papers to chart.</p>;
  const paths = slices.map((item, index) => {
    const start = -Math.PI / 2 + slices.slice(0, index).reduce((sum, slice) => sum + slice.count, 0) / total * 2 * Math.PI;
    const angle = start + item.count / total * 2 * Math.PI;
    const point = value => `${110 + 98 * Math.cos(value)},${110 + 98 * Math.sin(value)}`;
    return { ...item, color: colors[index], path: `M110,110 L${point(start)} A98,98 0 ${item.count / total > 0.5 ? 1 : 0},1 ${point(angle)} Z` };
  });
  return <div className={`venue-pie ${compact ? "compact" : ""}`}>
    <div className="pie-graphic"><svg viewBox="0 0 220 220" role="img" aria-label={`Publication venues for ${total} loaded papers`}>
      {paths.map(item => paths.length === 1
        ? <circle key={item.name} cx="110" cy="110" r="98" fill={item.color}><title>{item.name}: {item.count} papers</title></circle>
        : <path key={item.name} d={item.path} fill={item.color} stroke="white" strokeWidth="1.5"><title>{item.name}: {item.count} ({Math.round(item.count / total * 100)}%)</title></path>)}
    </svg><span className="quiet">{total} loaded papers</span></div>
    <ul className="pie-legend">{paths.map(item => <li key={item.name}><span className="legend-dot" style={{ background: item.color }} /><span>{item.name}</span><strong>{item.count}</strong></li>)}</ul>
    {!compact && distribution.length > 8 && <details className="all-venues"><summary>View all {distribution.length} venues</summary><ul className="pie-legend">{distribution.map(item => <li key={item.name}><span>{item.name}</span><strong>{item.count}</strong></li>)}</ul></details>}
  </div>;
}
