import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  getServiceInfo, 
  dropPostgresDB, 
  dropMinioBucket, 
  dropMongoDBDB, 
  deleteQdrantCollection 
} from '@/lib/api'

export function usePostgresDatabases() {
  return useQuery({
    queryKey: ['postgres', 'databases'],
    queryFn: async () => {
      const { info } = await getServiceInfo('postgres')
      return (info.databases as any[]) || []
    },
  })
}

export function usePostgresActions() {
  const queryClient = useQueryClient()
  const dropDB = useMutation({
    mutationFn: dropPostgresDB,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['postgres', 'databases'] })
      queryClient.invalidateQueries({ queryKey: ['service-info', 'postgres'] })
    },
  })
  return { dropDB }
}

export function useRedisKeys() {
  return useQuery({
    queryKey: ['redis', 'keys'],
    queryFn: () => [], // Simplified as backend list_keys was removed
  })
}

export function useMongoDBDatabases() {
  return useQuery({
    queryKey: ['mongodb', 'databases'],
    queryFn: async () => {
      const { info } = await getServiceInfo('mongodb')
      return (info.databases as any[]) || []
    },
  })
}

export function useMongoDBActions() {
  const queryClient = useQueryClient()
  const dropDB = useMutation({
    mutationFn: dropMongoDBDB,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mongodb', 'databases'] })
      queryClient.invalidateQueries({ queryKey: ['service-info', 'mongodb'] })
    },
  })
  return { dropDB }
}

export function useQdrantCollections() {
  return useQuery({
    queryKey: ['qdrant', 'collections'],
    queryFn: async () => {
      const { info } = await getServiceInfo('qdrant')
      return (info.collections as any[]) || []
    },
  })
}

export function useQdrantActions() {
  const queryClient = useQueryClient()
  const dropCollection = useMutation({
    mutationFn: deleteQdrantCollection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qdrant', 'collections'] })
      queryClient.invalidateQueries({ queryKey: ['service-info', 'qdrant'] })
    },
  })
  return { dropCollection }
}

export function useMinioBuckets() {
  return useQuery({
    queryKey: ['minio', 'buckets'],
    queryFn: async () => {
      const { info } = await getServiceInfo('minio')
      return (info.buckets as any[]) || []
    },
  })
}

export function useMinioActions() {
  const queryClient = useQueryClient()
  const dropBucket = useMutation({
    mutationFn: dropMinioBucket,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['minio', 'buckets'] })
      queryClient.invalidateQueries({ queryKey: ['service-info', 'minio'] })
    },
  })
  return { dropBucket }
}
