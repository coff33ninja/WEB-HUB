
import React, { useState } from 'react';
import { GripVertical, Move } from 'lucide-react';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';

interface LayoutEditorProps {
  children: React.ReactNode;
  editMode: boolean;
}

export function LayoutEditor({ children, editMode }: LayoutEditorProps) {
  const [orderedModules, setOrderedModules] = useState<React.ReactNode[]>(
    React.Children.toArray(children)
  );
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  
  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };
  
  const handleDragEnd = () => {
    setDraggedIndex(null);
  };
  
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };
  
  const handleDrop = (dropIndex: number) => {
    if (draggedIndex !== null && draggedIndex !== dropIndex) {
      const newModules = [...orderedModules];
      const [draggedItem] = newModules.splice(draggedIndex, 1);
      newModules.splice(dropIndex, 0, draggedItem);
      setOrderedModules(newModules);
    }
    setDraggedIndex(null);
  };

  if (!editMode) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {orderedModules}
      </div>
    );
  }

  return (
    <ResizablePanelGroup direction="horizontal" className="min-h-[500px] w-full rounded-lg border">
      <ResizablePanel defaultSize={75}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
          {orderedModules.map((child, index) => (
            <div
              key={index}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragEnd={handleDragEnd}
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(index)}
              className={`relative ${draggedIndex === index ? 'opacity-50' : ''}`}
            >
              <div className="absolute top-0 left-0 right-0 bg-background h-8 z-10 flex items-center justify-between px-2 cursor-move border-b rounded-t-lg">
                <div className="flex items-center gap-1">
                  <GripVertical className="h-4 w-4" />
                  <span className="text-xs font-medium">Module {index + 1}</span>
                </div>
                <Move className="h-4 w-4" />
              </div>
              <div className="pt-8">
                {child}
              </div>
            </div>
          ))}
        </div>
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize={25}>
        <div className="p-4 space-y-4">
          <h3 className="text-base font-medium">Layout Properties</h3>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium block mb-2">Grid Columns</label>
              <div className="flex gap-2">
                <button className="px-3 py-1 border rounded text-xs">1</button>
                <button className="px-3 py-1 border rounded text-xs bg-primary text-primary-foreground">2</button>
                <button className="px-3 py-1 border rounded text-xs">3</button>
                <button className="px-3 py-1 border rounded text-xs">4</button>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">Gap Size</label>
              <div className="flex gap-2">
                <button className="px-3 py-1 border rounded text-xs">S</button>
                <button className="px-3 py-1 border rounded text-xs bg-primary text-primary-foreground">M</button>
                <button className="px-3 py-1 border rounded text-xs">L</button>
              </div>
            </div>
          </div>
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
