import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, FolderOpen, Trash2, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { useService, useMinioBuckets, useMinioActions, useServiceInfo } from '@/hooks'
import { minioQuery, type ServiceQueryResponse } from '@/lib/api'

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
  const { data: infoData } = useServiceInfo('minio')
  const { dropBucket } = useMinioActions()
  const [copied, setCopied] = useState(false)
  const [queryText, setQueryText] = useState('{\n  "action": "list_buckets",\n  "params": {}\n}')
  const [queryRunning, setQueryRunning] = useState(false)
  const [queryResult, setQueryResult] = useState<ServiceQueryResponse | null>(null)

  const info = infoData?.info || {}

  const copyEndpoint = () => {
    const url = (info.connection as any)?.url || `http://127.0.0.1:${service?.ports[0]?.split(':')[0] || '9000'}`
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const runQuery = async () => {
    setQueryRunning(true)
    try {
      const parsed = JSON.parse(queryText) as {
        action?: string
        params?: Record<string, unknown>
      }
      if (!parsed.action) {
        setQueryResult({ success: false, error: 'Query JSON must include "action"' })
        return
      }
      const result = await minioQuery(parsed.action, parsed.params || {})
      setQueryResult(result)
    } catch (error) {
      setQueryResult({
        success: false,
        error: error instanceof Error ? error.message : 'Invalid query',
      })
    } finally {
      setQueryRunning(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <span>📦</span> MinIO
          </h1>
          <p className="text-muted-foreground">Object storage</p>
          {(info.connection || (service && service.ports.length > 0)) && (
            <div className="mt-2 flex items-center gap-2">
              <code className="rounded bg-muted px-2 py-1 text-xs">
                {(info.connection as any)?.url || `127.0.0.1:${service?.ports[0].split(':')[0]}`}
              </code>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={copyEndpoint}
              >
                {copied ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
              </Button>
            </div>
          )}
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

      {/* Stats Summary */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Buckets</CardTitle>
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{buckets?.length ?? 0}</div>
          </CardContent>
        </Card>
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
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:bg-destructive/10"
                    onClick={() => {
                      if (confirm(`Are you sure you want to delete bucket "${bucket.name}"?`)) {
                        dropBucket.mutate(String(bucket.name))
                      }
                    }}
                    disabled={dropBucket.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              {(!buckets || buckets.length === 0) && (
                <div className="text-muted-foreground">No buckets found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Query */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5" />
            Query
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            className="min-h-32 w-full rounded-md border bg-background p-3 font-mono text-sm"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder='{"action":"list_buckets","params":{}}'
          />
          <Button onClick={runQuery} disabled={queryRunning}>
            {queryRunning ? 'Running...' : 'Run Query'}
          </Button>
          {queryResult && (
            <pre className="overflow-x-auto rounded-md border bg-muted/30 p-3 text-xs">
              {JSON.stringify(queryResult, null, 2)}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
