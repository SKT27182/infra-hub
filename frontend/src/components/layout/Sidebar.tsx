import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  Container,
  LogOut,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ThemeToggle } from './ThemeToggle'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'

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
  const { logout, user } = useAuth()

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

      <div className="mt-auto border-t p-4 space-y-4">
        {user && (
          <div className="flex items-center gap-2 px-2">
            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium text-primary">
              {user.full_name?.[0] || user.email[0].toUpperCase()}
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="text-sm font-medium truncate">
                {user.full_name || 'User'}
              </span>
              <span className="text-xs text-muted-foreground truncate">
                {user.email}
              </span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 justify-start gap-2 text-muted-foreground hover:text-foreground"
            onClick={logout}
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
          <ThemeToggle />
        </div>

        <div className="text-[10px] text-center text-muted-foreground/50">
          Infra Hub v0.1.0
        </div>
      </div>
    </div>
  )
}
