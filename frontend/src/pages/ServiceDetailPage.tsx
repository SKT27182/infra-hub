import { useParams } from 'react-router-dom'
import { ExternalLink, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { AdminAccessCard, type AdminAccess } from '@/components/services/AdminAccessCard'
import { useService, useServiceInfo, useServiceLogs, useServiceActions } from '@/hooks'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { ResizableShell } from '@/components/layout/ResizableShell'
import { cn } from '@/lib/utils'

export function ServiceDetailPage() {
  const { name } = useParams<{ name: string }>()
  const { data: service, isLoading } = useService(name || '')
  const { data: info } = useServiceInfo(name || '')
  const { data: logs, refetch: refetchLogs } = useServiceLogs(name || '', 50)
  const { start, stop, restart } = useServiceActions(name || '')

  useDocumentTitle(
    service ? `${service.display_name} — Infra Hub` : 'Service — Infra Hub'
  )

  if (isLoading || !service) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-muted-foreground">Loading service...</div>
      </div>
    )
  }

  const isActing = start.isPending || stop.isPending || restart.isPending
  const adminAccess = info?.info?.admin_access as AdminAccess | undefined
  const adminUrl = service.admin_url || adminAccess?.url

  const mainColumn = (
    <div className="space-y-6 h-full overflow-auto pr-2">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{service.display_name}</h1>
          <p className="text-muted-foreground">
            Container: {service.container_name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={service.healthy ? 'default' : 'destructive'}
            className={cn(service.healthy && 'bg-success')}
          >
            {service.healthy ? 'Healthy' : service.running ? 'Running' : 'Stopped'}
          </Badge>
          {service.admin_url && (
            <Button
              variant="outline"
              onClick={() => window.open(service.admin_url!, '_blank')}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Admin
            </Button>
          )}
        </div>
      </div>

      <AdminAccessCard adminUrl={adminUrl} adminAccess={adminAccess} service={service} />

      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          {!service.running ? (
            <Button onClick={() => start.mutate()} disabled={isActing}>
              Start Service
            </Button>
          ) : (
            <>
              <Button variant="outline" onClick={() => stop.mutate()} disabled={isActing}>
                Stop
              </Button>
              <Button variant="outline" onClick={() => restart.mutate()} disabled={isActing}>
                Restart
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {info && (
        <Card>
          <CardHeader>
            <CardTitle>Service Information</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-lg bg-muted p-4 text-sm max-h-[50vh]">
              {JSON.stringify(info.info, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )

  const logsColumn = (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between shrink-0">
        <CardTitle>Logs</CardTitle>
        <Button variant="ghost" size="sm" onClick={() => refetchLogs()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex-1 min-h-0">
        <ScrollArea className="h-[calc(100vh-12rem)] rounded-lg bg-muted">
          <pre className="p-4 font-mono text-xs">
            {logs?.logs || 'No logs available'}
          </pre>
        </ScrollArea>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] min-h-[480px]">
      <div className="hidden lg:block h-full">
        <ResizableShell main={mainColumn} right={logsColumn} storageKey="infra-service-detail" />
      </div>
      <div className="lg:hidden space-y-6">
        {mainColumn}
        {logsColumn}
      </div>
    </div>
  )
}
