import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Database } from 'lucide-react'
import { useService, usePostgresDatabases } from '@/hooks'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function PostgresPage() {
  const { data: service } = useService('postgres')
  const { data: databases, isLoading, error } = usePostgresDatabases()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <span>🐘</span> PostgreSQL
          </h1>
          <p className="text-muted-foreground">Database management</p>
        </div>
        <div className="flex items-center gap-2">
          {service && (
            <Badge variant={service.healthy ? 'default' : 'destructive'}>
              {service.healthy ? 'Healthy' : 'Unhealthy'}
            </Badge>
          )}
          <Button
            variant="outline"
            onClick={() => window.open('http://localhost:5050', '_blank')}
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            pgAdmin
          </Button>
        </div>
      </div>

      {/* Databases */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Databases
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-muted-foreground">Loading databases...</div>
          ) : error ? (
            <div className="text-destructive">Failed to load databases. Is PostgreSQL running?</div>
          ) : (
            <div className="space-y-2">
              {databases?.map((db: Record<string, unknown>, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <div className="font-medium">{String(db.name)}</div>
                    <div className="text-sm text-muted-foreground">
                      Size: {formatBytes(Number(db.size) || 0)}
                    </div>
                  </div>
                </div>
              ))}
              {(!databases || databases.length === 0) && (
                <div className="text-muted-foreground">No databases found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
