export type InfraRole = 'SUPER_ADMIN' | 'USER'

export function isSuperAdmin(role: string | undefined): boolean {
  return role === 'SUPER_ADMIN'
}
