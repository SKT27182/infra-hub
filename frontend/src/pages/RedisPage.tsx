import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Key, Search } from 'lucide-react'
import { useService, useRedisKeys } from '@/hooks'

export function RedisPage() {
  const { data: service } = useService('redis')
  const [pattern, setPattern] = useState('*')
  const { data: keys, isLoading, error, refetch } = useRedisKeys(pattern, 50)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <span>🔴</span> Redis
          </h1>
          <p className="text-muted-foreground">Cache & key-value store</p>
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

      {/* Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Keys
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Search */}
          <div className="mb-4 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Pattern (e.g., user:*)"
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
                className="w-full rounded-md border bg-background py-2 pl-10 pr-4 text-sm"
              />
            </div>
            <Button onClick={() => refetch()}>Search</Button>
          </div>

          {isLoading ? (
            <div className="text-muted-foreground">Loading keys...</div>
          ) : error ? (
            <div className="text-destructive">Failed to load keys. Is Redis running?</div>
          ) : (
            <div className="space-y-2">
              {keys?.map((key: Record<string, unknown>, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <div className="font-mono text-sm">{String(key.key)}</div>
                    <div className="text-xs text-muted-foreground">
                      Type: {String(key.type)} {key.ttl ? `| TTL: ${key.ttl}s` : ''}
                    </div>
                  </div>
                </div>
              ))}
              {(!keys || keys.length === 0) && (
                <div className="text-muted-foreground">No keys found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
