import { useQuery } from '@tanstack/react-query'
import {
  getPostgresDatabases,
  getRedisKeys,
  getMongoDBDatabases,
  getQdrantCollections,
  getMinioBuckets,
} from '@/lib/api'

export function usePostgresDatabases() {
  return useQuery({
    queryKey: ['postgres', 'databases'],
    queryFn: getPostgresDatabases,
  })
}

export function useRedisKeys(pattern = '*', count = 100) {
  return useQuery({
    queryKey: ['redis', 'keys', pattern, count],
    queryFn: () => getRedisKeys(pattern, count),
  })
}

export function useMongoDBDatabases() {
  return useQuery({
    queryKey: ['mongodb', 'databases'],
    queryFn: getMongoDBDatabases,
  })
}

export function useQdrantCollections() {
  return useQuery({
    queryKey: ['qdrant', 'collections'],
    queryFn: getQdrantCollections,
  })
}

export function useMinioBuckets() {
  return useQuery({
    queryKey: ['minio', 'buckets'],
    queryFn: getMinioBuckets,
  })
}
