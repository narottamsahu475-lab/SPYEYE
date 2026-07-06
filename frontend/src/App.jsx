import React, { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import CurrentHero from './components/CurrentHero';
import MetricGrid from './components/MetricGrid';
import AQICard from './components/AQICard';
import WeatherCharts from './components/WeatherCharts';
import ForecastTabs from './components/ForecastTabs';
import WeatherMap from './components/WeatherMap';
import LiveBackground from './components/LiveBackground';

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [location, setLocation] = useState({ lat: 40.7128, lon: -74.0060, name: "New York, NY (United States)" });
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const fetchWeather = async (lat, lon) => {
    setLoading(true);
    try {
      // Production backend live URL access via env
      const baseUrl = import.meta.env.VITE_API_URL || '';
      const res = await fetch(`${baseUrl}/api/weather?lat=${lat}&lon=${lon}`);
      const data = await res.json();
      setWeatherData(data);
    } catch (e) {
      console.error("Error fetching weather updates.", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather(location.lat, location.lon);
  }, [location.lat, location.lon]);

  const handleSelectLocation = (lat, lon, name, fromHistory = false) => {
    if (fromHistory) {
      setLocation({ lat: 40.7128, lon: -74.0060, name });
    } else {
      setLocation({ lat, lon, name });
    }
  };

  return (
    <div className="min-h-screen w-full bg-[var(--bg-gradient-light)] dark:bg-[var(--bg-gradient-dark)] p-4 md:p-6 transition-all relative">
      {weatherData && (
        <LiveBackground 
          weatherCode={weatherData.weather.current.weather_code} 
          isDay={weatherData.weather.current.is_day} 
        />
      )}
      
      <div className="relative z-10 w-full">
        <Navigation 
          onSelectLocation={handleSelectLocation} 
          theme={theme} 
          toggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} 
        />

        {loading ? (
          <div className="flex items-center justify-center h-96 w-full text-slate-500 dark:text-slate-400 font-medium">
            Synchronizing live atmospheric data matrix...
          </div>
        ) : (
          weatherData && (
            <>
              <CurrentHero weather={weatherData.weather} locationName={location.name} />
              <MetricGrid weather={weatherData.weather} />
              <AQICard aqiData={weatherData.aqi} />
              <WeatherCharts hourlyData={weatherData.weather.hourly} />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-7xl mx-auto">
                <ForecastTabs daily={weatherData.weather.daily} />
                <WeatherMap lat={location.lat} lon={location.lon} />
              </div>
            </>
          )
        )}
      </div>
    </div>
  );
}
