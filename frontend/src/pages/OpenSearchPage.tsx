import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Layers, Trash2, Copy, Check, Activity } from 'lucide-react'
import { useState } from 'react'
import { AdminAccessCard, type AdminAccess } from '@/components/services/AdminAccessCard'
import { useService, useOpenSearchIndices, useOpenSearchActions, useServiceInfo } from '@/hooks'
import { opensearchQuery, type ServiceQueryResponse } from '@/lib/api'
import { confirmResourceDeletion } from '@/lib/confirm-resource'
import {
  DEFAULT_OPENSEARCH_QUERY,
  OPENSEARCH_QUERY_HINT,
} from '@/lib/service-default-queries'

export function OpenSearchPage() {
  const { data: service } = useService('opensearch')
  const { data: indices, isLoading, error } = useOpenSearchIndices()
  const { data: infoData } = useServiceInfo('opensearch')
  const { dropIndex } = useOpenSearchActions()
  const [copied, setCopied] = useState(false)
  const [queryText, setQueryText] = useState(DEFAULT_OPENSEARCH_QUERY)
  const [queryRunning, setQueryRunning] = useState(false)
  const [queryResult, setQueryResult] = useState<ServiceQueryResponse | null>(null)

  const info = infoData?.info || {}
  const adminAccess = info.admin_access as AdminAccess | undefined
  const adminUrl = service?.admin_url || adminAccess?.url
  const connection = (info.connection || {}) as Record<string, string>
  const endpoint = connection.url || `http://127.0.0.1:9200`
  const cluster = (info.cluster || {}) as Record<string, unknown>

  const copyEndpoint = () => {
    navigator.clipboard.writeText(endpoint)
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
      const result = await opensearchQuery(parsed.action, parsed.params || {})
      setQueryResult(result)
    } catch (err) {
      setQueryResult({
        success: false,
        error: err instanceof Error ? err.message : 'Invalid query',
      })
    } finally {
      setQueryRunning(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <span>🔎</span> OpenSearch
          </h1>
          <p className="text-muted-foreground">
            Full-text search, autocomplete, aggregations, and k-NN vectors
          </p>
          <div className="mt-2 flex items-center gap-2">
            <code className="rounded bg-muted px-2 py-1 text-xs">{endpoint}</code>
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={copyEndpoint}>
              {copied ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {service && (
            <Badge variant={service.healthy ? 'default' : 'destructive'}>
              {service.healthy ? 'Healthy' : 'Unhealthy'}
            </Badge>
          )}
          {service && adminUrl && (!service.admin || service.admin.running) && (
            <Button variant="outline" onClick={() => window.open(adminUrl, '_blank')}>
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Dashboards
            </Button>
          )}
        </div>
      </div>

      <AdminAccessCard adminUrl={adminUrl} adminAccess={adminAccess} service={service} />
      {dropIndex.error && <p className="text-sm text-destructive" role="alert">{dropIndex.error.message}</p>}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Activity className="h-4 w-4" />
              Cluster
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {String(cluster.status || 'unknown')}
            </div>
            <p className="text-xs text-muted-foreground">{String(cluster.name || '')}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Layers className="h-4 w-4" />
              Indices
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '…' : (info.total_indices as number | undefined) ?? indices?.length ?? 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              Nodes / shards
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {String(cluster.number_of_nodes ?? '—')} / {String(cluster.active_shards ?? '—')}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Indices
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-muted-foreground">Loading indices...</div>
          ) : error ? (
            <div className="text-destructive">Failed to load indices. Is OpenSearch running?</div>
          ) : (
            <div className="space-y-2">
              {indices?.map((idx: Record<string, unknown>, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <div className="font-medium">{String(idx.name)}</div>
                    <div className="text-sm text-muted-foreground">
                      Docs: {String(idx.docs_count ?? 0)} | Size: {String(idx.store_size || '—')}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{String(idx.health || idx.status || 'unknown')}</Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:bg-destructive/10"
                      onClick={() => {
                        if (confirmResourceDeletion('index', String(idx.name))) {
                          dropIndex.mutate(String(idx.name))
                        }
                      }}
                      disabled={dropIndex.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              {(!indices || indices.length === 0) && (
                <div className="text-muted-foreground">No indices found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Query</CardTitle>
          <p className="text-sm text-muted-foreground">{OPENSEARCH_QUERY_HINT}</p>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            className="min-h-32 w-full rounded-md border bg-background p-3 font-mono text-sm"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder='{"action":"list_indices","params":{}}'
            spellCheck={false}
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
