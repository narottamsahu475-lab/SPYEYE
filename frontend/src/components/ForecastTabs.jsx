import React from 'react';
import { Cloud, Calendar } from 'lucide-react';

export default function ForecastTabs({ daily }) {
  return (
    <div className="glass-panel p-6 w-full max-w-7xl mx-auto mb-6">
      <div className="flex items-center gap-2 mb-4 border-b border-slate-100 dark:border-slate-800 pb-3">
        <Calendar className="w-5 h-5 text-blue-500" />
        <h3 className="text-md font-bold text-slate-700 dark:text-slate-200">10-Day Extended Forecast Plan</h3>
      </div>
      
      <div className="flex flex-col divide-y divide-slate-100 dark:divide-slate-800/60">
        {daily.time.map((time, idx) => (
          <div key={idx} className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0">
            <div className="w-28 font-medium text-sm text-slate-600 dark:text-slate-300">
              {new Date(time).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
            </div>
            <div className="flex items-center gap-2 text-slate-400 w-24">
              <Cloud className="w-4 h-4 text-slate-400" />
              <span className="text-xs">{daily.precipitation_probability_max[idx]}% rain</span>
            </div>
            <div className="flex items-center gap-3 text-sm font-semibold">
              <span className="text-slate-800 dark:text-white">{Math.round(daily.temperature_2m_max[idx])}°</span>
              <span className="text-slate-400 dark:text-slate-500">{Math.round(daily.temperature_2m_min[idx])}°</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
