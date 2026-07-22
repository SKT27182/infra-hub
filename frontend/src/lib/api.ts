export const API_BASE = '/api/v2'

export interface ApiErrorBody {
  error?: { code?: string; message?: string; request_id?: string }
  detail?: string | { msg?: string }[]
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const response = await fetch(url, { ...options, credentials: 'include' })

  if (response.status === 401) {
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorBody
    const validation = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).filter(Boolean).join(', ')
      : undefined
    throw new Error(
      body.error?.message || validation ||
        (typeof body.detail === 'string' ? body.detail : undefined) ||
        `Request failed (${response.status})`
    )
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
  admin: AdminContainerStatus | null
}

export interface AdminContainerStatus {
  container_name: string
  running: boolean
  healthy: boolean
  status: string
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
  command?: string | null
  truncated?: boolean
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
  action: 'start' | 'stop' | 'restart'
  message: string
  service: string
  containers: Array<{
    name: string
    state: string
    healthy: boolean
    health: string
  }>
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

export async function startServiceAdmin(name: string): Promise<ServiceAction> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}/admin/start`, { method: 'POST' })
  return res.json()
}

export async function stopServiceAdmin(name: string): Promise<ServiceAction> {
  const res = await fetchWithAuth(`${API_BASE}/services/${name}/admin/stop`, { method: 'POST' })
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

export async function neo4jQuery(action: string, params: Record<string, unknown> = {}): Promise<ServiceQueryResponse> {
  const res = await fetchWithAuth(`${API_BASE}/services/neo4j/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, params }),
  })
  return res.json()
}

export async function opensearchQuery(action: string, params: Record<string, unknown> = {}): Promise<ServiceQueryResponse> {
  const res = await fetchWithAuth(`${API_BASE}/services/opensearch/query`, {
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

export async function deleteOpenSearchIndex(name: string): Promise<{ success: boolean }> {
  const res = await fetchWithAuth(`${API_BASE}/services/opensearch/indices/${name}`, { method: 'DELETE' })
  return res.json()
}

export interface InfraUser {
  id: number
  email: string
  name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export async function getMe(): Promise<InfraUser> {
  const res = await fetchWithAuth(`${API_BASE}/auth/me`)
  return res.json()
}

export async function loginUser(email: string, password: string): Promise<InfraUser> {
  const res = await fetchWithAuth(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return res.json()
}

export async function logoutUser(): Promise<void> {
  await fetchWithAuth(`${API_BASE}/auth/logout`, { method: 'POST' })
}

export async function updateProfile(name: string): Promise<InfraUser> {
  const res = await fetchWithAuth(`${API_BASE}/auth/me/profile`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  return res.json()
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<void> {
  await fetchWithAuth(`${API_BASE}/auth/me/password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  })
}
