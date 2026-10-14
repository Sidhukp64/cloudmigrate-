import { api } from './client'

export interface AuditLog {
  id: string
  action: string
  actor_id?: string
  actor_email?: string
  resource_type?: string
  resource_id?: string
  details?: Record<string, unknown>
  ip_address?: string
  checksum?: string
  created_at: string
}

export const auditApi = {
  list: (params?: {
    action?: string
    actor_email?: string
    resource_type?: string
    page?: number
    page_size?: number
    start_date?: string
    end_date?: string
  }) => api.get<AuditLog[]>('/audit', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<AuditLog>(`/audit/${id}`).then((r) => r.data),

  exportCsv: () =>
    api.get('/audit/export', { responseType: 'blob' }),
}
