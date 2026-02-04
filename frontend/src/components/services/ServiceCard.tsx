import {
  Play,
  Square,
  RotateCcw,
  ExternalLink,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useServiceActions } from '@/hooks'
import type { ServiceStatus } from '@/lib/api'
import { cn } from '@/lib/utils'

const serviceIcons: Record<string, string> = {
  postgres: '🐘',
  redis: '🔴',
  mongodb: '🍃',
  qdrant: '🔷',
  minio: '📦',
}

interface ServiceCardProps {
  service: ServiceStatus
  showActions?: boolean
}

export function ServiceCard({ service, showActions = true }: ServiceCardProps) {
  const { start, stop, restart } = useServiceActions(service.name)
  const isLoading = start.isPending || stop.isPending || restart.isPending

  return (
    <Card className={cn(
      'transition-all duration-200 hover:shadow-lg',
      service.healthy ? 'border-success/30' : service.running ? 'border-warning/30' : 'border-destructive/30'
    )}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-medium">
          <span className="text-xl">{serviceIcons[service.name] || '🔧'}</span>
          {service.display_name}
        </CardTitle>
        <Badge
          variant={service.healthy ? 'default' : service.running ? 'secondary' : 'destructive'}
          className={cn(
            service.healthy && 'bg-success text-success-foreground',
            service.running && !service.healthy && 'bg-warning text-warning-foreground'
          )}
        >
          {service.healthy ? 'Healthy' : service.running ? 'Running' : 'Stopped'}
        </Badge>
      </CardHeader>

      <CardContent>
        <div className="space-y-3">
          {/* Status info */}
          <div className="text-sm text-muted-foreground">
            <div className="flex justify-between">
              <span>Container:</span>
              <span className="font-mono text-xs">{service.container_name || 'N/A'}</span>
            </div>
            {service.ports.length > 0 && (
              <div className="flex justify-between">
                <span>Ports:</span>
                <span className="font-mono text-xs">{service.ports.join(', ')}</span>
              </div>
            )}
          </div>

          {/* Actions */}
          {showActions && (
            <TooltipProvider>
              <div className="flex items-center gap-2 pt-2">
                {!service.running ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => start.mutate()}
                        disabled={isLoading}
                        className="flex-1"
                      >
                        {start.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                        <span className="ml-1">Start</span>
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Start service</TooltipContent>
                  </Tooltip>
                ) : (
                  <>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => stop.mutate()}
                          disabled={isLoading}
                        >
                          {stop.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Square className="h-4 w-4" />
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Stop service</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => restart.mutate()}
                          disabled={isLoading}
                        >
                          {restart.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RotateCcw className="h-4 w-4" />
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Restart service</TooltipContent>
                    </Tooltip>
                  </>
                )}

                {service.admin_url && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="sm"
                        variant="secondary"
                        className="ml-auto"
                        onClick={() => window.open(service.admin_url!, '_blank')}
                      >
                        <ExternalLink className="h-4 w-4" />
                        <span className="ml-1">Admin</span>
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Open admin UI</TooltipContent>
                  </Tooltip>
                )}
              </div>
            </TooltipProvider>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
