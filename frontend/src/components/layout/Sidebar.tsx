import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  Container,
  Database,
  HardDrive,
  Layers,
  FileBox,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

interface NavItem {
  title: string
  href: string
  icon: ReactNode
}

const mainNav: NavItem[] = [
  { title: 'Dashboard', href: '/', icon: <LayoutDashboard className="h-4 w-4" /> },
  { title: 'Services', href: '/services', icon: <Server className="h-4 w-4" /> },
  { title: 'Containers', href: '/containers', icon: <Container className="h-4 w-4" /> },
]

const serviceNav: NavItem[] = [
  { title: 'PostgreSQL', href: '/services/postgres', icon: <Database className="h-4 w-4" /> },
  { title: 'Redis', href: '/services/redis', icon: <HardDrive className="h-4 w-4" /> },
  { title: 'MongoDB', href: '/services/mongodb', icon: <Database className="h-4 w-4" /> },
  { title: 'Qdrant', href: '/services/qdrant', icon: <Layers className="h-4 w-4" /> },
  { title: 'MinIO', href: '/services/minio', icon: <FileBox className="h-4 w-4" /> },
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

        <Separator className="my-4" />

        <div className="mb-2 px-3 text-xs font-medium text-muted-foreground">
          Services
        </div>
        <div className="space-y-1">
          {serviceNav.map((item) => (
            <NavLink key={item.href} item={item} />
          ))}
        </div>
      </ScrollArea>

      <div className="border-t p-4">
        <div className="text-xs text-muted-foreground">
          Infra Hub v0.1.0
        </div>
      </div>
    </div>
  )
}
