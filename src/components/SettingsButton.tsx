
import React, { useState } from 'react';
import { Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SettingsDialog } from '@/components/ui/settings-dialog';
import { useToast } from '@/hooks/use-toast';

export function SettingsButton() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { toast } = useToast();
  
  return (
    <>
      <Button 
        variant="outline" 
        size="icon"
        onClick={() => setSettingsOpen(true)}
        className="h-8 w-8"
      >
        <Settings className="h-4 w-4" />
        <span className="sr-only">Settings</span>
      </Button>
      <SettingsDialog 
        open={settingsOpen} 
        onOpenChange={setSettingsOpen}
      />
    </>
  );
}
