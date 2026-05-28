import { useState, useEffect } from 'react'
import { Users, Plus, Trash2, Pencil } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
  type InfraUser,
} from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import { isSuperAdmin } from '@/lib/roles'
import { Navigate } from 'react-router-dom'

export function UsersPage() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState<InfraUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [formEmail, setFormEmail] = useState('')
  const [formPassword, setFormPassword] = useState('')
  const [formName, setFormName] = useState('')
  const [saving, setSaving] = useState(false)

  if (!isSuperAdmin(currentUser?.role)) {
    return <Navigate to="/" replace />
  }

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      setUsers(await listUsers())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const resetForm = () => {
    setFormEmail('')
    setFormPassword('')
    setFormName('')
    setEditId(null)
    setShowCreate(false)
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await createUser({
        email: formEmail,
        password: formPassword,
        name: formName || undefined,
      })
      resetForm()
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editId == null) return
    setSaving(true)
    setError('')
    try {
      await updateUser(editId, {
        name: formName || undefined,
        password: formPassword || undefined,
      })
      resetForm()
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Update failed')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleActive = async (u: InfraUser) => {
    try {
      await updateUser(u.id, { is_active: !u.is_active })
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Update failed')
    }
  }

  const handleDelete = async (u: InfraUser) => {
    if (!confirm(`Delete user "${u.email}"?`)) return
    try {
      await deleteUser(u.id)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  const startEdit = (u: InfraUser) => {
    setEditId(u.id)
    setFormEmail(u.email)
    setFormName(u.name || '')
    setFormPassword('')
    setShowCreate(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Users</h1>
            <p className="text-sm text-muted-foreground">Manage platform access</p>
          </div>
        </div>
        <Button onClick={() => { resetForm(); setShowCreate(true) }}>
          <Plus className="h-4 w-4 mr-2" />
          Add user
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {(showCreate || editId != null) && (
        <Card>
          <CardHeader>
            <CardTitle>{editId != null ? 'Edit user' : 'Create user'}</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={editId != null ? handleUpdate : handleCreate}
              className="grid gap-4 max-w-md"
            >
              {editId == null && (
                <div>
                  <label className="text-sm font-medium">Email</label>
                  <Input
                    type="email"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    required
                  />
                </div>
              )}
              <div>
                <label className="text-sm font-medium">Full name</label>
                <Input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium">
                  {editId != null ? 'New password (optional)' : 'Password'}
                </label>
                <Input
                  type="password"
                  value={formPassword}
                  onChange={(e) => setFormPassword(e.target.value)}
                  required={editId == null}
                  minLength={8}
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving ? 'Saving…' : editId != null ? 'Save' : 'Create'}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <p className="p-6 text-muted-foreground">Loading…</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="p-4">Email</th>
                    <th className="p-4">Name</th>
                    <th className="p-4">Role</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b last:border-0">
                      <td className="p-4">{u.email}</td>
                      <td className="p-4">{u.name || '—'}</td>
                      <td className="p-4">
                        <span className="rounded-md bg-muted px-2 py-0.5 text-xs">
                          {u.role}
                        </span>
                      </td>
                      <td className="p-4">
                        {u.is_active ? 'Active' : 'Inactive'}
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleToggleActive(u)}
                          disabled={u.role === 'SUPER_ADMIN' && u.is_active}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => startEdit(u)}>
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDelete(u)}
                          disabled={u.id === currentUser?.id}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
