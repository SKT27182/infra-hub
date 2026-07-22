import { ExternalLink, Loader2, Play, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useAdminActions } from '@/hooks'
import type { ServiceStatus } from '@/lib/api'

export interface AdminAccess {
  url: string
  instructions: string[]
  api_key_required?: boolean
  login?: Record<string, string>
}

interface AdminAccessCardProps {
  adminUrl?: string | null
  adminAccess?: AdminAccess | null
  service?: ServiceStatus
}

export function AdminAccessCard({ adminUrl, adminAccess, service }: AdminAccessCardProps) {
  const url = adminAccess?.url || adminUrl
  const { start, stop } = useAdminActions(service?.name || '')
  const admin = service?.admin
  const isPending = start.isPending || stop.isPending
  const actionError = start.error || stop.error
  if (!url && !adminAccess?.instructions?.length) {
    return null
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base">Admin access</CardTitle>
        <div className="flex items-center gap-2">
          {admin && (
            <Badge variant={admin.running ? 'default' : 'secondary'}>
              {admin.running ? 'Running' : 'Stopped'}
            </Badge>
          )}
          {admin && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={isPending || (!admin.running && !service?.running)}
                      onClick={() => admin.running ? stop.mutate() : start.mutate()}
                    >
                      {isPending ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : admin.running ? (
                        <Square className="mr-2 h-4 w-4" />
                      ) : (
                        <Play className="mr-2 h-4 w-4" />
                      )}
                      {admin.running ? 'Stop admin UI' : 'Start admin UI'}
                    </Button>
                  </span>
                </TooltipTrigger>
                {!admin.running && !service?.running && (
                  <TooltipContent>Start the primary service first</TooltipContent>
                )}
              </Tooltip>
            </TooltipProvider>
          )}
          {url && (!admin || admin.running) && (
            <Button variant="outline" size="sm" onClick={() => window.open(url, '_blank')}>
              <ExternalLink className="mr-2 h-4 w-4" />
              Open admin UI
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-2 text-sm text-muted-foreground">
        {url && (
          <p>
            URL:{' '}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs text-foreground">{url}</code>
          </p>
        )}
        {adminAccess?.api_key_required && (
          <p className="text-foreground">
            API key required — use <code className="rounded bg-muted px-1">QDRANT_API_KEY</code> from{' '}
            <code className="rounded bg-muted px-1">backend/.env</code>.
          </p>
        )}
        {adminAccess?.login && (
          <ul className="list-disc space-y-1 pl-5">
            {Object.entries(adminAccess.login).map(([key, value]) => (
              <li key={key}>
                <span className="font-medium text-foreground">{value}</span>
                <span className="text-muted-foreground"> ({key.replace(/_/g, ' ')})</span>
              </li>
            ))}
          </ul>
        )}
        {adminAccess?.instructions?.map((line) => (
          <p key={line}>{line}</p>
        ))}
        {admin && !service?.running && !admin.running && (
          <p>Start {service?.display_name || 'the primary service'} before starting its admin UI.</p>
        )}
        {actionError && (
          <p className="text-destructive" role="alert">
            {actionError instanceof Error ? actionError.message : 'Admin UI action failed'}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
