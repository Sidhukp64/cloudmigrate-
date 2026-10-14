import { api } from './client'

export interface SyncJob {
  id: string
  name: string
  description?: string
  source_type: 'sftp' | 'postgresql' | 'local_fs'
  destination_type: 's3'
  source_config: Record<string, unknown>
  destination_config: Record<string, unknown>
  transform: 'none' | 'csv_to_parquet' | 'json_normalize' | 'pii_mask'
  schedule_cron?: string
  max_retries: number
  retry_delay_seconds: number
  status: 'active' | 'paused' | 'archived'
  created_at: string
  updated_at: string
  last_run?: JobRun
}

export interface JobRun {
  id: string
  job_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'retrying' | 'cancelled'
  attempt_number: number
  files_processed: number
  bytes_transferred: number
  error_message?: string
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  triggered_by: string
  created_at: string
}

export interface CreateJobPayload {
  name: string
  description?: string
  source_type: string
  destination_type: string
  source_config: Record<string, unknown>
  destination_config: Record<string, unknown>
  transform: string
  schedule_cron?: string
  max_retries: number
  retry_delay_seconds: number
}

export const jobsApi = {
  list: (params?: { status?: string }) =>
    api.get<SyncJob[]>('/jobs', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<SyncJob>(`/jobs/${id}`).then((r) => r.data),

  create: (payload: CreateJobPayload) =>
    api.post<SyncJob>('/jobs', payload).then((r) => r.data),

  update: (id: string, payload: Partial<CreateJobPayload>) =>
    api.put<SyncJob>(`/jobs/${id}`, payload).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/jobs/${id}`),

  trigger: (id: string) =>
    api.post<JobRun>(`/jobs/${id}/run`).then((r) => r.data),

  getRuns: (id: string) =>
    api.get<JobRun[]>(`/jobs/${id}/runs`).then((r) => r.data),
}
