
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { FileText } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function NotesModule() {
  const [notes] = useState([
    { id: 1, title: "Meeting Notes", content: "Discussed Q2 goals and roadmap...", service: "Local" },
    { id: 2, title: "Shopping List", content: "Milk, Eggs, Bread...", service: "Google Keep" },
    { id: 3, title: "Project Ideas", content: "1. Smart home dashboard\n2. AI-powered note taking...", service: "Notion" },
  ]);
  
  const [selectedNoteId, setSelectedNoteId] = useState(1);
  const [noteContent, setNoteContent] = useState(notes[0].content);
  
  const selectedNote = notes.find(note => note.id === selectedNoteId);

  const handleNoteChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNoteContent(event.target.value);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <Select 
          value={selectedNoteId.toString()} 
          onValueChange={value => setSelectedNoteId(parseInt(value))}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select note" />
          </SelectTrigger>
          <SelectContent>
            {notes.map(note => (
              <SelectItem key={note.id} value={note.id.toString()}>
                {note.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        <div className="flex items-center text-xs text-muted-foreground">
          <FileText className="h-3 w-3 mr-1" />
          {selectedNote?.service}
        </div>
      </div>
      
      <Textarea
        value={noteContent}
        onChange={handleNoteChange}
        className="min-h-[150px] text-sm"
        placeholder="Write your note here..."
      />
      
      <div className="flex justify-end mt-3">
        <Button variant="outline" size="sm">
          Sync Notes
        </Button>
      </div>
    </div>
  );
}
