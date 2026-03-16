import React from "react";
import { useParams } from "react-router-dom";
import AreaChart from "../components/AreaChart";

const InstitutePage = () => {

  const { name } = useParams();

  const institute = {
    name: name,
    totalPapers: 1245,
    citations: 15200,
    hIndex: 72,
    topAreas: [
      { area: "Machine Learning", papers: 320 },
      { area: "Computer Vision", papers: 210 },
      { area: "Distributed Systems", papers: 150 },
      { area: "Databases", papers: 120 },
    ],
    topVenues: [
      { venue: "NeurIPS", papers: 45 },
      { venue: "ICML", papers: 40 },
      { venue: "CVPR", papers: 38 },
      { venue: "SIGMOD", papers: 25 },
    ],
    topAuthors: [
      { name: "Author A", papers: 85 },
      { name: "Author B", papers: 70 },
      { name: "Author C", papers: 65 },
    ],
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>

      <h1>{institute.name}</h1>
      <p>Computer Science Research Overview</p>

      <h3>Total Papers: {institute.totalPapers}</h3>
      <h3>Citations: {institute.citations}</h3>
      <h3>H-Index: {institute.hIndex}</h3>

      <h2 style={{ marginTop: "40px" }}>Research Areas</h2>

      <AreaChart areas={institute.topAreas} />

      <h2 style={{ marginTop: "40px" }}>Top Venues</h2>

      {institute.topVenues.map((v, i) => (
        <p key={i}>{v.venue} — {v.papers}</p>
      ))}

      <h2 style={{ marginTop: "40px" }}>Top Authors</h2>

      {institute.topAuthors.map((a, i) => (
        <p key={i}>{a.name} — {a.papers}</p>
      ))}

    </div>
  );
};

export default InstitutePage;