import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeftRight,
  CheckCircle,
  XCircle,
  Activity,
  Database,
} from 'lucide-react'
import { jobsApi, SyncJob, JobRun } from '../api/jobs'
import { auditApi } from '../api/audit'
import StatsCard from '../components/StatsCard'
import StatusBadge from '../components/StatusBadge'
import { formatDistanceToNow } from 'date-fns'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export default function DashboardPage() {
  const { data: jobs = [] } = useQuery({ queryKey: ['jobs'], queryFn: () => jobsApi.list() })
  const { data: auditLogs = [] } = useQuery({
    queryKey: ['audit', 'recent'],
    queryFn: () => auditApi.list({ page_size: 10 }),
  })

  const activeJobs = jobs.filter((j: SyncJob) => j.status === 'active').length
  const successRuns = jobs.filter((j: SyncJob) => j.last_run?.status === 'success').length
  const failedRuns = jobs.filter((j: SyncJob) => j.last_run?.status === 'failed').length
  const totalBytes = jobs.reduce(
    (acc: number, j: SyncJob) => acc + (j.last_run?.bytes_transferred || 0),
    0
  )

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Real-time overview of your migration gateway</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatsCard label="Active Jobs" value={activeJobs} icon={ArrowLeftRight} color="blue" />
        <StatsCard label="Successful Runs" value={successRuns} icon={CheckCircle} color="green" />
        <StatsCard label="Failed Runs" value={failedRuns} icon={XCircle} color="red" />
        <StatsCard label="Data Transferred" value={formatBytes(totalBytes)} icon={Database} color="yellow" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recent Jobs */}
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <ArrowLeftRight className="w-4 h-4 text-brand-400" />
            Recent Sync Jobs
          </h2>
          <div className="space-y-3">
            {jobs.slice(0, 6).map((job: SyncJob) => (
              <div key={job.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                <div>
                  <p className="text-sm font-medium text-white">{job.name}</p>
                  <p className="text-xs text-gray-400">
                    {job.source_type.toUpperCase()} → {job.destination_type.toUpperCase()}
                  </p>
                </div>
                <div className="text-right">
                  {job.last_run ? (
                    <StatusBadge status={job.last_run.status} />
                  ) : (
                    <span className="text-xs text-gray-500">Never run</span>
                  )}
                </div>
              </div>
            ))}
            {jobs.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">No jobs configured yet</p>
            )}
          </div>
        </div>

        {/* Recent Audit Events */}
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-brand-400" />
            Recent Audit Events
          </h2>
          <div className="space-y-3">
            {auditLogs.slice(0, 8).map((log) => (
              <div key={log.id} className="flex items-start gap-3 py-2 border-b border-gray-800 last:border-0">
                <div className="w-2 h-2 rounded-full bg-brand-500 mt-1.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-mono text-gray-300">{log.action.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-gray-500 truncate">{log.actor_email || 'System'}</p>
                </div>
                <p className="text-xs text-gray-600 shrink-0">
                  {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                </p>
              </div>
            ))}
            {auditLogs.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">No audit events yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
