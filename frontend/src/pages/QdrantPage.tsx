import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Layers, Trash2, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { useService, useQdrantCollections, useQdrantActions, useServiceInfo } from '@/hooks'
import { qdrantQuery, type ServiceQueryResponse } from '@/lib/api'

export function QdrantPage() {
  const { data: service } = useService('qdrant')
  const { data: collections, isLoading, error } = useQdrantCollections()
  const { data: infoData } = useServiceInfo('qdrant')
  const { dropCollection } = useQdrantActions()
  const [copied, setCopied] = useState(false)
  const [queryText, setQueryText] = useState('{\n  "action": "list_collections",\n  "params": {}\n}')
  const [queryRunning, setQueryRunning] = useState(false)
  const [queryResult, setQueryResult] = useState<ServiceQueryResponse | null>(null)

  const info = infoData?.info || {}

  const copyEndpoint = () => {
    const url = (info.connection as any)?.url || `http://127.0.0.1:${service?.ports[0]?.split(':')[0] || '6333'}`
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
      const result = await qdrantQuery(parsed.action, parsed.params || {})
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
            <span>🔷</span> Qdrant
          </h1>
          <p className="text-muted-foreground">Vector database</p>
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
            onClick={() => window.open('http://localhost:6333/dashboard', '_blank')}
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            Dashboard
          </Button>
        </div>
      </div>

      {/* Collections */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Collections
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-muted-foreground">Loading collections...</div>
          ) : error ? (
            <div className="text-destructive">Failed to load collections. Is Qdrant running?</div>
          ) : (
            <div className="space-y-2">
              {collections?.map((coll: Record<string, unknown>, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <div className="font-medium">{String(coll.name)}</div>
                    <div className="text-sm text-muted-foreground">
                      Vectors: {String(coll.vectors_count || 0)} | Points: {String(coll.points_count || 0)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{String(coll.status || 'unknown')}</Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:bg-destructive/10"
                      onClick={() => {
                        if (confirm(`Are you sure you want to delete collection "${coll.name}"?`)) {
                          dropCollection.mutate(String(coll.name))
                        }
                      }}
                      disabled={dropCollection.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              {(!collections || collections.length === 0) && (
                <div className="text-muted-foreground">No collections found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Query */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Query
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            className="min-h-32 w-full rounded-md border bg-background p-3 font-mono text-sm"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder='{"action":"list_collections","params":{}}'
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
