
import React from 'react';
import { CrawlForm } from '@/components/CrawlForm';
import { Globe } from 'lucide-react';

export function WebScraperModule() {
  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <Globe className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold">Website Scraper</h3>
      </div>
      <CrawlForm />
    </div>
  );
}
