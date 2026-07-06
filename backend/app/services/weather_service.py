import httpx
from app.config import settings
from app.utils.cache import cache_store

class WeatherService:
    @staticmethod
    async def search_locations(name: str):
        cache_key = f"search:{name.lower()}"
        cached = cache_store.get(cache_key)
        if cached:
            return cached

        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.GEOCODING_API_URL,
                params={"name": name, "count": 10, "language": "en", "format": "json"}
            )
            data = response.json().get("results", [])
            cache_store.set(cache_key, data, ttl=3600)
            return data

    @staticmethod
    async def get_weather_data(lat: float, lon: float):
        cache_key = f"weather:{lat}:{lon}"
        cached = cache_store.get(cache_key)
        if cached:
            return cached

        async with httpx.AsyncClient() as client:
            # Fetch Forecast and Historical data details matching requirements
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day", "precipitation", "rain", "showers", "snowfall", "weather_code", "cloud_cover", "pressure_msl", "surface_pressure", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
                "hourly": ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature", "precipitation_probability", "precipitation", "weather_code", "pressure_msl", "wind_speed_10m", "uv_index", "visibility"],
                "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset", "uv_index_max", "precipitation_sum", "precipitation_probability_max"],
                "timezone": "auto"
            }
            
            aqi_params = {
                "latitude": lat,
                "longitude": lon,
                "current": ["european_aqi", "us_aqi", "pm2_5", "pm10", "nitrogen_dioxide", "sulphur_dioxide", "ozone"],
                "timezone": "auto"
            }

            weather_res = await client.get(settings.WEATHER_API_URL, params=weather_params)
            aqi_res = await client.get(settings.AIR_QUALITY_API_URL, params=aqi_params)
            
            combined_data = {
                "weather": weather_res.json(),
                "aqi": aqi_res.json()
            }
            cache_store.set(cache_key, combined_data, ttl=settings.CACHE_EXPIRATION_SECONDS)
            return combined_data
