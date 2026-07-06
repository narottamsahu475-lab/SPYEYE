  const fetchWeather = async (lat, lon) => {
    setLoading(true);
    try {
      // Direct Live Backend URL bina kisi .env variable ke jhanjhat ke
      const res = await fetch(`https://weather-backend-amit.onrender.com/api/weather?lat=${lat}&lon=${lon}`);
      const data = await res.json();
      setWeatherData(data);
    } catch (e) {
      console.error("Error fetching weather updates.", e);
    } finally {
      setLoading(false);
    }
  };
