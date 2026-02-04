import { useParams } from 'react-router-dom'
import { ExternalLink, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useService, useServiceInfo, useServiceLogs, useServiceActions } from '@/hooks'
import { cn } from '@/lib/utils'

export function ServiceDetailPage() {
  const { name } = useParams<{ name: string }>()
  const { data: service, isLoading } = useService(name || '')
  const { data: info } = useServiceInfo(name || '')
  const { data: logs, refetch: refetchLogs } = useServiceLogs(name || '', 50)
  const { start, stop, restart } = useServiceActions(name || '')

  if (isLoading || !service) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-muted-foreground">Loading service...</div>
      </div>
    )
  }

  const isActing = start.isPending || stop.isPending || restart.isPending

  return (
    <div className="space-y-6">
      {/* Header */}
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

      {/* Actions */}
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

      {/* Info */}
      {info && (
        <Card>
          <CardHeader>
            <CardTitle>Service Information</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-lg bg-muted p-4 text-sm">
              {JSON.stringify(info.info, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Logs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Logs</CardTitle>
          <Button variant="ghost" size="sm" onClick={() => refetchLogs()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64 rounded-lg bg-muted">
            <pre className="p-4 font-mono text-xs">
              {logs?.logs || 'No logs available'}
            </pre>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
