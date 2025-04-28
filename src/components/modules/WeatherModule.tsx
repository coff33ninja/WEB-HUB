import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { CloudSun, Thermometer } from 'lucide-react';
import { useWeather } from '@/hooks/useWeather';

export function WeatherModule() {
  const { data: weatherData, isLoading, error } = useWeather();
  const [unit, setUnit] = useState<'F' | 'C'>('F');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-4 text-destructive">
        <p>Could not load weather data</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{weatherData?.location}</h3>
          <div className="text-sm text-muted-foreground">{weatherData?.condition}</div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setUnit(unit === 'F' ? 'C' : 'F')}
        >
          <Thermometer className="h-4 w-4 mr-1" /> °{unit}
        </Button>
      </div>

      <div className="flex items-center mb-6">
        <CloudSun className="h-16 w-16 text-primary mr-4" />
        <div>
          <div className="text-4xl font-bold">
            {unit === 'F'
              ? weatherData?.temperature
              : ((weatherData?.temperature - 32) * 5 / 9).toFixed(1)}°
          </div>
          <div className="text-sm text-muted-foreground">
            H: {unit === 'F'
              ? weatherData?.high
              : ((weatherData?.high - 32) * 5 / 9).toFixed(1)}° 
            L: {unit === 'F'
              ? weatherData?.low
              : ((weatherData?.low - 32) * 5 / 9).toFixed(1)}°
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 text-center">
        {weatherData?.forecast.map((day, index) => (
          <div key={index} className="p-2 rounded-md bg-muted/30">
            <div className="text-sm font-medium">{day.day}</div>
            <CloudSun className="h-6 w-6 mx-auto my-1 text-primary" />
            <div className="text-xs">
              {unit === 'F'
                ? `${day.high}° / ${day.low}°`
                : `${((day.high - 32) * 5 / 9).toFixed(1)}° / ${((day.low - 32) * 5 / 9).toFixed(1)}°`}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
