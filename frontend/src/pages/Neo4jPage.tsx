import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Copy, Check, Network, GitBranch, Database } from 'lucide-react'
import { useState } from 'react'
import { AdminAccessCard, type AdminAccess } from '@/components/services/AdminAccessCard'
import { useService, useServiceInfo, useNeo4jGraphStats } from '@/hooks'
import { neo4jQuery, type ServiceQueryResponse } from '@/lib/api'
import {
  DEFAULT_NEO4J_CYPHER,
  NEO4J_CYPHER_HINT,
} from '@/lib/service-default-queries'

export function Neo4jPage() {
  const { data: service } = useService('neo4j')
  const { data: infoData } = useServiceInfo('neo4j')
  const { data: stats, isLoading, error } = useNeo4jGraphStats()
  const [copiedBolt, setCopiedBolt] = useState(false)
  const [copiedHttp, setCopiedHttp] = useState(false)
  const [cypher, setCypher] = useState(DEFAULT_NEO4J_CYPHER)
  const [queryRunning, setQueryRunning] = useState(false)
  const [queryResult, setQueryResult] = useState<ServiceQueryResponse | null>(null)

  const info = infoData?.info || {}
  const adminAccess = info.admin_access as AdminAccess | undefined
  const adminUrl = service?.admin_url || adminAccess?.url
  const connection = (info.connection || {}) as Record<string, string>
  const boltUri = connection.bolt_uri || `bolt://127.0.0.1:7687`
  const httpUrl = connection.http_url || adminUrl || 'http://127.0.0.1:7474'
  const labels = (stats?.labels || info.labels || []) as string[]
  const relationshipTypes = (stats?.relationshipTypes || info.relationship_types || []) as string[]
  const nodeCount = stats?.nodeCount ?? (info.node_count as number | undefined) ?? 0
  const relationshipCount =
    stats?.relationshipCount ?? (info.relationship_count as number | undefined) ?? 0

  const copyText = (text: string, setter: (value: boolean) => void) => {
    navigator.clipboard.writeText(text)
    setter(true)
    setTimeout(() => setter(false), 2000)
  }

  const runQuery = async () => {
    const query = cypher.trim()
    if (!query) return

    setQueryRunning(true)
    try {
      const result = await neo4jQuery('run_readonly_cypher', { cypher: query, limit: 100 })
      setQueryResult(result)
    } catch (err) {
      setQueryResult({
        success: false,
        error: err instanceof Error ? err.message : 'Failed to run query',
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
            <span>🕸️</span> Neo4j
          </h1>
          <p className="text-muted-foreground">Graph database for knowledge graphs and Graph RAG</p>
          <div className="mt-2 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Bolt:</span>
              <code className="rounded bg-muted px-2 py-1 text-xs">{boltUri}</code>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => copyText(boltUri, setCopiedBolt)}
              >
                {copiedBolt ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">HTTP:</span>
              <code className="rounded bg-muted px-2 py-1 text-xs">{httpUrl}</code>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => copyText(httpUrl, setCopiedHttp)}
              >
                {copiedHttp ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
              </Button>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {service && (
            <Badge variant={service.healthy ? 'default' : 'destructive'}>
              {service.healthy ? 'Healthy' : 'Unhealthy'}
            </Badge>
          )}
          {adminUrl && (
            <Button variant="outline" onClick={() => window.open(adminUrl, '_blank')}>
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Neo4j Browser
            </Button>
          )}
        </div>
      </div>

      <AdminAccessCard adminUrl={adminUrl} adminAccess={adminAccess} />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Network className="h-4 w-4" />
              Nodes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? '…' : nodeCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <GitBranch className="h-4 w-4" />
              Relationships
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? '…' : relationshipCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Database className="h-4 w-4" />
              Labels
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? '…' : labels.length}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Labels</CardTitle>
          </CardHeader>
          <CardContent>
            {error ? (
              <div className="text-destructive">Failed to load graph stats. Is Neo4j running?</div>
            ) : labels.length === 0 ? (
              <div className="text-muted-foreground">No labels yet</div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {labels.map((label) => (
                  <Badge key={label} variant="secondary">
                    {label}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Relationship types</CardTitle>
          </CardHeader>
          <CardContent>
            {relationshipTypes.length === 0 ? (
              <div className="text-muted-foreground">No relationship types yet</div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {relationshipTypes.map((relType) => (
                  <Badge key={relType} variant="outline">
                    {relType}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cypher query</CardTitle>
          <p className="text-sm text-muted-foreground">{NEO4J_CYPHER_HINT}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            className="min-h-[140px] w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
            value={cypher}
            onChange={(e) => setCypher(e.target.value)}
            spellCheck={false}
          />
          <Button onClick={runQuery} disabled={queryRunning}>
            {queryRunning ? 'Running…' : 'Run query'}
          </Button>
          {queryResult && (
            <pre className="max-h-96 overflow-auto rounded-md bg-muted p-4 text-xs">
              {JSON.stringify(queryResult, null, 2)}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
