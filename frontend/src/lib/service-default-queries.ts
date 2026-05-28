export const DEFAULT_POSTGRES_QUERY = `SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;`

export const POSTGRES_QUERY_HINT =
  'Starter query — lists all tables in the public schema'
