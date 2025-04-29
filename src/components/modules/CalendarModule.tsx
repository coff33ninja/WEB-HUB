import React, { useState, useEffect } from 'react';
import { Calendar } from "@/components/ui/calendar";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar as CalendarIcon } from "lucide-react";

export function CalendarModule() {
  const [date, setDate] = useState<Date | undefined>(new Date());
  const [events, setEvents] = useState(() => {
    const stored = localStorage.getItem('calendarEvents');
    if (stored) {
      // Parse and convert date strings back to Date objects
      return JSON.parse(stored).map((e: any) => ({ ...e, date: new Date(e.date) }));
    }
    return [
      { date: new Date(2025, 3, 30), title: "Team Meeting" },
      { date: new Date(2025, 4, 1), title: "Project Deadline" },
      { date: new Date(2025, 4, 3), title: "Doctor Appointment" },
    ];
  });
  const [newEventTitle, setNewEventTitle] = useState('');

  useEffect(() => {
    // Save events to localStorage whenever they change
    localStorage.setItem('calendarEvents', JSON.stringify(events));
  }, [events]);

  // Filter events for the selected day
  const todayEvents = events.filter(
    (event) => date && event.date.toDateString() === date.toDateString()
  );

  const handleAddEvent = () => {
    if (!date || !newEventTitle.trim()) return;
    setEvents(prev => [
      ...prev,
      { date: new Date(date), title: newEventTitle.trim() }
    ]);
    setNewEventTitle('');
  };

  const handleSync = () => {
    localStorage.setItem('calendarEvents', JSON.stringify(events));
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-medium">
          {date ? date.toLocaleString('default', { month: 'long', year: 'numeric' }) : 'Calendar'}
        </h3>
        <Button variant="outline" size="sm" className="h-7 gap-1" onClick={handleSync}>
          <CalendarIcon className="h-3.5 w-3.5" />
          <span className="text-xs">Sync</span>
        </Button>
      </div>
      <Calendar
        mode="single"
        selected={date}
        onSelect={setDate}
        className="rounded-md border"
        modifiers={{
          event: events.map(event => event.date),
        }}
        modifiersStyles={{
          event: {
            fontWeight: 'bold',
            backgroundColor: 'hsl(var(--accent))',
            color: 'white',
            borderRadius: '50%'
          }
        }}
      />
      <div className="mt-4 flex gap-2">
        <input
          type="text"
          className="border rounded px-2 py-1 text-sm flex-1"
          placeholder="Add event for selected day"
          value={newEventTitle}
          onChange={e => setNewEventTitle(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleAddEvent(); }}
        />
        <Button size="sm" onClick={handleAddEvent} disabled={!date || !newEventTitle.trim()}>
          Add
        </Button>
      </div>
      {todayEvents.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium mb-2">Events</h4>
          {todayEvents.map((event, index) => (
            <Card key={index} className="mb-2 bg-muted/40">
              <CardContent className="p-2 flex justify-between items-center">
                <span className="text-sm">{event.title}</span>
                <Badge variant="outline" className="text-xs">
                  {event.date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
