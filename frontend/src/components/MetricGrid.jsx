import React from 'react';
import { Eye, Gauge, Sunrise, Sunset, ShieldAlert } from 'lucide-react';

export default function MetricGrid({ weather }) {
  const hourly = weather.hourly;
  const daily = weather.daily;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-7xl mx-auto mb-6">
      <div className="glass-panel p-5 flex flex-col justify-between h-36">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold tracking-wider uppercase">UV Index</span>
          <ShieldAlert className="w-5 h-5 text-amber-500" />
        </div>
        <div>
          <div className="text-2xl font-bold text-slate-800 dark:text-white">{daily.uv_index_max[0]}</div>
          <div className="text-xs text-emerald-500 font-medium mt-1">Safe protection tier</div>
        </div>
      </div>

      <div className="glass-panel p-5 flex flex-col justify-between h-36">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold tracking-wider uppercase">Visibility</span>
          <Eye className="w-5 h-5 text-blue-500" />
        </div>
        <div>
          <div className="text-2xl font-bold text-slate-800 dark:text-white">{(hourly.visibility[0] / 1000).toFixed(1)} km</div>
          <div className="text-xs text-slate-400 mt-1">Clear atmospheric horizon</div>
        </div>
      </div>

      <div className="glass-panel p-5 flex flex-col justify-between h-36">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold tracking-wider uppercase">Pressure</span>
          <Gauge className="w-5 h-5 text-purple-500" />
        </div>
        <div>
          <div className="text-2xl font-bold text-slate-800 dark:text-white">{Math.round(weather.current.pressure_msl)} hPa</div>
          <div className="text-xs text-slate-400 mt-1">Stable local pressure zone</div>
        </div>
      </div>

      <div className="glass-panel p-5 flex flex-col justify-between h-36">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold tracking-wider uppercase">Sun Cycle</span>
          <Sunrise className="w-5 h-5 text-orange-400" />
        </div>
        <div className="text-xs text-slate-600 dark:text-slate-300 space-y-0.5">
          <div>Rise: {daily.sunrise[0].split('T')[1]}</div>
          <div>Set: {daily.sunset[0].split('T')[1]}</div>
        </div>
      </div>
    </div>
  );
}
