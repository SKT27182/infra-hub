import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  Container,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ThemeToggle } from './ThemeToggle'

interface NavItem {
  title: string
  href: string
  icon: ReactNode
}

const mainNav: NavItem[] = [
  { title: 'Dashboard', href: '/', icon: <LayoutDashboard className="h-4 w-4" /> },
  { title: 'Containers', href: '/containers', icon: <Container className="h-4 w-4" /> },
]

function NavLink({ item }: { item: NavItem }) {
  const location = useLocation()
  const isActive = location.pathname === item.href

  return (
    <Link
      to={item.href}
      className={cn(
        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
        isActive
          ? 'bg-primary/10 text-primary'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      )}
    >
      {item.icon}
      {item.title}
    </Link>
  )
}

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  return (
    <div className={cn('flex h-full flex-col border-r bg-card', className)}>
      <div className="flex h-14 items-center border-b px-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <Server className="h-5 w-5 text-primary" />
          <span>Infra Hub</span>
        </Link>
      </div>

      <ScrollArea className="flex-1 px-3 py-4">
        <div className="space-y-1">
          {mainNav.map((item) => (
            <NavLink key={item.href} item={item} />
          ))}
        </div>
      </ScrollArea>

      <div className="border-t p-4 flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          Infra Hub v0.1.0
        </div>
        <ThemeToggle />
      </div>
    </div>
  )
}
