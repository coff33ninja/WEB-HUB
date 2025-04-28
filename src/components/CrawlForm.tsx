
import { useState } from 'react';
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";
import { Globe } from "lucide-react";

export function CrawlForm() {
  const { toast } = useToast();
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [crawlResult, setCrawlResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setProgress(0);
    setCrawlResult(null);
    
    try {
      // Simulate API call for now
      await new Promise(resolve => setTimeout(resolve, 2000));
      setProgress(100);
      
      toast({
        title: "Success",
        description: "Website content fetched successfully",
      });
      
      setCrawlResult({
        title: "Example Website",
        content: "Sample scraped content would appear here...",
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch website content",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
          />
        </div>
        {isLoading && (
          <Progress value={progress} className="w-full" />
        )}
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full"
        >
          <Globe className="h-4 w-4 mr-2" />
          {isLoading ? "Fetching..." : "Fetch Content"}
        </Button>
      </form>

      {crawlResult && (
        <Card className="p-4">
          <h4 className="font-medium mb-2">{crawlResult.title}</h4>
          <p className="text-sm text-muted-foreground">{crawlResult.content}</p>
          <p className="text-xs text-muted-foreground mt-2">
            Fetched at: {new Date(crawlResult.timestamp).toLocaleString()}
          </p>
        </Card>
      )}
    </div>
  );
}
