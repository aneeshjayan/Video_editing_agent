import { useCallback, useRef, useState } from 'react'
import { Upload, Film, X } from 'lucide-react'

interface Props {
  files: File[]
  onChange: (files: File[]) => void
  disabled?: boolean
}

export default function VideoUpload({ files, onChange, disabled }: Props) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const accept = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska']

  const addFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming) return
      const valid = Array.from(incoming).filter((f) => accept.some((a) => f.type === a) || /\.(mp4|mov|avi|mkv)$/i.test(f.name))
      onChange([...files, ...valid])
    },
    [files, onChange],
  )

  const remove = (i: number) => {
    const next = files.filter((_, idx) => idx !== i)
    onChange(next)
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (!disabled) addFiles(e.dataTransfer.files)
  }

  const totalMb = files.reduce((s, f) => s + f.size / 1048576, 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Drop zone */}
      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        style={{
          border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
          borderRadius: 'var(--radius-lg)',
          background: dragging ? 'var(--accent-light)' : 'var(--bg-card)',
          padding: '32px 20px',
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s',
          boxShadow: dragging ? 'var(--shadow-glow)' : 'none',
          opacity: disabled ? 0.5 : 1,
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".mp4,.mov,.avi,.mkv"
          multiple
          style={{ display: 'none' }}
          onChange={(e) => addFiles(e.target.files)}
          disabled={disabled}
        />
        <Upload size={32} color="var(--accent)" style={{ marginBottom: 12 }} />
        <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>
          Drop videos here
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
          MP4, MOV, AVI, MKV · Multiple files supported
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {files.map((f, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                background: 'var(--bg-card)',
                borderRadius: 'var(--radius)',
                padding: '10px 12px',
                border: '1px solid var(--border)',
              }}
            >
              <Film size={16} color="var(--accent)" style={{ flexShrink: 0 }} />
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {f.name}
              </span>
              <span style={{ color: 'var(--text-muted)', fontSize: 12, flexShrink: 0 }}>
                {(f.size / 1048576).toFixed(1)} MB
              </span>
              {!disabled && (
                <button
                  onClick={(e) => { e.stopPropagation(); remove(i) }}
                  style={{ background: 'none', color: 'var(--text-muted)', padding: 2, lineHeight: 0 }}
                >
                  <X size={14} />
                </button>
              )}
            </div>
          ))}
          {files.length > 1 && (
            <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center' }}>
              {files.length} videos · {totalMb.toFixed(1)} MB total — will be merged before editing
            </div>
          )}
        </div>
      )}
    </div>
  )
}
