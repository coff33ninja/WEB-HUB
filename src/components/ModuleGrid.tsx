
import React, { useState } from 'react';
import { CalendarModule } from './modules/CalendarModule';
import { WeatherModule } from './modules/WeatherModule';
import { NotesModule } from './modules/NotesModule';
import { UploadModule } from './modules/UploadModule';
import { AIAssistantModule } from './modules/AIAssistantModule';
import { WebScraperModule } from './modules/WebScraperModule';
import { ModuleWrapper } from './ModuleWrapper';
import { LayoutEditor } from './LayoutEditor';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';

export function ModuleGrid() {
  const [editMode, setEditMode] = useState(false);
  const { toast } = useToast();
  
  const toggleEditMode = () => {
    setEditMode(!editMode);
    toast({
      title: editMode ? "Layout saved" : "Edit mode activated",
      description: editMode 
        ? "Your custom dashboard layout has been saved."
        : "You can now drag modules to reposition them or resize using the handles.",
    });
  };

  const modules = [
    {
      title: "Calendar",
      description: "Sync with your online calendars",
      component: <CalendarModule />
    },
    {
      title: "Weather",
      description: "Current conditions and forecast",
      component: <WeatherModule />
    },
    {
      title: "Notes",
      description: "Sync with online note services",
      component: <NotesModule />
    },
    {
      title: "Upload Module",
      description: "Drop Python or JSON modules",
      component: <UploadModule />
    },
    {
      title: "AI Assistant",
      description: "Powered by local Ollama models",
      component: <AIAssistantModule />
    },
    {
      title: "Web Scraper",
      description: "Import content from your favorite websites",
      component: <WebScraperModule />
    }
  ];

  return (
    <>
      <div className="flex justify-between mb-4">
        <h2 className="text-lg font-semibold">Dashboard Modules</h2>
        <Button 
          variant={editMode ? "default" : "outline"} 
          size="sm"
          onClick={toggleEditMode}
        >
          {editMode ? "Save Layout" : "Customize Layout"}
        </Button>
      </div>
      
      <LayoutEditor editMode={editMode}>
        {modules.map((module, index) => (
          <ModuleWrapper 
            key={index}
            title={module.title} 
            description={module.description}
          >
            {module.component}
          </ModuleWrapper>
        ))}
      </LayoutEditor>
    </>
  );
}
