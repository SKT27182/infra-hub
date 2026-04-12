const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8888') + '/api'

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('auth_token')
  const headers = {
    ...options.headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  const response = await fetch(url, { ...options, headers })

  if (response.status === 401) {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  return response
}

export interface ServiceStatus {
  name: string
  display_name: string
  running: boolean
  healthy: boolean
  container_id: string | null
  container_name: string | null
  status: string
  ports: string[]
  admin_url: string | null
}

export interface AllServicesResponse {
  services: ServiceStatus[]
  total: number
  healthy: number
  unhealthy: number
}

export interface ServiceHealth {
  healthy: boolean
  message: string
  details: Record<string, unknown>
}

export interface ServiceInfo {
  name: string
  info: Record<string, unknown>
}

export interface PostgresQueryResponse {
  success: boolean
  database?: string
  row_count?: number
  columns?: string[]
  rows?: Record<string, unknown>[]
  error?: string
}

export interface ServiceQueryResponse {
  success: boolean
  error?: string
  count?: number
  result?: unknown
  [key: string]: unknown
}

export interface ContainerInfo {
  id: string
  name: string
  image: string
  status: string
  state: string
  created: string | null
  ports: string[]
  labels: Record<string, string>
}

export interface ServiceAction {
  success: boolean
  message: string
  service: string
}

// Health endpoints
export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetchWithAuth(`${API_BASE}/health`)
  return res.json()
}

// Services endpoints
export async function getServices(): Promise<AllServicesResponse> {
  const res = await fetchWithAuth(`${API_BASE}/services`)
  return res.json()
}

export async function getService(name: string): Promise<ServiceStatus> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}`)
  return res.json()
}

export async function getServiceHealth(name: string): Promise<ServiceHealth> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}/health`)
  return res.json()
}

export async function getServiceInfo(name: string): Promise<ServiceInfo> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}/info`)
  return res.json()
}

export async function startService(name: string): Promise<ServiceAction> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}/start`, { method: 'POST' })
  return res.json()
}

export async function stopService(name: string): Promise<ServiceAction> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}/stop`, { method: 'POST' })
  return res.json()
}

export async function restartService(name: string): Promise<ServiceAction> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}/restart`, { method: 'POST' })
  return res.json()
}

export async function getServiceLogs(name: string, tail = 100): Promise<{ logs: string; lines: number }> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}/logs?tail=${tail}`)
  return res.json()
}

// Containers endpoints
export async function getContainers(): Promise<ContainerInfo[]> {
  const res = await fetchWithAuth(`${API_BASE}/containers`)
  return res.json()
}

export async function getInfraContainers(): Promise<ContainerInfo[]> {
  const res = await fetchWithAuth(`${API_BASE}/containers/infra`)
  return res.json()
}

export async function startContainer(id: string): Promise<ServiceAction> {
  const res = await fetchWithAuth(`${API_BASE}/containers/${id}/start`, { method: 'POST' })
  return res.json()
}

export async function stopContainer(id: string): Promise<ServiceAction> {
  const res = await fetchWithAuth(`${API_BASE}/containers/${id}/stop`, { method: 'POST' })
  return res.json()
}

export async function restartContainer(id: string): Promise<ServiceAction> {
  const res = await fetchWithAuth(`${API_BASE}/containers/${id}/restart`, { method: 'POST' })
  return res.json()
}

// Deep service actions (simplified)
export async function redisQuery(command: string, args: unknown[] = []): Promise<ServiceQueryResponse> {
  const res = await fetchWithAuth(`${API_BASE}/services/redis/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command, args }),
  })
  return res.json()
}

export async function mongodbQuery(action: string, params: Record<string, unknown> = {}): Promise<ServiceQueryResponse> {
  const res = await fetchWithAuth(`${API_BASE}/services/mongodb/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, params }),
  })
  return res.json()
}

export async function minioQuery(action: string, params: Record<string, unknown> = {}): Promise<ServiceQueryResponse> {
  const res = await fetchWithAuth(`${API_BASE}/services/minio/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, params }),
  })
  return res.json()
}

export async function qdrantQuery(action: string, params: Record<string, unknown> = {}): Promise<ServiceQueryResponse> {
  const res = await fetchWithAuth(`${API_BASE}/services/qdrant/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, params }),
  })
  return res.json()
}

export async function createPostgresDB(name: string): Promise<{ success: boolean }> {
  const res = await fetchWithAuth(`${API_BASE}/services/postgres/databases/${name}`, { method: 'POST' })
  return res.json()
}

export async function dropPostgresDB(name: string): Promise<{ success: boolean }> {
  const res = await fetchWithAuth(`${API_BASE}/services/postgres/databases/${name}`, { method: 'DELETE' })
  return res.json()
}

export async function postgresQuery(query: string, database?: string): Promise<PostgresQueryResponse> {
  const res = await fetchWithAuth(`${API_BASE}/services/postgres/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, database }),
  })
  return res.json()
}

export async function createMinioBucket(name: string): Promise<{ success: boolean }> {
  const res = await fetchWithAuth(`${API_BASE}/services/minio/buckets/${name}`, { method: 'POST' })
  return res.json()
}

export async function dropMinioBucket(name: string): Promise<{ success: boolean }> {
  const res = await fetchWithAuth(`${API_BASE}/services/minio/buckets/${name}`, { method: 'DELETE' })
  return res.json()
}

export async function dropMongoDBDB(name: string): Promise<{ success: boolean }> {
  const res = await fetchWithAuth(`${API_BASE}/services/mongodb/databases/${name}`, { method: 'DELETE' })
  return res.json()
}

export async function deleteQdrantCollection(name: string): Promise<{ success: boolean }> {
  const res = await fetchWithAuth(`${API_BASE}/services/qdrant/collections/${name}`, { method: 'DELETE' })
  return res.json()
}
