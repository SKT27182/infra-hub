import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/theme-provider'
import { AppLayout } from '@/components/layout'
import {
  DashboardPage,
  ServiceDetailPage,
  ContainersPage,
  PostgresPage,
  RedisPage,
  MongoDBPage,
  QdrantPage,
  MinIOPage,
} from '@/pages'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 5,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="infra-hub-theme">
        <BrowserRouter>
          <AppLayout>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/services/:name" element={<ServiceDetailPage />} />
              <Route path="/containers" element={<ContainersPage />} />
              {/* Deep service pages */}
              <Route path="/services/postgres" element={<PostgresPage />} />
              <Route path="/services/redis" element={<RedisPage />} />
              <Route path="/services/mongodb" element={<MongoDBPage />} />
              <Route path="/services/qdrant" element={<QdrantPage />} />
              <Route path="/services/minio" element={<MinIOPage />} />
            </Routes>
          </AppLayout>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
