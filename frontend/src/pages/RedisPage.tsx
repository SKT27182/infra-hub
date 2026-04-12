import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Key, Copy, Check, MemoryStick, Users, Server } from 'lucide-react'
import { useState } from 'react'
import { useService, useServiceInfo } from '@/hooks'
import { redisQuery, type ServiceQueryResponse } from '@/lib/api'

export function RedisPage() {
  const { data: service } = useService('redis')
  const { data: infoData, isLoading } = useServiceInfo('redis')
  const [copied, setCopied] = useState(false)
  const [queryText, setQueryText] = useState('{\n  "command": "PING",\n  "args": []\n}')
  const [queryRunning, setQueryRunning] = useState(false)
  const [queryResult, setQueryResult] = useState<ServiceQueryResponse | null>(null)

  const info = infoData?.info || {}

  const copyEndpoint = () => {
    const url = (info.connection as any)?.url || `redis://127.0.0.1:${service?.ports[0]?.split(':')[0] || '6379'}`
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    if (days > 0) return `${days}d ${hours}h`
    if (hours > 0) return `${hours}h ${mins}m`
    return `${mins}m`
  }

  const runQuery = async () => {
    setQueryRunning(true)
    try {
      const parsed = JSON.parse(queryText) as { command?: string; args?: unknown[] }
      if (!parsed.command) {
        setQueryResult({ success: false, error: 'Query JSON must include "command"' })
        return
      }
      const result = await redisQuery(parsed.command, parsed.args || [])
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
            <span>🔴</span> Redis
          </h1>
          <p className="text-muted-foreground">Cache & key-value store</p>
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
            onClick={() => window.open('http://localhost:5540', '_blank')}
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            RedisInsight
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      {isLoading ? (
        <div className="text-muted-foreground">Loading Redis info...</div>
      ) : info.error ? (
        <div className="text-destructive">Failed to load Redis info. Is Redis running?</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Keys</CardTitle>
              <Key className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{String(info.total_keys ?? 0)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Memory</CardTitle>
              <MemoryStick className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{String((info.memory as any)?.used ?? '—')}</div>
              <p className="text-xs text-muted-foreground">Peak: {String((info.memory as any)?.peak ?? '—')}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Clients</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{String(info.connected_clients ?? 0)}</div>
              <p className="text-xs text-muted-foreground">Blocked: {String(info.blocked_clients ?? 0)}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Server</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">v{String(info.redis_version ?? '?')}</div>
              <p className="text-xs text-muted-foreground">Uptime: {formatUptime(Number(info.uptime_seconds) || 0)}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* RedisInsight link */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Key Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-muted-foreground">
              For deep key inspection and management, use the integrated <strong>RedisInsight</strong> tool.
            </p>
            <Button
              className="w-full"
              onClick={() => window.open('http://localhost:5540', '_blank')}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Open RedisInsight
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Query */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Query
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            className="min-h-28 w-full rounded-md border bg-background p-3 font-mono text-sm"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder='{"command":"PING","args":[]}'
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
