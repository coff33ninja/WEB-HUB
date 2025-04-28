
import React from 'react';
import { BookmarkPlus, Bookmark as BookmarkIcon } from 'lucide-react';
import { Bookmark } from '@/types/bookmark';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';

export function BookmarksSidebar() {
  const [bookmarks, setBookmarks] = React.useState<Bookmark[]>([]);
  const [showAddForm, setShowAddForm] = React.useState(false);
  const { toast } = useToast();

  React.useEffect(() => {
    // Load bookmarks from localStorage on mount
    const savedBookmarks = localStorage.getItem('bookmarks');
    if (savedBookmarks) {
      setBookmarks(JSON.parse(savedBookmarks));
    }
  }, []);

  const handleAddBookmark = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const title = formData.get('title') as string;
    const url = formData.get('url') as string;

    if (!title || !url) return;

    const newBookmark = {
      id: Date.now().toString(),
      title,
      url: url.startsWith('http') ? url : `https://${url}`,
    };

    const updatedBookmarks = [...bookmarks, newBookmark];
    setBookmarks(updatedBookmarks);
    localStorage.setItem('bookmarks', JSON.stringify(updatedBookmarks));
    setShowAddForm(false);
    toast({
      title: "Bookmark added",
      description: `${title} has been added to your bookmarks.`,
    });
  };

  return (
    <Sidebar className="border-r">
      <SidebarHeader className="p-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Bookmarks</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            <BookmarkPlus className="h-5 w-5" />
          </Button>
        </div>
        {showAddForm && (
          <form onSubmit={handleAddBookmark} className="mt-2 space-y-2">
            <Input
              name="title"
              placeholder="Title"
              className="h-8"
            />
            <Input
              name="url"
              placeholder="URL"
              className="h-8"
            />
            <Button type="submit" className="w-full h-8">
              Add Bookmark
            </Button>
          </form>
        )}
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Quick Access</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {bookmarks.map((bookmark) => (
                <SidebarMenuItem key={bookmark.id}>
                  <SidebarMenuButton
                    asChild
                    tooltip={bookmark.url}
                  >
                    <a
                      href={bookmark.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2"
                    >
                      <BookmarkIcon className="h-4 w-4" />
                      <span>{bookmark.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
