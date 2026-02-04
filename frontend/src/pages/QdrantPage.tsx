import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Layers } from 'lucide-react'
import { useService, useQdrantCollections } from '@/hooks'

export function QdrantPage() {
  const { data: service } = useService('qdrant')
  const { data: collections, isLoading, error } = useQdrantCollections()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold">
            <span>🔷</span> Qdrant
          </h1>
          <p className="text-muted-foreground">Vector database</p>
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
                  <Badge variant="secondary">{String(coll.status || 'unknown')}</Badge>
                </div>
              ))}
              {(!collections || collections.length === 0) && (
                <div className="text-muted-foreground">No collections found</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
