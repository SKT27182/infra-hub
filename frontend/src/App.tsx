import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout'
import {
  DashboardPage,
  ServicesPage,
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
      <BrowserRouter>
        <AppLayout>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/services" element={<ServicesPage />} />
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
    </QueryClientProvider>
  )
}

export default App
