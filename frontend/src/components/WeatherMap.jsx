import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function WeatherMap({ lat, lon }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapContainerRef.current, {
        center: [lat, lon],
        zoom: 10,
        zoomControl: false
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(mapInstanceRef.current);

      markerRef.current = L.marker([lat, lon]).addTo(mapInstanceRef.current);
    } else {
      mapInstanceRef.current.setView([lat, lon], 10);
      if (markerRef.current) {
        markerRef.current.setLatLng([lat, lon]);
      }
    }
  }, [lat, lon]);

  return (
    <div className="glass-panel p-4 w-full max-w-7xl mx-auto mb-6">
      <h3 className="text-md font-semibold text-slate-700 dark:text-slate-300 mb-3">Interactive Weather Map Core</h3>
      <div ref={mapContainerRef} className="h-80 w-full rounded-2xl overflow-hidden z-10" />
    </div>
  );
}
