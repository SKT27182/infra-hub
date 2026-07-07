import { ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export interface AdminAccess {
  url: string
  instructions: string[]
  api_key_required?: boolean
  login?: Record<string, string>
}

interface AdminAccessCardProps {
  adminUrl?: string | null
  adminAccess?: AdminAccess | null
}

export function AdminAccessCard({ adminUrl, adminAccess }: AdminAccessCardProps) {
  const url = adminAccess?.url || adminUrl
  if (!url && !adminAccess?.instructions?.length) {
    return null
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base">Admin access</CardTitle>
        {url && (
          <Button variant="outline" size="sm" onClick={() => window.open(url, '_blank')}>
            <ExternalLink className="mr-2 h-4 w-4" />
            Open admin UI
          </Button>
        )}
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
      </CardContent>
    </Card>
  )
}
