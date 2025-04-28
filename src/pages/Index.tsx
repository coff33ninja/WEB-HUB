
import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { ModuleGrid } from '@/components/ModuleGrid';
import { BookmarksSidebar } from '@/components/BookmarksSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';

const Index = () => {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen">
        <BookmarksSidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 container py-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold">ModularHub Dashboard</h1>
                <p className="text-muted-foreground">
                  Your customizable modular workspace
                </p>
              </div>
            </div>
            
            <ModuleGrid />
          </main>
          <footer className="border-t py-4">
            <div className="container flex items-center justify-between text-sm text-muted-foreground">
              <div>© 2025 ModularHub</div>
              <div>
                <span className="inline-flex items-center bg-primary/10 text-primary px-2 py-1 rounded text-xs">
                  <span className="h-2 w-2 rounded-full bg-primary mr-1.5"></span>
                  Connected to Ollama
                </span>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Index;
