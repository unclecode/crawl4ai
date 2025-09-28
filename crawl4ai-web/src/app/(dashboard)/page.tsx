import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import Link from "next/link"

export default function DashboardPage() {
  // Mock data - will be replaced with real data from API
  const stats = [
    { name: 'Active Crawlers', value: '3', change: '+2', changeType: 'positive' },
    { name: 'Pages Crawled', value: '1,234', change: '+12%', changeType: 'positive' },
    { name: 'Errors', value: '5', change: '-3', changeType: 'negative' },
    { name: 'Storage Used', value: '2.5 GB', change: '+0.5 GB', changeType: 'neutral' },
  ]

  const recentCrawlers = [
    { id: 1, name: 'E-commerce Sites', status: 'running', pagesCrawled: 456, lastRun: '2 minutes ago' },
    { id: 2, name: 'News Aggregator', status: 'completed', pagesCrawled: 321, lastRun: '1 hour ago' },
    { id: 3, name: 'Documentation Scraper', status: 'error', pagesCrawled: 12, lastRun: '3 hours ago' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Overview of your crawlers and their status
          </p>
        </div>
        <Button asChild>
          <Link href="/crawlers/new">
            <Plus className="mr-2 h-4 w-4" /> New Crawler
          </Link>
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.name}
              </CardTitle>
              <div className={`text-xs px-2 py-1 rounded-full ${
                stat.changeType === 'positive' 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-400' 
                  : stat.changeType === 'negative' 
                    ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-400'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
              }`}>
                {stat.change}
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Crawlers */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Crawlers</CardTitle>
          <CardDescription>
            Your most recently modified crawlers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentCrawlers.map((crawler) => (
              <div key={crawler.id} className="flex items-center p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="font-medium">{crawler.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {crawler.pagesCrawled} pages • Last run {crawler.lastRun}
                  </div>
                </div>
                <div className="flex items-center">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    crawler.status === 'running' 
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300'
                      : crawler.status === 'completed'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
                  }`}>
                    {crawler.status.charAt(0).toUpperCase() + crawler.status.slice(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
