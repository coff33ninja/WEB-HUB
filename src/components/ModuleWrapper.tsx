
import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Blocks, Move, GripVertical } from "lucide-react";

interface ModuleWrapperProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

export function ModuleWrapper({ title, description, children }: ModuleWrapperProps) {
  return (
    <Card className="module-card overflow-hidden">
      <CardHeader className="p-4 flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-base">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Blocks className="h-4 w-4" />
              <span className="sr-only">Module options</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Configure</DropdownMenuItem>
            <DropdownMenuItem>Resize</DropdownMenuItem>
            <DropdownMenuItem>Refresh</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive">Remove</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent className="p-4 pt-0">
        {children}
      </CardContent>
    </Card>
  );
}
