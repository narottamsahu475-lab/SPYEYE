import React from 'react';
import { CloudRain, Sun, Wind, Droplets, Compass } from 'lucide-react';

export default function CurrentHero({ weather, locationName }) {
  const current = weather.current;
  const daily = weather.daily;

  return (
    <div className="glass-panel p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-6 w-full max-w-7xl mx-auto mb-6">
      <div className="space-y-2 text-center md:text-left">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-800 dark:text-white">{locationName}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">Current Weather Status</p>
        <div className="flex items-baseline justify-center md:justify-start gap-2 pt-4">
          <span className="text-6xl md:text-8xl font-black tracking-tighter text-slate-800 dark:text-white">
            {Math.round(current.temperature_2m)}°
          </span>
          <span className="text-xl font-medium text-slate-400">
            / {Math.round(daily.temperature_2m_max[0])}°
          </span>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center p-4 rounded-full bg-slate-100/50 dark:bg-slate-800/40 w-40 h-40 border border-white/40">
        <Sun className="w-16 h-16 text-amber-500 animate-pulse" />
        <span className="text-sm font-semibold mt-2 text-slate-700 dark:text-slate-300">
          {current.is_day ? "Daylight" : "Nighttime"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 w-full md:w-auto min-w-[280px]">
        <div className="bg-white/50 dark:bg-slate-800/30 p-4 rounded-2xl flex items-center gap-3">
          <Droplets className="w-5 h-5 text-blue-500" />
          <div>
            <div className="text-xs text-slate-400">Humidity</div>
            <div className="text-sm font-bold text-slate-700 dark:text-white">{current.relative_humidity_2m}%</div>
          </div>
        </div>
        <div className="bg-white/50 dark:bg-slate-800/30 p-4 rounded-2xl flex items-center gap-3">
          <Wind className="w-5 h-5 text-teal-500" />
          <div>
            <div className="text-xs text-slate-400">Wind Speed</div>
            <div className="text-sm font-bold text-slate-700 dark:text-white">{current.wind_speed_10m} km/h</div>
          </div>
        </div>
        <div className="bg-white/50 dark:bg-slate-800/30 p-4 rounded-2xl flex items-center gap-3">
          <Compass className="w-5 h-5 text-indigo-500" />
          <div>
            <div className="text-xs text-slate-400">Feels Like</div>
            <div className="text-sm font-bold text-slate-700 dark:text-white">{Math.round(current.apparent_temperature)}°C</div>
          </div>
        </div>
        <div className="bg-white/50 dark:bg-slate-800/30 p-4 rounded-2xl flex items-center gap-3">
          <CloudRain className="w-5 h-5 text-sky-500" />
          <div>
            <div className="text-xs text-slate-400">Precipitation</div>
            <div className="text-sm font-bold text-slate-700 dark:text-white">{current.precipitation} mm</div>
          </div>
        </div>
      </div>
    </div>
  );
}
