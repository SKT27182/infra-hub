export const DEFAULT_POSTGRES_QUERY = `SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;`

export const POSTGRES_QUERY_HINT =
  'Starter query — lists all tables in the public schema'

export const DEFAULT_NEO4J_CYPHER = `MATCH (n)
RETURN labels(n) AS labels, count(*) AS count
LIMIT 25`

export const NEO4J_CYPHER_HINT =
  'Read-only Cypher only. Use Neo4j Browser for interactive graph visualization (e.g. MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50).'

export const DEFAULT_OPENSEARCH_QUERY = `{
  "action": "list_indices",
  "params": {}
}`

export const OPENSEARCH_QUERY_HINT =
  'Actions: list_indices, cluster_health, index_info, search, knn_search, suggest, delete_index. Use Dashboards Dev Tools for richer Query DSL.'
