import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Database, Trash2, Copy, Check, Layers, Server } from 'lucide-react'
import { useState } from 'react'
import { useService, useMongoDBDatabases, useMongoDBActions, useServiceInfo } from '@/hooks'
import { mongodbQuery, type ServiceQueryResponse } from '@/lib/api'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function MongoDBPage() {
  const { data: service } = useService('mongodb')
  const { data: databases, isLoading, error } = useMongoDBDatabases()
  const { data: infoData } = useServiceInfo('mongodb')
  const { dropDB } = useMongoDBActions()
  const [copied, setCopied] = useState(false)
  const [queryText, setQueryText] = useState('{\n  "action": "list_databases",\n  "params": {}\n}')
  const [queryRunning, setQueryRunning] = useState(false)
  const [queryResult, setQueryResult] = useState<ServiceQueryResponse | null>(null)

  const info = infoData?.info || {}

  const copyEndpoint = () => {
    const url = (info.connection as any)?.url || `mongodb://127.0.0.1:${service?.ports[0]?.split(':')[0] || '27017'}`
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
      const result = await mongodbQuery(parsed.action, parsed.params || {})
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
            <span>🍃</span> MongoDB
          </h1>
          <p className="text-muted-foreground">Document database</p>
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
            onClick={() => window.open('http://localhost:8081', '_blank')}
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            Mongo Express
          </Button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Databases</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{databases?.length ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Collections</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{String(info.total_collections ?? 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Version</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">v{String(info.version ?? '?')}</div>
          </CardContent>
        </Card>
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
            <div className="text-destructive">Failed to load databases. Is MongoDB running?</div>
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
                      Size: {formatBytes(Number(db.size) || 0)} | Collections: {String(db.collections || 0)}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:bg-destructive/10"
                    onClick={() => {
                      if (confirm(`Are you sure you want to delete database "${db.name}"?`)) {
                        dropDB.mutate(String(db.name))
                      }
                    }}
                    disabled={dropDB.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              {(!databases || databases.length === 0) && (
                <div className="text-muted-foreground">No databases found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Query */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Query
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            className="min-h-32 w-full rounded-md border bg-background p-3 font-mono text-sm"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder='{"action":"list_databases","params":{}}'
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
