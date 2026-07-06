import React, { useState, useEffect, useRef } from 'react';
import { Search, Sun, Moon, MapPin, Settings } from 'lucide-react';

export default function Navigation({ onSelectLocation, theme, toggleTheme }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [history, setHistory] = useState(() => JSON.parse(localStorage.getItem('weather_history') || '[]'));
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (query.length < 3) {
      setSuggestions([]);
      return;
    }
    const delayDebounce = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        setSuggestions(data || []);
      } catch (e) {
        console.error("Failed fetching locations", e);
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [query]);

  const handleSelect = (loc) => {
    const locName = `${loc.name}, ${loc.admin1 || ''} (${loc.country})`;
    onSelectLocation(loc.latitude, loc.longitude, locName);
    
    const updatedHistory = [locName, ...history.filter(i => i !== locName)].slice(0, 5);
    setHistory(updatedHistory);
    localStorage.setItem('weather_history', JSON.stringify(updatedHistory));
    
    setShowDropdown(false);
    setQuery('');
  };

  const getUserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        onSelectLocation(pos.coords.latitude, pos.coords.longitude, "Current GPS Location");
      });
    }
  };

  return (
    <nav className="relative z-50 flex items-center justify-between w-full gap-4 p-4 glass-panel max-w-7xl mx-auto mb-6">
      <div className="flex items-center gap-2 font-bold text-xl tracking-tight text-slate-800 dark:text-white">
        <Sun className="w-6 h-6 text-amber-500 animate-spin-slow" />
        <span>AURA<span className="text-blue-500 font-light">Weather</span></span>
      </div>

      <div ref={dropdownRef} className="relative flex-1 max-w-xl">
        <div className="relative flex items-center bg-slate-100 dark:bg-slate-800 rounded-full px-4 py-2 border border-transparent focus-within:border-blue-400 dark:focus-within:border-blue-500 transition-all">
          <Search className="w-5 h-5 text-slate-400 mr-2" />
          <input
            type="text"
            placeholder="Search city, district, state..."
            value={query}
            onChange={(e) => { setQuery(e.target.value); setShowDropdown(true); }}
            onFocus={() => setShowDropdown(true)}
            className="w-full bg-transparent border-none outline-none text-slate-800 dark:text-slate-100 placeholder-slate-400 text-sm"
          />
        </div>

        {showDropdown && (
          <div className="absolute top-full left-0 w-full mt-2 glass-panel p-2 overflow-hidden shadow-2xl max-h-80 overflow-y-auto custom-scrollbar">
            {suggestions.map((loc, idx) => (
              <button
                key={idx}
                onClick={() => handleSelect(loc)}
                className="w-full text-left px-4 py-3 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl text-sm text-slate-700 dark:text-slate-300 transition-colors"
              >
                {loc.name}, <span className="text-xs text-slate-400">{loc.admin1} ({loc.country})</span>
              </button>
            ))}
            {suggestions.length === 0 && history.length > 0 && (
              <div>
                <div className="text-xs font-semibold px-4 py-2 text-slate-400 uppercase tracking-wider">Recent Searches</div>
                {history.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => { onSelectLocation(null, null, item, true); setShowDropdown(false); }}
                    className="w-full text-left px-4 py-2.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl text-sm text-slate-600 dark:text-slate-400"
                  >
                    {item}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button onClick={getUserLocation} className="p-2.5 bg-slate-100 dark:bg-slate-800 rounded-full hover:scale-105 active:scale-95 transition-all text-slate-700 dark:text-slate-300">
          <MapPin className="w-5 h-5" />
        </button>
        <button onClick={toggleTheme} className="p-2.5 bg-slate-100 dark:bg-slate-800 rounded-full hover:scale-105 active:scale-95 transition-all text-slate-700 dark:text-slate-300">
          {theme === 'dark' ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>
    </nav>
  );
}
