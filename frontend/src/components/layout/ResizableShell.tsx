import type { ReactNode } from 'react'
import { Panel, Group, Separator, type Layout } from 'react-resizable-panels'
import { cn } from '@/lib/utils'

interface ResizableShellProps {
  left?: ReactNode
  main: ReactNode
  right?: ReactNode
  className?: string
  storageKey?: string
}

export function ResizableShell({
  left,
  main,
  right,
  className,
  storageKey = 'infra-hub-panels',
}: ResizableShellProps) {
  const layout: Layout =
    right && left
      ? ({ left: 18, main: 55, right: 27 } as Layout)
      : right
        ? ({ main: 65, right: 35 } as Layout)
        : ({ left: 20, main: 80 } as Layout)

  return (
    <Group
      orientation="horizontal"
      className={cn('h-full min-h-0', className)}
      defaultLayout={layout}
      id={storageKey}
    >
      {left && (
        <>
          <Panel id="left" defaultSize={20} minSize={12} maxSize={35}>
            {left}
          </Panel>
          <Separator className="w-1 bg-border hover:bg-primary/30 transition-colors" />
        </>
      )}
      <Panel id="main" minSize={30} defaultSize={left ? undefined : 65}>
        {main}
      </Panel>
      {right && (
        <>
          <Separator className="w-1 bg-border hover:bg-primary/30 transition-colors" />
          <Panel id="right" defaultSize={30} minSize={18} maxSize={45}>
            {right}
          </Panel>
        </>
      )}
    </Group>
  )
}
