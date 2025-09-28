import { SidebarNav } from "@/components/layout/sidebar-nav"
import { DashboardHeader } from "@/components/layout/header"
import { ThemeToggle } from "@/components/theme-toggle"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r">
        <div className="flex flex-col flex-1 min-h-0 bg-background">
          <div className="flex items-center h-16 flex-shrink-0 px-4 border-b">
            <h1 className="text-xl font-bold">Crawl4AI</h1>
            <div className="ml-auto">
              <ThemeToggle />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <SidebarNav />
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64 flex flex-col flex-1">
        <DashboardHeader />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
