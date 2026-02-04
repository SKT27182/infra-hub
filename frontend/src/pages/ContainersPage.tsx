import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useInfraContainers } from '@/hooks'
import { startContainer, stopContainer, restartContainer } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'
import { Play, Square, RotateCcw } from 'lucide-react'

export function ContainersPage() {
  const { data: containers, isLoading, error } = useInfraContainers()
  const queryClient = useQueryClient()

  const handleAction = async (id: string, action: 'start' | 'stop' | 'restart') => {
    const actions = { start: startContainer, stop: stopContainer, restart: restartContainer }
    await actions[action](id)
    queryClient.invalidateQueries({ queryKey: ['containers'] })
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-muted-foreground">Loading containers...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
        <p className="text-destructive">Failed to load containers.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Containers</h1>
        <p className="text-muted-foreground">
          Manage Docker containers
        </p>
      </div>

      <div className="space-y-4">
        {containers?.map((container) => (
          <Card key={container.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base font-medium">
                {container.name}
              </CardTitle>
              <Badge variant={container.status === 'running' ? 'default' : 'secondary'}>
                {container.status}
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div>Image: <span className="font-mono">{container.image}</span></div>
                  <div>ID: <span className="font-mono">{container.id}</span></div>
                  {container.ports.length > 0 && (
                    <div>Ports: {container.ports.join(', ')}</div>
                  )}
                </div>
                <div className="flex gap-2">
                  {container.status !== 'running' ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleAction(container.id, 'start')}
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                  ) : (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleAction(container.id, 'stop')}
                      >
                        <Square className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleAction(container.id, 'restart')}
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
