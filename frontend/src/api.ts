const BASE = import.meta.env.VITE_API_URL ?? ''

export interface PlatformPreset {
  label: string
  width: number
  height: number
  fps?: number
  description?: string
}

export interface Job {
  job_id: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  progress: number
  logs: string[]
  output_url: string | null
  error: string | null
  edit_explanation: string | null
  crew_output: string | null
}

export const api = {
  async platforms(): Promise<Record<string, PlatformPreset>> {
    const res = await fetch(`${BASE}/api/platforms`)
    if (!res.ok) throw new Error('Failed to load platforms')
    return res.json()
  },

  async submit(
    files: File[],
    instruction: string,
    platform: string,
    addSubtitles: boolean,
  ): Promise<{ job_id: string }> {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    form.append('instruction', instruction)
    form.append('platform', platform)
    form.append('add_subtitles', String(addSubtitles))

    const res = await fetch(`${BASE}/api/jobs`, { method: 'POST', body: form })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || `HTTP ${res.status}`)
    }
    return res.json()
  },

  async poll(jobId: string): Promise<Job> {
    const res = await fetch(`${BASE}/api/jobs/${jobId}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  downloadUrl(jobId: string): string {
    return `${BASE}/api/jobs/${jobId}/download`
  },
}
