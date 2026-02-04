const API_BASE = '/api'

export interface ServiceStatus {
  name: string
  display_name: string
  running: boolean
  healthy: boolean
  container_id: string | null
  container_name: string | null
  status: string
  uptime: string | null
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
  const res = await fetch(`${API_BASE}/health`)
  return res.json()
}

// Services endpoints
export async function getServices(): Promise<AllServicesResponse> {
  const res = await fetch(`${API_BASE}/services`)
  return res.json()
}

export async function getService(name: string): Promise<ServiceStatus> {
  const res = await fetch(`${API_BASE}/services/${name}`)
  return res.json()
}

export async function getServiceHealth(name: string): Promise<ServiceHealth> {
  const res = await fetch(`${API_BASE}/services/${name}/health`)
  return res.json()
}

export async function getServiceInfo(name: string): Promise<ServiceInfo> {
  const res = await fetch(`${API_BASE}/services/${name}/info`)
  return res.json()
}

export async function startService(name: string): Promise<ServiceAction> {
  const res = await fetch(`${API_BASE}/services/${name}/start`, { method: 'POST' })
  return res.json()
}

export async function stopService(name: string): Promise<ServiceAction> {
  const res = await fetch(`${API_BASE}/services/${name}/stop`, { method: 'POST' })
  return res.json()
}

export async function restartService(name: string): Promise<ServiceAction> {
  const res = await fetch(`${API_BASE}/services/${name}/restart`, { method: 'POST' })
  return res.json()
}

export async function getServiceLogs(name: string, tail = 100): Promise<{ logs: string; lines: number }> {
  const res = await fetch(`${API_BASE}/services/${name}/logs?tail=${tail}`)
  return res.json()
}

// Containers endpoints
export async function getContainers(): Promise<ContainerInfo[]> {
  const res = await fetch(`${API_BASE}/containers`)
  return res.json()
}

export async function getInfraContainers(): Promise<ContainerInfo[]> {
  const res = await fetch(`${API_BASE}/containers/infra`)
  return res.json()
}

export async function startContainer(id: string): Promise<ServiceAction> {
  const res = await fetch(`${API_BASE}/containers/${id}/start`, { method: 'POST' })
  return res.json()
}

export async function stopContainer(id: string): Promise<ServiceAction> {
  const res = await fetch(`${API_BASE}/containers/${id}/stop`, { method: 'POST' })
  return res.json()
}

export async function restartContainer(id: string): Promise<ServiceAction> {
  const res = await fetch(`${API_BASE}/containers/${id}/restart`, { method: 'POST' })
  return res.json()
}

// Deep service endpoints
export async function getPostgresDatabases(): Promise<Record<string, unknown>[]> {
  const res = await fetch(`${API_BASE}/services/postgres/databases`)
  return res.json()
}

export async function getRedisKeys(pattern = '*', count = 100): Promise<Record<string, unknown>[]> {
  const res = await fetch(`${API_BASE}/services/redis/keys?pattern=${pattern}&count=${count}`)
  return res.json()
}

export async function getMongoDBDatabases(): Promise<Record<string, unknown>[]> {
  const res = await fetch(`${API_BASE}/services/mongodb/databases`)
  return res.json()
}

export async function getQdrantCollections(): Promise<Record<string, unknown>[]> {
  const res = await fetch(`${API_BASE}/services/qdrant/collections`)
  return res.json()
}

export async function getMinioBuckets(): Promise<Record<string, unknown>[]> {
  const res = await fetch(`${API_BASE}/services/minio/buckets`)
  return res.json()
}
