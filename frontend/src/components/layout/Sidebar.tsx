import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  Container,
  LogOut,
  Settings,
  PanelLeftClose,
  PanelLeft,
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

function getMainNav(): NavItem[] {
  return [
    { title: 'Dashboard', href: '/', icon: <LayoutDashboard className="h-4 w-4 shrink-0" /> },
    { title: 'Containers', href: '/containers', icon: <Container className="h-4 w-4 shrink-0" /> },
  ]
}

function NavLink({
  item,
  collapsed,
  onNavigate,
}: {
  item: NavItem
  collapsed: boolean
  onNavigate?: () => void
}) {
  const location = useLocation()
  const isActive = location.pathname === item.href

  return (
    <Link
      to={item.href}
      onClick={onNavigate}
      title={collapsed ? item.title : undefined}
      className={cn(
        'flex items-center rounded-lg text-sm transition-colors',
        collapsed ? 'justify-center p-2.5' : 'gap-3 px-3 py-2',
        isActive
          ? 'bg-primary/10 text-primary'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      )}
    >
      {item.icon}
      {!collapsed && <span className="truncate">{item.title}</span>}
    </Link>
  )
}

interface SidebarProps {
  className?: string
  collapsed?: boolean
  onToggleCollapse?: () => void
  showCollapseToggle?: boolean
  onNavigate?: () => void
}

export function Sidebar({
  className,
  collapsed = false,
  onToggleCollapse,
  showCollapseToggle = false,
  onNavigate,
}: SidebarProps) {
  const { logout, user } = useAuth()

  return (
    <div className={cn('flex h-full flex-col border-r bg-card', className)}>
      <div
        className={cn(
          'flex h-14 items-center border-b shrink-0',
          collapsed ? 'justify-center px-2' : 'justify-between px-4'
        )}
      >
        <Link
          to="/"
          className={cn(
            'flex items-center font-semibold min-w-0',
            collapsed ? 'p-1' : 'gap-2'
          )}
          title={collapsed ? 'Infra Hub' : undefined}
        >
          <Server className="h-5 w-5 text-primary shrink-0" />
          {!collapsed && <span className="truncate">Infra Hub</span>}
        </Link>
        {showCollapseToggle && onToggleCollapse && !collapsed && (
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0"
            onClick={onToggleCollapse}
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="h-4 w-4" />
          </Button>
        )}
      </div>

      {showCollapseToggle && onToggleCollapse && collapsed && (
        <div className="flex justify-center py-2 border-b">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapse}
            aria-label="Expand sidebar"
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
        </div>
      )}

      <ScrollArea className="flex-1 px-2 py-4">
        <div className="space-y-1">
          {getMainNav().map((item) => (
            <NavLink
              key={item.href}
              item={item}
              collapsed={collapsed}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      </ScrollArea>

      <div className="mt-auto border-t p-2 space-y-2">
        {user && !collapsed && (
          <div className="flex items-center gap-2 px-2 py-1">
            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium text-primary shrink-0">
              {(user.name?.[0] || user.email[0]).toUpperCase()}
            </div>
            <div className="flex flex-col overflow-hidden min-w-0">
              <span className="text-sm font-medium truncate">
                {user.name?.trim() || user.email.split('@')[0] || 'User'}
              </span>
            </div>
          </div>
        )}

        <div
          className={cn(
            'flex gap-1',
            collapsed ? 'flex-col items-center' : 'items-center px-1'
          )}
        >
          <Link
            to="/settings"
            onClick={onNavigate}
            title={collapsed ? 'Settings' : undefined}
            className={cn(
              'inline-flex items-center justify-center rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors',
              collapsed ? 'h-9 w-9' : 'flex-1 gap-2 px-3 py-2'
            )}
          >
            <Settings className="h-4 w-4 shrink-0" />
            {!collapsed && 'Settings'}
          </Link>
          <Button
            variant="ghost"
            size={collapsed ? 'icon' : 'sm'}
            className={cn(
              'text-muted-foreground hover:text-foreground',
              !collapsed && 'flex-1 justify-center gap-2'
            )}
            onClick={() => void logout()}
            title={collapsed ? 'Logout' : undefined}
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {!collapsed && 'Logout'}
          </Button>
          <ThemeToggle />
        </div>

        {!collapsed && (
          <div className="text-[10px] text-center text-muted-foreground/50 pb-1">
            Infra Hub v2
          </div>
        )}
      </div>
    </div>
  )
}
