import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getServices,
  getService,
  getServiceHealth,
  getServiceInfo,
  startService,
  stopService,
  restartService,
  getServiceLogs,
  getInfraContainers,
  type ServiceStatus,
  type AllServicesResponse,
} from '@/lib/api'

export function useServices() {
  return useQuery<AllServicesResponse>({
    queryKey: ['services'],
    queryFn: getServices,
    refetchInterval: 5000,
  })
}

export function useService(name: string) {
  return useQuery<ServiceStatus>({
    queryKey: ['service', name],
    queryFn: () => getService(name),
    refetchInterval: 5000,
    enabled: !!name,
  })
}

export function useServiceHealth(name: string) {
  return useQuery({
    queryKey: ['service-health', name],
    queryFn: () => getServiceHealth(name),
    enabled: !!name,
  })
}

export function useServiceInfo(name: string) {
  return useQuery({
    queryKey: ['service-info', name],
    queryFn: () => getServiceInfo(name),
    enabled: !!name,
  })
}

export function useServiceLogs(name: string, tail = 100) {
  return useQuery({
    queryKey: ['service-logs', name, tail],
    queryFn: () => getServiceLogs(name, tail),
    enabled: !!name,
    refetchInterval: 10000,
  })
}

export function useInfraContainers() {
  return useQuery({
    queryKey: ['containers', 'infra'],
    queryFn: getInfraContainers,
    refetchInterval: 5000,
  })
}

export function useServiceActions(name: string) {
  const queryClient = useQueryClient()

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['services'] })
    queryClient.invalidateQueries({ queryKey: ['service', name] })
  }

  const start = useMutation({
    mutationFn: () => startService(name),
    onSuccess: invalidate,
  })

  const stop = useMutation({
    mutationFn: () => stopService(name),
    onSuccess: invalidate,
  })

  const restart = useMutation({
    mutationFn: () => restartService(name),
    onSuccess: invalidate,
  })

  return { start, stop, restart }
}
