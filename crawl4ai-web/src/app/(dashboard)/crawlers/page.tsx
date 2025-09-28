import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Plus, Search, Filter, MoreHorizontal } from "lucide-react"
import { Input } from "@/components/ui/input"

export default function CrawlersPage() {
  // Mock data - will be replaced with real data from API
  const crawlers = [
    {
      id: 1,
      name: 'E-commerce Sites',
      status: 'running',
      urls: ['example.com', 'test.com'],
      lastRun: '2 minutes ago',
      pagesCrawled: 456,
      schedule: 'Daily'
    },
    {
      id: 2,
      name: 'News Aggregator',
      status: 'completed',
      urls: ['news.example.com'],
      lastRun: '1 hour ago',
      pagesCrawled: 321,
      schedule: 'Every 6 hours'
    },
    {
      id: 3,
      name: 'Documentation Scraper',
      status: 'error',
      urls: ['docs.example.com'],
      lastRun: '3 hours ago',
      pagesCrawled: 12,
      schedule: 'Weekly'
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Crawlers</h2>
          <p className="text-muted-foreground">
            Manage your web crawlers and their configurations
          </p>
        </div>
        <Button asChild>
          <a href="/crawlers/new">
            <Plus className="mr-2 h-4 w-4" /> New Crawler
          </a>
        </Button>
      </div>

      <Card>
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search crawlers..."
                className="w-[300px] pl-8"
              />
            </div>
            <Button variant="outline" size="sm" className="h-9">
              <Filter className="mr-2 h-4 w-4" />
              Filter
            </Button>
          </div>
        </div>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>URLs</TableHead>
                <TableHead>Last Run</TableHead>
                <TableHead>Pages</TableHead>
                <TableHead>Schedule</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {crawlers.map((crawler) => (
                <TableRow key={crawler.id}>
                  <TableCell className="font-medium">{crawler.name}</TableCell>
                  <TableCell>
                    <Badge 
                      variant={
                        crawler.status === 'running' 
                          ? 'default' 
                          : crawler.status === 'completed' 
                            ? 'secondary' 
                            : 'destructive'
                      }
                    >
                      {crawler.status.charAt(0).toUpperCase() + crawler.status.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {crawler.urls.join(', ')}
                  </TableCell>
                  <TableCell>{crawler.lastRun}</TableCell>
                  <TableCell>{crawler.pagesCrawled.toLocaleString()}</TableCell>
                  <TableCell>{crawler.schedule}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon">
                      <MoreHorizontal className="h-4 w-4" />
                      <span className="sr-only">More</span>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
