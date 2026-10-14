type Status = 'success' | 'failed' | 'running' | 'pending' | 'retrying' | 'cancelled' | 'active' | 'paused' | 'archived'

const BADGE_MAP: Record<Status, string> = {
  success: 'badge-success',
  active: 'badge-success',
  failed: 'badge-failed',
  running: 'badge-running',
  pending: 'badge-pending',
  retrying: 'badge-retrying',
  cancelled: 'badge-pending',
  paused: 'badge-retrying',
  archived: 'badge-pending',
}

export default function StatusBadge({ status }: { status: string }) {
  const cls = BADGE_MAP[status as Status] || 'badge-pending'
  return <span className={cls}>{status}</span>
}
