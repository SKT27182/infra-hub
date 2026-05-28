import type { ReactNode } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'

interface AuthLoginLayoutProps {
  productName: string
  tagline: string
  icon: ReactNode
  children: ReactNode
  footer?: ReactNode
}

export function AuthLoginLayout({
  productName,
  tagline,
  icon,
  children,
  footer,
}: AuthLoginLayoutProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="p-3 rounded-xl bg-primary/10 text-primary">{icon}</div>
          <div>
            <h1 className="text-3xl font-bold">{productName}</h1>
            <p className="text-sm text-muted-foreground">{tagline}</p>
          </div>
        </div>
        <Card>{children}</Card>
        {footer && <div className="mt-4 text-center text-sm text-muted-foreground">{footer}</div>}
      </div>
    </div>
  )
}

export function AuthLoginCardHeader({ title, description }: { title: string; description: string }) {
  return (
    <CardHeader className="text-center">
      <CardTitle>{title}</CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
  )
}

export { CardContent, CardFooter }
