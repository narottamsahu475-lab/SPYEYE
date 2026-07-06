import React from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler);

export default function WeatherCharts({ hourlyData }) {
  const labels = hourlyData.time.slice(0, 24).map(t => t.split('T')[1]);
  const temperatures = hourlyData.temperature_2m.slice(0, 24);

  const data = {
    labels,
    datasets: [
      {
        fill: true,
        label: 'Temperature Forecast (°C)',
        data: temperatures,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        pointRadius: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false }
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
      y: { grid: { color: 'rgba(148, 163, 184, 0.1)' }, ticks: { color: '#94a3b8' } }
    }
  };

  return (
    <div className="glass-panel p-6 w-full max-w-7xl mx-auto mb-6">
      <h3 className="text-md font-semibold text-slate-700 dark:text-slate-300 mb-4">24-Hour Horizon Timeline</h3>
      <div className="h-64 w-full">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
