import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement
} from "chart.js";

import { Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement);

const AreaChart = ({ areas }) => {

  const data = {
    labels: areas.map(a => a.area),

    datasets: [
      {
        label: "Papers",
        data: areas.map(a => a.papers),
        backgroundColor: "#6C63FF"
      }
    ]
  };

  return (
    <div style={{ width: "600px" }}>
      <Bar data={data} />
    </div>
  );
};

export default AreaChart;