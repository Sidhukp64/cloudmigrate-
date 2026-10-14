import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Play, Trash2, Settings, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import toast from 'react-hot-toast'
import { jobsApi, SyncJob, JobRun } from '../api/jobs'
import StatusBadge from '../components/StatusBadge'
import { formatDistanceToNow } from 'date-fns'
import { useAuthStore } from '../store/authStore'

function formatBytes(b: number) {
  if (!b) return '0 B'
  const k = 1024, s = ['B','KB','MB','GB']
  const i = Math.floor(Math.log(b) / Math.log(k))
  return `${(b / Math.pow(k,i)).toFixed(1)} ${s[i]}`
}

function JobRow({ job }: { job: SyncJob }) {
  const [expanded, setExpanded] = useState(false)
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const canOperate = user?.role === 'admin' || user?.role === 'operator'

  const { data: runs = [] } = useQuery({
    queryKey: ['job-runs', job.id],
    queryFn: () => jobsApi.getRuns(job.id),
    enabled: expanded,
  })

  const triggerMutation = useMutation({
    mutationFn: () => jobsApi.trigger(job.id),
    onSuccess: () => {
      toast.success(`Job "${job.name}" triggered!`)
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: () => toast.error('Failed to trigger job'),
  })

  const deleteMutation = useMutation({
    mutationFn: () => jobsApi.delete(job.id),
    onSuccess: () => {
      toast.success('Job deleted')
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: () => toast.error('Failed to delete job'),
  })

  return (
    <>
      <tr className="hover:bg-gray-800/50 transition-colors">
        <td className="px-4 py-3">
          <div>
            <p className="font-medium text-white text-sm">{job.name}</p>
            {job.description && <p className="text-xs text-gray-500 mt-0.5">{job.description}</p>}
          </div>
        </td>
        <td className="px-4 py-3">
          <span className="text-xs font-mono bg-gray-800 px-2 py-1 rounded text-gray-300">
            {job.source_type} → {job.destination_type}
          </span>
        </td>
        <td className="px-4 py-3">
          <StatusBadge status={job.status} />
        </td>
        <td className="px-4 py-3">
          {job.last_run ? <StatusBadge status={job.last_run.status} /> : <span className="text-xs text-gray-500">—</span>}
        </td>
        <td className="px-4 py-3 text-xs text-gray-400">
          {job.last_run?.files_processed ?? '—'} files<br />
          {job.last_run ? formatBytes(job.last_run.bytes_transferred) : ''}
        </td>
        <td className="px-4 py-3 text-xs text-gray-400">
          {job.schedule_cron ? <code className="text-brand-300">{job.schedule_cron}</code> : 'Manual'}
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center gap-1">
            {canOperate && (
              <button
                onClick={() => triggerMutation.mutate()}
                disabled={triggerMutation.isPending}
                className="p-1.5 hover:bg-green-900/40 rounded text-green-400 transition-colors disabled:opacity-50"
                title="Run now"
              >
                <Play className="w-3.5 h-3.5" />
              </button>
            )}
            {user?.role === 'admin' && (
              <button
                onClick={() => { if (confirm('Delete this job?')) deleteMutation.mutate() }}
                className="p-1.5 hover:bg-red-900/40 rounded text-red-400 transition-colors"
                title="Delete"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1.5 hover:bg-gray-700 rounded text-gray-400 transition-colors"
              title="View runs"
            >
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
        </td>
      </tr>

      {/* Expanded runs */}
      {expanded && (
        <tr>
          <td colSpan={7} className="px-4 pb-3 bg-gray-900">
            <div className="border border-gray-800 rounded-lg overflow-hidden mt-1">
              <table className="w-full text-xs">
                <thead className="bg-gray-800">
                  <tr>
                    <th className="px-3 py-2 text-left text-gray-400">Status</th>
                    <th className="px-3 py-2 text-left text-gray-400">Attempt</th>
                    <th className="px-3 py-2 text-left text-gray-400">Files</th>
                    <th className="px-3 py-2 text-left text-gray-400">Size</th>
                    <th className="px-3 py-2 text-left text-gray-400">Duration</th>
                    <th className="px-3 py-2 text-left text-gray-400">Triggered</th>
                    <th className="px-3 py-2 text-left text-gray-400">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run: JobRun) => (
                    <tr key={run.id} className="border-t border-gray-800">
                      <td className="px-3 py-2"><StatusBadge status={run.status} /></td>
                      <td className="px-3 py-2 text-gray-400">#{run.attempt_number}</td>
                      <td className="px-3 py-2 text-gray-400">{run.files_processed}</td>
                      <td className="px-3 py-2 text-gray-400">{formatBytes(run.bytes_transferred)}</td>
                      <td className="px-3 py-2 text-gray-400">{run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '—'}</td>
                      <td className="px-3 py-2 text-gray-400">{run.triggered_by}</td>
                      <td className="px-3 py-2 text-gray-400">{formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}</td>
                    </tr>
                  ))}
                  {runs.length === 0 && (
                    <tr><td colSpan={7} className="px-3 py-4 text-center text-gray-500">No runs yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function JobsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const canOperate = user?.role === 'admin' || user?.role === 'operator'

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsApi.list(),
    refetchInterval: 15_000,
  })

  const createMutation = useMutation({
    mutationFn: jobsApi.create,
    onSuccess: () => {
      toast.success('Job created!')
      qc.invalidateQueries({ queryKey: ['jobs'] })
      setShowCreate(false)
    },
    onError: () => toast.error('Failed to create job'),
  })

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    createMutation.mutate({
      name: fd.get('name') as string,
      description: fd.get('description') as string,
      source_type: fd.get('source_type') as string,
      destination_type: 's3',
      source_config: { path: fd.get('source_path') },
      destination_config: { prefix: fd.get('dest_prefix') },
      transform: fd.get('transform') as string,
      schedule_cron: (fd.get('schedule_cron') as string) || undefined,
      max_retries: Number(fd.get('max_retries')),
      retry_delay_seconds: 60,
    })
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Sync Jobs</h1>
          <p className="text-gray-400 text-sm mt-1">{jobs.length} jobs configured</p>
        </div>
        {canOperate && (
          <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Job
          </button>
        )}
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4">Create Sync Job</h2>
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Job Name *</label>
              <input name="name" required className="input" placeholder="SFTP to S3 Daily" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Source Type</label>
              <select name="source_type" className="input">
                <option value="sftp">SFTP</option>
                <option value="postgresql">PostgreSQL</option>
                <option value="local_fs">Local Filesystem</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Source Path / Query</label>
              <input name="source_path" className="input" placeholder="/remote/uploads" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">S3 Destination Prefix</label>
              <input name="dest_prefix" className="input" placeholder="data/uploads/" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Transform</label>
              <select name="transform" className="input">
                <option value="none">None</option>
                <option value="csv_to_parquet">CSV → Parquet</option>
                <option value="json_normalize">JSON Normalize</option>
                <option value="pii_mask">PII Mask</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Schedule (cron)</label>
              <input name="schedule_cron" className="input" placeholder="0 2 * * * (2 AM daily)" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Max Retries</label>
              <input name="max_retries" type="number" defaultValue={3} className="input" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Description</label>
              <input name="description" className="input" placeholder="Optional description" />
            </div>
            <div className="col-span-2 flex gap-3 justify-end">
              <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
              <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Job'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Jobs table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-800 border-b border-gray-700">
            <tr>
              {['Job Name', 'Route', 'Status', 'Last Run', 'Transfer', 'Schedule', 'Actions'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : jobs.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No sync jobs yet. Create your first one!</td></tr>
            ) : (
              jobs.map((job: SyncJob) => <JobRow key={job.id} job={job} />)
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
