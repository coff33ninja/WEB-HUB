import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';

interface WeatherData {
  location: string;
  temperature: number;
  condition: string;
  high: number;
  low: number;
  precipitation: string;
  humidity: string;
  wind: string;
  forecast: Array<{
    day: string;
    high: number;
    low: number;
    icon: string;
  }>;
}

async function fetchWeather(apiKey: string): Promise<WeatherData> {
  if (!apiKey) {
    throw new Error("API key is required");
  }
  // Example using OpenWeatherMap API (replace with actual API if different)
  const url = `https://api.openweathermap.org/data/2.5/weather?q=San Francisco&units=imperial&appid=${apiKey}`;
  const forecastUrl = `https://api.openweathermap.org/data/2.5/forecast?q=San Francisco&units=imperial&appid=${apiKey}`;

  const weatherResponse = await fetch(url);
  if (!weatherResponse.ok) {
    throw new Error("Failed to fetch weather data");
  }
  const weatherJson = await weatherResponse.json();

  const forecastResponse = await fetch(forecastUrl);
  if (!forecastResponse.ok) {
    throw new Error("Failed to fetch weather forecast");
  }
  const forecastJson = await forecastResponse.json();

  // Map API response to WeatherData interface
  const forecastData = forecastJson.list
    .filter((item: any, index: number) => index % 8 === 0) // roughly daily
    .slice(0, 4)
    .map((item: any) => ({
      day: new Date(item.dt * 1000).toLocaleDateString('en-US', { weekday: 'short' }),
      high: Math.round(item.main.temp_max),
      low: Math.round(item.main.temp_min),
      icon: item.weather[0].icon,
    }));

  return {
    location: `${weatherJson.name}, ${weatherJson.sys.country}`,
    temperature: Math.round(weatherJson.main.temp),
    condition: weatherJson.weather[0].description,
    high: Math.round(weatherJson.main.temp_max),
    low: Math.round(weatherJson.main.temp_min),
    precipitation: `${weatherJson.rain ? weatherJson.rain['1h'] || 0 : 0} mm`,
    humidity: `${weatherJson.main.humidity}%`,
    wind: `${Math.round(weatherJson.wind.speed)} mph`,
    forecast: forecastData,
  };
}

export function useWeather() {
  const [apiKey, setApiKey] = useState<string>('');
  const [apiKeyLoaded, setApiKeyLoaded] = useState(false);

  useEffect(() => {
    fetch('/api/weather/api-key')
      .then(res => res.json())
      .then(data => {
        setApiKey(data.apiKey || '');
        setApiKeyLoaded(true);
      })
      .catch(() => setApiKeyLoaded(true));
  }, []);

  return useQuery({
    queryKey: ['weather', apiKey],
    queryFn: () => fetchWeather(apiKey),
    enabled: apiKeyLoaded && !!apiKey,
    refetchInterval: 300000, // Refetch every 5 minutes
  });
}
