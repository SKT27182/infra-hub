import type { ReactNode } from 'react'
import { useState, useEffect } from 'react'
import { Menu } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Sidebar } from './Sidebar'
import { Button } from '@/components/ui/button'

const SIDEBAR_COLLAPSED_KEY = 'infra-hub-sidebar-collapsed'

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === 'true'
    } catch {
      return false
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(sidebarCollapsed))
    } catch {
      /* ignore */
    }
  }, [sidebarCollapsed])

  const toggleCollapse = () => setSidebarCollapsed((c) => !c)

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Mobile header */}
      <header className="fixed top-0 left-0 right-0 z-50 flex h-14 items-center border-b bg-card px-4 md:hidden">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsSidebarOpen(true)}
          className="mr-2"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <div className="font-semibold">Infra Hub</div>
      </header>

      {/* Mobile overlay */}
      <div
        className={cn(
          'fixed inset-0 z-50 bg-background/80 backdrop-blur-sm transition-opacity md:hidden',
          isSidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        )}
        onClick={() => setIsSidebarOpen(false)}
        aria-hidden={!isSidebarOpen}
      />

      {/* Mobile sidebar — full width drawer */}
      <Sidebar
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out md:hidden',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        collapsed={false}
        onNavigate={() => setIsSidebarOpen(false)}
      />

      {/* Desktop: flex sidebar + main (no resizable panel collapse trap) */}
      <aside
        className={cn(
          'hidden md:flex shrink-0 h-full transition-[width] duration-300 ease-in-out overflow-hidden',
          sidebarCollapsed ? 'w-[4.5rem]' : 'w-64'
        )}
      >
        <Sidebar
          className="w-full"
          collapsed={sidebarCollapsed}
          onToggleCollapse={toggleCollapse}
          showCollapseToggle
        />
      </aside>

      <main className="flex-1 min-w-0 overflow-auto pt-14 md:pt-0">
        <div className="container mx-auto p-4 md:p-6">{children}</div>
      </main>
    </div>
  )
}
