import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Database, Trash2, Copy, Check, Users, Server } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useService, usePostgresDatabases, usePostgresActions, useServiceInfo } from '@/hooks'
import { postgresQuery, type PostgresQueryResponse } from '@/lib/api'

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
  const { data: infoData } = useServiceInfo('postgres')
  const { dropDB } = usePostgresActions()
  const [copied, setCopied] = useState(false)
  const [selectedDb, setSelectedDb] = useState('main_db')
  const [query, setQuery] = useState('SELECT now() AS server_time;')
  const [queryRunning, setQueryRunning] = useState(false)
  const [queryResult, setQueryResult] = useState<PostgresQueryResponse | null>(null)

  const info = infoData?.info || {}
  const databaseNames = (databases || []).map((db: Record<string, unknown>) => String(db.name))

  useEffect(() => {
    if (databaseNames.length > 0 && !databaseNames.includes(selectedDb)) {
      setSelectedDb(databaseNames[0])
    }
  }, [databaseNames, selectedDb])

  const copyEndpoint = () => {
    const url = (info.connection as any)?.url || `postgresql://127.0.0.1:${service?.ports[0]?.split(':')[0] || '5432'}`
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const runQuery = async () => {
    const sql = query.trim()
    if (!sql) return

    setQueryRunning(true)
    try {
      const result = await postgresQuery(sql, selectedDb)
      setQueryResult(result)
    } catch (error) {
      setQueryResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to run query',
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
            <span>🐘</span> PostgreSQL
          </h1>
          <p className="text-muted-foreground">Database management</p>
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
            onClick={() => window.open('http://localhost:5050', '_blank')}
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            pgAdmin
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
            <CardTitle className="text-sm font-medium">Active Connections</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{String(info.active_connections ?? 0)}</div>
            <p className="text-xs text-muted-foreground">Max: {String(info.max_connections ?? '—')}</p>
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
                  {String(db.name) !== 'postgres' && (
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
                  )}
                </div>
              ))}
              {(!databases || databases.length === 0) && (
                <div className="text-muted-foreground">No databases found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* SQL Query */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            SQL Query
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <select
              className="h-10 rounded-md border bg-background px-3 text-sm"
              value={selectedDb}
              onChange={(e) => setSelectedDb(e.target.value)}
            >
              {databaseNames.map((dbName) => (
                <option key={dbName} value={dbName}>
                  {dbName}
                </option>
              ))}
              {databaseNames.length === 0 && <option value="main_db">main_db</option>}
            </select>
            <Button onClick={runQuery} disabled={queryRunning}>
              {queryRunning ? 'Running...' : 'Run Query'}
            </Button>
          </div>

          <textarea
            className="min-h-28 w-full rounded-md border bg-background p-3 font-mono text-sm"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Write a read-only SQL query"
          />

          {queryResult && !queryResult.success && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {queryResult.error || 'Query failed'}
            </div>
          )}

          {queryResult?.success && (
            <div className="space-y-2">
              <div className="text-sm text-muted-foreground">
                Database: <span className="font-medium">{queryResult.database}</span> | Rows: <span className="font-medium">{String(queryResult.row_count ?? 0)}</span>
              </div>
              {queryResult.columns && queryResult.columns.length > 0 ? (
                <div className="overflow-x-auto rounded-md border">
                  <table className="min-w-full text-sm">
                    <thead className="bg-muted/40">
                      <tr>
                        {queryResult.columns.map((col) => (
                          <th key={col} className="px-3 py-2 text-left font-medium">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(queryResult.rows || []).map((row, idx) => (
                        <tr key={idx} className="border-t">
                          {queryResult.columns!.map((col) => (
                            <td key={`${idx}-${col}`} className="px-3 py-2 align-top">
                              <code className="text-xs">
                                {typeof row[col] === 'object' ? JSON.stringify(row[col]) : String(row[col] ?? 'null')}
                              </code>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">Query executed successfully.</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
