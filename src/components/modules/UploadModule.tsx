
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Upload, FileUp } from "lucide-react";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";

export function UploadModule() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedModules, setUploadedModules] = useState([
    { name: "currency_converter.py", type: "python", status: "active" },
    { name: "stock_tracker.json", type: "json", status: "inactive" },
  ]);
  const { toast } = useToast();
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = () => {
    setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    // Handle file upload logic
    const files = Array.from(e.dataTransfer.files);
    if (files.length) {
      // In a real app, we'd process the files here
      toast({
        title: "Module uploaded",
        description: `${files[0].name} has been added to your modules.`,
      });
      
      // Simulate adding a new module
      setUploadedModules([
        ...uploadedModules,
        { 
          name: files[0].name, 
          type: files[0].name.endsWith('.py') ? 'python' : 'json',
          status: 'pending'
        }
      ]);
    }
  };
  
  return (
    <Tabs defaultValue="upload">
      <TabsList className="grid grid-cols-2 mb-4">
        <TabsTrigger value="upload">Upload</TabsTrigger>
        <TabsTrigger value="installed">Installed</TabsTrigger>
      </TabsList>
      
      <TabsContent value="upload">
        <div
          className={`dropzone h-[150px] ${isDragging ? 'active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <Upload className="h-10 w-10 text-muted-foreground mb-2" />
          <p className="text-sm text-center text-muted-foreground">
            Drag and drop Python or JSON modules here
          </p>
          <Button variant="outline" size="sm" className="mt-4">
            <FileUp className="h-4 w-4 mr-2" /> Browse Files
          </Button>
        </div>
      </TabsContent>
      
      <TabsContent value="installed">
        <div className="space-y-2">
          {uploadedModules.map((module, index) => (
            <div key={index} className="flex items-center justify-between p-2 rounded-md bg-muted/30">
              <div>
                <div className="text-sm font-medium">{module.name}</div>
                <div className="text-xs text-muted-foreground capitalize">{module.type}</div>
              </div>
              <div>
                <Button variant="ghost" size="sm">
                  {module.status === "active" ? "Disable" : "Enable"}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </TabsContent>
    </Tabs>
  );
}
