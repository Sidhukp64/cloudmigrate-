import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, ChevronDown, ChevronUp, CheckCircle, XCircle, Webhook } from 'lucide-react'
import toast from 'react-hot-toast'
import { webhooksApi, Webhook as WebhookType, WebhookDelivery } from '../api/webhooks'
import { formatDistanceToNow } from 'date-fns'
import { useAuthStore } from '../store/authStore'

const EVENTS = ['*', 'job.run.started', 'job.run.completed', 'job.run.failed']

function WebhookCard({ hook }: { hook: WebhookType }) {
  const [expanded, setExpanded] = useState(false)
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)

  const { data: deliveries = [] } = useQuery({
    queryKey: ['webhook-deliveries', hook.id],
    queryFn: () => webhooksApi.getDeliveries(hook.id),
    enabled: expanded,
  })

  const toggleMutation = useMutation({
    mutationFn: () => webhooksApi.update(hook.id, { is_active: !hook.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['webhooks'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: () => webhooksApi.delete(hook.id),
    onSuccess: () => {
      toast.success('Webhook deleted')
      qc.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })

  const successCount = deliveries.filter((d: WebhookDelivery) => d.status === 'success').length
  const failCount = deliveries.filter((d: WebhookDelivery) => d.status === 'failed').length

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Webhook className="w-4 h-4 text-brand-400 shrink-0" />
            <p className="font-semibold text-white">{hook.name}</p>
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
              hook.is_active ? 'bg-green-900 text-green-300' : 'bg-gray-700 text-gray-400'
            }`}>
              {hook.is_active ? 'Active' : 'Paused'}
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1 font-mono truncate">{hook.url}</p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {hook.events.map((e) => (
              <span key={e} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-mono">{e}</span>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 ml-4 shrink-0">
          {(user?.role === 'admin' || user?.role === 'operator') && (
            <button
              onClick={() => toggleMutation.mutate()}
              className="text-xs btn-secondary py-1 px-2"
            >
              {hook.is_active ? 'Pause' : 'Resume'}
            </button>
          )}
          {user?.role === 'admin' && (
            <button
              onClick={() => { if (confirm('Delete webhook?')) deleteMutation.mutate() }}
              className="p-1.5 hover:bg-red-900/40 rounded text-red-400 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 transition-colors"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Deliveries */}
      {expanded && (
        <div className="mt-4 border-t border-gray-800 pt-4">
          <div className="flex items-center gap-4 mb-3">
            <span className="text-xs text-green-400 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" />
              {successCount} success
            </span>
            <span className="text-xs text-red-400 flex items-center gap-1">
              <XCircle className="w-3.5 h-3.5" />
              {failCount} failed
            </span>
          </div>
          <div className="space-y-2">
            {deliveries.slice(0, 10).map((d: WebhookDelivery) => (
              <div key={d.id} className="flex items-center justify-between text-xs bg-gray-800 rounded px-3 py-2">
                <div className="flex items-center gap-2">
                  {d.status === 'success' ? (
                    <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                  )}
                  <span className="font-mono text-gray-300">{d.event_type}</span>
                </div>
                <div className="flex items-center gap-3 text-gray-500">
                  {d.http_status_code && <span className="font-mono">HTTP {d.http_status_code}</span>}
                  <span>{formatDistanceToNow(new Date(d.created_at), { addSuffix: true })}</span>
                </div>
              </div>
            ))}
            {deliveries.length === 0 && (
              <p className="text-gray-500 text-center py-2">No deliveries yet</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function WebhooksPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [selectedEvents, setSelectedEvents] = useState<string[]>(['*'])
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const canOperate = user?.role === 'admin' || user?.role === 'operator'

  const { data: webhooks = [], isLoading } = useQuery({
    queryKey: ['webhooks'],
    queryFn: webhooksApi.list,
  })

  const createMutation = useMutation({
    mutationFn: webhooksApi.create,
    onSuccess: () => {
      toast.success('Webhook registered!')
      qc.invalidateQueries({ queryKey: ['webhooks'] })
      setShowCreate(false)
      setSelectedEvents(['*'])
    },
    onError: () => toast.error('Failed to create webhook'),
  })

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    createMutation.mutate({
      name: fd.get('name') as string,
      url: fd.get('url') as string,
      secret: (fd.get('secret') as string) || undefined,
      events: selectedEvents,
    })
  }

  const toggleEvent = (ev: string) => {
    setSelectedEvents((prev) =>
      prev.includes(ev) ? prev.filter((e) => e !== ev) : [...prev, ev]
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Webhooks</h1>
          <p className="text-gray-400 text-sm mt-1">Push notifications to external systems on job events</p>
        </div>
        {canOperate && (
          <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Register Webhook
          </button>
        )}
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4">Register Webhook Endpoint</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Name *</label>
                <input name="name" required className="input" placeholder="Slack Notifications" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">URL *</label>
                <input name="url" type="url" required className="input" placeholder="https://hooks.example.com/..." />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Signing Secret (optional)</label>
                <input name="secret" className="input" placeholder="HMAC signing secret" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-2">Events</label>
                <div className="flex flex-wrap gap-2">
                  {EVENTS.map((ev) => (
                    <button
                      key={ev}
                      type="button"
                      onClick={() => toggleEvent(ev)}
                      className={`text-xs px-2 py-1 rounded font-mono transition-colors ${
                        selectedEvents.includes(ev)
                          ? 'bg-brand-600 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      {ev}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
              <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Registering...' : 'Register Webhook'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Webhook cards */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center text-gray-500 py-8">Loading...</div>
        ) : webhooks.length === 0 ? (
          <div className="card text-center py-8">
            <Webhook className="w-10 h-10 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No webhooks configured</p>
            <p className="text-gray-500 text-sm mt-1">Register an endpoint to receive push notifications</p>
          </div>
        ) : (
          webhooks.map((hook: WebhookType) => <WebhookCard key={hook.id} hook={hook} />)
        )}
      </div>
    </div>
  )
}
