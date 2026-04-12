import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/theme-provider'
import { AppLayout, ProtectedRoute } from '@/components/layout'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import {
  DashboardPage,
  ServiceDetailPage,
  ContainersPage,
  PostgresPage,
  RedisPage,
  MongoDBPage,
  QdrantPage,
  MinIOPage,
  LoginPage,
} from '@/pages'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 5,
      retry: 1,
    },
  },
})

function AppRoutes() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      <Route
        path="/login"
        element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" />}
      />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout>
              <DashboardPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/containers"
        element={
          <ProtectedRoute>
            <AppLayout>
              <ContainersPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/services/:name"
        element={
          <ProtectedRoute>
            <AppLayout>
              <ServiceDetailPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/services/postgres"
        element={
          <ProtectedRoute>
            <AppLayout>
              <PostgresPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/services/redis"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RedisPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/services/mongodb"
        element={
          <ProtectedRoute>
            <AppLayout>
              <MongoDBPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/services/qdrant"
        element={
          <ProtectedRoute>
            <AppLayout>
              <QdrantPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/services/minio"
        element={
          <ProtectedRoute>
            <AppLayout>
              <MinIOPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider defaultTheme="dark" storageKey="infra-hub-theme">
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
