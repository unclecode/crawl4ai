import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  LayoutDashboard,
  Bot,
  Settings,
  FileText,
  Clock,
  Database,
  LogOut,
} from "lucide-react"

const items = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Crawlers",
    href: "/crawlers",
    icon: Bot,
  },
  {
    title: "Logs",
    href: "/logs",
    icon: FileText,
  },
  {
    title: "History",
    href: "/history",
    icon: Clock,
  },
  {
    title: "Data",
    href: "/data",
    icon: Database,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
]

export function SidebarNav() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 space-y-2">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center px-4 py-3 rounded-lg transition-colors",
              pathname.startsWith(item.href)
                ? "bg-accent text-accent-foreground"
                : "hover:bg-accent/50"
            )}
          >
            <item.icon className="w-5 h-5 mr-3" />
            <span>{item.title}</span>
          </Link>
        ))}
      </div>
      <div className="mt-auto pt-4 border-t">
        <Button variant="ghost" className="w-full justify-start">
          <LogOut className="w-5 h-5 mr-3" />
          Sign Out
        </Button>
      </div>
    </div>
  )
}
