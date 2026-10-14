import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Shield, Search } from 'lucide-react'
import { auditApi, AuditLog } from '../api/audit'
import { api } from '../api/client'
import toast from 'react-hot-toast'
import { formatDistanceToNow, format } from 'date-fns'

const AUDIT_ACTIONS = [
  '', 'JOB_CREATED', 'JOB_UPDATED', 'JOB_DELETED',
  'JOB_RUN_STARTED', 'JOB_RUN_COMPLETED', 'JOB_RUN_FAILED',
  'FILE_UPLOADED', 'USER_LOGIN', 'USER_CREATED', 'WEBHOOK_FIRED', 'WEBHOOK_FAILED',
]

export default function AuditPage() {
  const [action, setAction] = useState('')
  const [actorEmail, setActorEmail] = useState('')
  const [page, setPage] = useState(1)

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['audit', action, actorEmail, page],
    queryFn: () => auditApi.list({
      action: action || undefined,
      actor_email: actorEmail || undefined,
      page,
      page_size: 50,
    }),
  })

  const handleExport = async () => {
    try {
      const res = await api.get('/audit/export', { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'audit_logs.csv'
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Audit logs exported')
    } catch {
      toast.error('Export failed')
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-brand-400" />
            Audit Logs
          </h1>
          <p className="text-gray-400 text-sm mt-1">Immutable audit trail with tamper detection</p>
        </div>
        <button onClick={handleExport} className="btn-secondary flex items-center gap-2">
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="card flex items-center gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              value={actorEmail}
              onChange={(e) => { setActorEmail(e.target.value); setPage(1) }}
              className="input pl-10"
              placeholder="Filter by actor email..."
            />
          </div>
        </div>
        <div>
          <select
            value={action}
            onChange={(e) => { setAction(e.target.value); setPage(1) }}
            className="input w-56"
          >
            {AUDIT_ACTIONS.map((a) => (
              <option key={a} value={a}>{a || 'All actions'}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-800 border-b border-gray-700">
            <tr>
              {['Timestamp', 'Action', 'Actor', 'Resource', 'IP Address', 'Integrity'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No audit logs found</td></tr>
            ) : (
              logs.map((log: AuditLog) => (
                <tr key={log.id} className="hover:bg-gray-800/30">
                  <td className="px-4 py-3">
                    <p className="text-xs text-white">{format(new Date(log.created_at), 'MMM d, HH:mm:ss')}</p>
                    <p className="text-xs text-gray-500">{formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs bg-gray-800 px-2 py-1 rounded text-brand-300">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-300">{log.actor_email || <span className="text-gray-600">system</span>}</td>
                  <td className="px-4 py-3 text-xs">
                    {log.resource_type && (
                      <><span className="text-gray-400">{log.resource_type}</span> <span className="text-gray-600 font-mono">{log.resource_id?.slice(0, 8)}...</span></>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">{log.ip_address || '—'}</td>
                  <td className="px-4 py-3">
                    {log.checksum ? (
                      <span className="text-green-400 text-xs flex items-center gap-1">
                        <Shield className="w-3 h-3" /> Signed
                      </span>
                    ) : (
                      <span className="text-gray-600 text-xs">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="btn-secondary disabled:opacity-30"
        >
          Previous
        </button>
        <span className="text-sm text-gray-400">Page {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={logs.length < 50}
          className="btn-secondary disabled:opacity-30"
        >
          Next
        </button>
      </div>
    </div>
  )
}
