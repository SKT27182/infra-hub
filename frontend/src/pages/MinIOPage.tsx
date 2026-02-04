import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, FolderOpen } from 'lucide-react'
import { useService, useMinioBuckets } from '@/hooks'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function MinIOPage() {
  const { data: service } = useService('minio')
  const { data: buckets, isLoading, error } = useMinioBuckets()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <span>📦</span> MinIO
          </h1>
          <p className="text-muted-foreground">Object storage</p>
        </div>
        <div className="flex items-center gap-2">
          {service && (
            <Badge variant={service.healthy ? 'default' : 'destructive'}>
              {service.healthy ? 'Healthy' : 'Unhealthy'}
            </Badge>
          )}
          <Button
            variant="outline"
            onClick={() => window.open('http://localhost:9001', '_blank')}
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            Console
          </Button>
        </div>
      </div>

      {/* Buckets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5" />
            Buckets
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-muted-foreground">Loading buckets...</div>
          ) : error ? (
            <div className="text-destructive">Failed to load buckets. Is MinIO running?</div>
          ) : (
            <div className="space-y-2">
              {buckets?.map((bucket: Record<string, unknown>, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <div className="font-medium">{String(bucket.name)}</div>
                    <div className="text-sm text-muted-foreground">
                      Objects: {String(bucket.objects || 0)} | Size: {formatBytes(Number(bucket.size) || 0)}
                    </div>
                  </div>
                </div>
              ))}
              {(!buckets || buckets.length === 0) && (
                <div className="text-muted-foreground">No buckets found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
