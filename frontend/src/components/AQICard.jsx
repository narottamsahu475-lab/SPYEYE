import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function AQICard({ aqiData }) {
  const currentAQI = aqiData.current;
  const usAqi = currentAQI.us_aqi;

  const getAqiTier = (val) => {
    if (val <= 50) return { label: "Good", color: "text-emerald-500 bg-emerald-500/10" };
    if (val <= 100) return { label: "Moderate", color: "text-amber-500 bg-amber-500/10" };
    return { label: "Unhealthy", color: "text-rose-500 bg-rose-500/10" };
  };

  const tier = getAqiTier(usAqi);

  return (
    <div className="glass-panel p-6 w-full max-w-7xl mx-auto mb-6 flex flex-col md:flex-row items-center justify-between gap-6">
      <div className="flex items-center gap-4">
        <div className={`p-4 rounded-2xl ${tier.color}`}>
          <ShieldCheck className="w-8 h-8" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-800 dark:text-white">Air Quality Index (AQI)</h3>
          <p className="text-sm text-slate-400">Real-time local tracking metrics</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full md:w-auto flex-1 max-w-2xl">
        <div className="text-center p-3 bg-slate-100/50 dark:bg-slate-800/30 rounded-2xl">
          <div className="text-xs text-slate-400">US AQI Index</div>
          <div className="text-xl font-bold text-slate-700 dark:text-white">{usAqi} ({tier.label})</div>
        </div>
        <div className="text-center p-3 bg-slate-100/50 dark:bg-slate-800/30 rounded-2xl">
          <div className="text-xs text-slate-400">PM2.5</div>
          <div className="text-xl font-bold text-slate-700 dark:text-white">{currentAQI.pm2_5} μg/m³</div>
        </div>
        <div className="text-center p-3 bg-slate-100/50 dark:bg-slate-800/30 rounded-2xl">
          <div className="text-xs text-slate-400">PM10</div>
          <div className="text-xl font-bold text-slate-700 dark:text-white">{currentAQI.pm10} μg/m³</div>
        </div>
        <div className="text-center p-3 bg-slate-100/50 dark:bg-slate-800/30 rounded-2xl">
          <div className="text-xs text-slate-400">Ozone (O₃)</div>
          <div className="text-xl font-bold text-slate-700 dark:text-white">{Math.round(currentAQI.ozone)} μg/m³</div>
        </div>
      </div>
    </div>
  );
}
