import { api } from './client'

export interface Webhook {
  id: string
  name: string
  url: string
  events: string[]
  is_active: boolean
  created_at: string
}

export interface WebhookDelivery {
  id: string
  endpoint_id: string
  event_type: string
  status: 'pending' | 'success' | 'failed' | 'retrying'
  http_status_code?: number
  attempt_count: number
  delivered_at?: string
  created_at: string
}

export const webhooksApi = {
  list: () =>
    api.get<Webhook[]>('/webhooks').then((r) => r.data),

  create: (payload: { name: string; url: string; events: string[]; secret?: string }) =>
    api.post<Webhook>('/webhooks', payload).then((r) => r.data),

  update: (id: string, payload: Partial<{ name: string; url: string; is_active: boolean }>) =>
    api.put<Webhook>(`/webhooks/${id}`, payload).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/webhooks/${id}`),

  getDeliveries: (id: string) =>
    api.get<WebhookDelivery[]>(`/webhooks/${id}/deliveries`).then((r) => r.data),
}
