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
    <div style={{ background: "#f5f7fa", minHeight: "100vh", padding: "40px" }}>
      <div style={{ maxWidth: "900px", margin: "auto" }}>

        {/* HEADER */}
        <div style={{
          background: "white",
          padding: "30px",
          borderRadius: "12px",
          marginBottom: "20px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.06)"
        }}>
          <h1 style={{
            margin: 0,
            fontSize: "36px",
            fontWeight: "700",
            color: "#1a202c"
          }}>
            {institute.name}
          </h1>

          <p style={{ color: "#555", marginTop: "8px" }}>
            Computer Science Research Overview
          </p>
        </div>

        {/* STATS CARDS */}
        <div style={{
          display: "flex",
          gap: "20px",
          marginBottom: "20px"
        }}>
          <div style={cardStyle}>
            <p style={labelStyle}>Total Papers</p>
            <h2 style={valueStyle}>{institute.totalPapers}</h2>
          </div>

          <div style={cardStyle}>
            <p style={labelStyle}>Citations</p>
            <h2 style={valueStyle}>{institute.citations}</h2>
          </div>

          <div style={cardStyle}>
            <p style={labelStyle}>H-Index</p>
            <h2 style={valueStyle}>{institute.hIndex}</h2>
          </div>
        </div>

        {/* RESEARCH AREAS */}
        <div style={sectionStyle}>
          <h2 style={sectionTitle}>Research Areas</h2>
          <AreaChart areas={institute.topAreas} />
        </div>

        {/* TOP VENUES */}
        <div style={sectionStyle}>
          <h2 style={sectionTitle}>Top Venues</h2>

          {institute.topVenues.map((v, i) => (
            <div key={i} style={rowStyle}>
              <span>{v.venue}</span>
              <span>{v.papers} papers</span>
            </div>
          ))}
        </div>

        {/* TOP AUTHORS */}
        <div style={sectionStyle}>
          <h2 style={sectionTitle}>Top Authors</h2>

          {institute.topAuthors.map((a, i) => (
            <div key={i} style={rowStyle}>
              <span>{a.name}</span>
              <span>{a.papers} papers</span>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
};

/* ---------- STYLES ---------- */

const cardStyle = {
  flex: 1,
  background: "white",
  padding: "20px",
  borderRadius: "10px",
  boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
  textAlign: "center"
};

const labelStyle = {
  color: "#666",
  marginBottom: "5px"
};

const valueStyle = {
  margin: 0,
  color: "#2b6cb0"
};

const sectionStyle = {
  background: "white",
  borderRadius: "10px",
  padding: "20px",
  marginBottom: "20px",
  boxShadow: "0 2px 10px rgba(0,0,0,0.05)"
};

const sectionTitle = {
  marginBottom: "15px",
  color: "#1a202c",
  borderBottom: "1px solid #eee",
  paddingBottom: "8px"
};

const rowStyle = {
  display: "flex",
  justifyContent: "space-between",
  padding: "10px 0",
  borderBottom: "1px solid #f0f0f0"
};

export default InstitutePage;