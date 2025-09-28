import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Plus, X, ChevronLeft } from "lucide-react"
import Link from "next/link"

export default function NewCrawlerPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="outline" size="icon" asChild>
          <Link href="/crawlers">
            <ChevronLeft className="h-4 w-4" />
            <span className="sr-only">Back</span>
          </Link>
        </Button>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">New Crawler</h2>
          <p className="text-muted-foreground">
            Configure a new web crawler with the options below
          </p>
        </div>
      </div>

      <Tabs defaultValue="basic" className="space-y-4">
        <TabsList>
          <TabsTrigger value="basic">Basic</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
          <TabsTrigger value="scheduling">Scheduling</TabsTrigger>
          <TabsTrigger value="processing">Processing</TabsTrigger>
          <TabsTrigger value="storage">Storage</TabsTrigger>
        </TabsList>

        <form className="space-y-6">
          <TabsContent value="basic" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
                <CardDescription>
                  Configure the basic settings for your crawler
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Crawler Name</Label>
                  <Input id="name" placeholder="My Awesome Crawler" />
                </div>
                <div className="space-y-2">
                  <Label>Target URLs</Label>
                  <div className="space-y-2">
                    <div className="flex space-x-2">
                      <Input placeholder="https://example.com" />
                      <Button type="button" variant="outline" size="icon">
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="flex items-center gap-1">
                        example.com
                        <button className="rounded-full hover:bg-muted p-0.5">
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Textarea id="description" placeholder="What does this crawler do?" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Advanced Settings</CardTitle>
                <CardDescription>
                  Configure advanced crawling options
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="max-depth">Max Depth</Label>
                    <Input id="max-depth" type="number" min="1" defaultValue="3" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max-pages">Max Pages</Label>
                    <Input id="max-pages" type="number" min="1" defaultValue="1000" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="crawl-speed">Crawl Speed</Label>
                    <Select defaultValue="normal">
                      <SelectTrigger>
                        <SelectValue placeholder="Select speed" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="slow">Slow (be nice to servers)</SelectItem>
                        <SelectItem value="normal">Normal</SelectItem>
                        <SelectItem value="fast">Fast (use with caution)</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="parallel-requests">Parallel Requests</Label>
                    <Input id="parallel-requests" type="number" min="1" max="50" defaultValue="5" />
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <input type="checkbox" id="respect-robots" className="rounded border-gray-300" defaultChecked />
                    <Label htmlFor="respect-robots" className="!m-0">Respect robots.txt</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input type="checkbox" id="follow-sitemap" className="rounded border-gray-300" defaultChecked />
                    <Label htmlFor="follow-sitemap" className="!m-0">Follow sitemap.xml if available</Label>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="scheduling" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Scheduling</CardTitle>
                <CardDescription>
                  Configure when and how often the crawler should run
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Schedule Type</Label>
                  <Select defaultValue="manual">
                    <SelectTrigger>
                      <SelectValue placeholder="Select schedule" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="manual">Manual (run on demand)</SelectItem>
                      <SelectItem value="once">Run once at specific time</SelectItem>
                      <SelectItem value="recurring">Recurring schedule</SelectItem>
                      <SelectItem value="cron">Custom cron expression</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Start Date</Label>
                    <Input type="datetime-local" />
                  </div>
                  <div className="space-y-2">
                    <Label>Time Zone</Label>
                    <Select defaultValue="utc">
                      <SelectTrigger>
                        <SelectValue placeholder="Select timezone" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="utc">UTC</SelectItem>
                        <SelectItem value="local">Local Time</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="processing" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Content Processing</CardTitle>
                <CardDescription>
                  Configure how the crawler should process content
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Content Types to Extract</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="extract-text" className="rounded border-gray-300" defaultChecked />
                      <Label htmlFor="extract-text" className="!m-0">Text content</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="extract-images" className="rounded border-gray-300" defaultChecked />
                      <Label htmlFor="extract-images" className="!m-0">Images</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="extract-pdfs" className="rounded border-gray-300" defaultChecked />
                      <Label htmlFor="extract-pdfs" className="!m-0">PDFs</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="extract-media" className="rounded border-gray-300" />
                      <Label htmlFor="extract-media" className="!m-0">Audio/Video</Label>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="content-selectors">Content Selectors (CSS)</Label>
                  <Textarea 
                    id="content-selectors" 
                    placeholder="main, article, .content"
                    className="font-mono text-sm"
                  />
                  <p className="text-sm text-muted-foreground">
                    CSS selectors to extract content (one per line)
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="storage" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Storage & Output</CardTitle>
                <CardDescription>
                  Configure where and how to store the crawled data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Output Format</Label>
                  <Select defaultValue="json">
                    <SelectTrigger>
                      <SelectValue placeholder="Select format" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="markdown">Markdown</SelectItem>
                      <SelectItem value="sqlite">SQLite</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Storage Location</Label>
                  <Select defaultValue="local">
                    <SelectTrigger>
                      <SelectValue placeholder="Select storage" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="local">Local File System</SelectItem>
                      <SelectItem value="s3">AWS S3</SelectItem>
                      <SelectItem value="gcs">Google Cloud Storage</SelectItem>
                      <SelectItem value="azure">Azure Blob Storage</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="output-path">Output Path</Label>
                  <Input id="output-path" placeholder="/data/crawls/{name}_{timestamp}" />
                  <p className="text-sm text-muted-foreground">
                    Available variables: {'{name}, {timestamp}, {date}, {id}'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <div className="flex justify-end space-x-4">
            <Button type="button" variant="outline">
              Cancel
            </Button>
            <Button type="submit">
              Save & Start Crawler
            </Button>
          </div>
        </form>
      </Tabs>
    </div>
  )
}
