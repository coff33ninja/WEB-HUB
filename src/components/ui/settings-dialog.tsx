import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const [weatherApiKey, setWeatherApiKey] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      // Fetch the stored API key from backend
      setLoading(true);
      fetch('/api/weather/api-key')
        .then(res => res.json())
        .then(data => {
          setWeatherApiKey(data.apiKey || '');
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [open]);

  const saveApiKey = () => {
    setLoading(true);
    fetch('/api/weather/api-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ apiKey: weatherApiKey }),
    })
      .then(res => res.json())
      .then(() => {
        setLoading(false);
        onOpenChange(false);
      })
      .catch(() => setLoading(false));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Dashboard Settings</DialogTitle>
          <DialogDescription>
            Customize your ModularHub dashboard appearance, layout, and API keys.
          </DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="layout" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="layout">Layout</TabsTrigger>
            <TabsTrigger value="appearance">Appearance</TabsTrigger>
            <TabsTrigger value="modules">Modules</TabsTrigger>
            <TabsTrigger value="api">API Keys</TabsTrigger>
          </TabsList>
          <TabsContent value="layout" className="space-y-4 py-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Layout Mode</h3>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="outline" className="justify-start h-20 p-4">
                  <div className="flex flex-col items-center">
                    <div className="grid grid-cols-2 gap-1 mb-2">
                      <div className="bg-primary/20 h-2 w-6 rounded"></div>
                      <div className="bg-primary/20 h-2 w-6 rounded"></div>
                      <div className="bg-primary/20 h-2 w-6 rounded"></div>
                      <div className="bg-primary/20 h-2 w-6 rounded"></div>
                    </div>
                    <span className="text-xs">Grid</span>
                  </div>
                </Button>
                <Button variant="outline" className="justify-start h-20 p-4">
                  <div className="flex flex-col items-center">
                    <div className="flex flex-col gap-1 mb-2">
                      <div className="bg-primary/20 h-2 w-12 rounded"></div>
                      <div className="bg-primary/20 h-2 w-12 rounded"></div>
                      <div className="bg-primary/20 h-2 w-12 rounded"></div>
                    </div>
                    <span className="text-xs">List</span>
                  </div>
                </Button>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium mb-2">Sidebar Position</h3>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="outline" className="justify-start h-16">
                  <div className="flex items-center gap-2">
                    <div className="bg-primary/20 h-8 w-2 rounded"></div>
                    <div className="bg-primary/20 h-8 w-8 rounded"></div>
                    <span className="text-xs">Left</span>
                  </div>
                </Button>
                <Button variant="outline" className="justify-start h-16">
                  <div className="flex items-center gap-2">
                    <div className="bg-primary/20 h-8 w-8 rounded"></div>
                    <div className="bg-primary/20 h-8 w-2 rounded"></div>
                    <span className="text-xs">Right</span>
                  </div>
                </Button>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="appearance" className="space-y-4 py-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Color Theme</h3>
              <div className="grid grid-cols-3 gap-2">
                <Button variant="outline" className="h-20 p-2">
                  <div className="flex flex-col items-center gap-2">
                    <div className="bg-primary h-8 w-8 rounded-full"></div>
                    <span className="text-xs">Primary</span>
                  </div>
                </Button>
                <Button variant="outline" className="h-20 p-2">
                  <div className="flex flex-col items-center gap-2">
                    <div className="bg-accent h-8 w-8 rounded-full"></div>
                    <span className="text-xs">Accent</span>
                  </div>
                </Button>
                <Button variant="outline" className="h-20 p-2">
                  <div className="flex flex-col items-center gap-2">
                    <div className="bg-muted-foreground h-8 w-8 rounded-full"></div>
                    <span className="text-xs">Neutral</span>
                  </div>
                </Button>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="modules" className="space-y-4 py-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Active Modules</h3>
              <div className="space-y-2 border rounded-md p-4 max-h-[200px] overflow-y-auto">
                <div className="flex items-center justify-between p-2 bg-background rounded-md border cursor-move hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary"></div>
                    <span>Calendar</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">⋮</Button>
                </div>
                <div className="flex items-center justify-between p-2 bg-background rounded-md border cursor-move hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary"></div>
                    <span>Weather</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">⋮</Button>
                </div>
                <div className="flex items-center justify-between p-2 bg-background rounded-md border cursor-move hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary"></div>
                    <span>Notes</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">⋮</Button>
                </div>
                <div className="flex items-center justify-between p-2 bg-background rounded-md border cursor-move hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary"></div>
                    <span>Upload Module</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">⋮</Button>
                </div>
                <div className="flex items-center justify-between p-2 bg-background rounded-md border cursor-move hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary"></div>
                    <span>AI Assistant</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">⋮</Button>
                </div>
                <div className="flex items-center justify-between p-2 bg-background rounded-md border cursor-move hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary"></div>
                    <span>Web Scraper</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">⋮</Button>
                </div>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="api" className="space-y-4 py-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Weather API Key</h3>
              <input
                type="text"
                className="w-full rounded border border-gray-300 p-2"
                placeholder="Enter your weather API key"
                value={weatherApiKey}
                onChange={(e) => setWeatherApiKey(e.target.value)}
                disabled={loading}
                aria-label="Weather API Key"
              />
            </div>
          </TabsContent>
        </Tabs>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={saveApiKey} disabled={loading || !weatherApiKey.trim()}>
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}