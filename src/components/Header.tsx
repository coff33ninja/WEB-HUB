
import React from 'react';
import { ModeToggle } from './ModeToggle';
import { SettingsButton } from './SettingsButton';

export function Header() {
  return (
    <header className="sticky top-0 z-10 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-bold text-primary text-lg">ModularHub</span>
        </div>
        <div className="flex items-center gap-2">
          <SettingsButton />
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}
