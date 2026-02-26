import { Wand2 } from 'lucide-react'

const PRESETS = [
  { label: '✂️ Trim first 30s', value: 'Trim the first 30 seconds' },
  { label: '🔇 Remove silence', value: 'Remove all silent gaps longer than 0.5 seconds' },
  { label: '⚡ 2× speed', value: 'Speed up the video to 2x' },
  { label: '🎯 Highlight reel', value: 'Create a 60-second highlight reel with the best moments' },
  { label: '📱 YouTube Short', value: 'Create a YouTube Short — vertical 9:16, 60 seconds max, strong hook' },
  { label: '🎵 Remove fillers', value: 'Remove all filler words (um, uh, like, you know) and awkward pauses' },
]

interface Props {
  instruction: string
  onChange: (v: string) => void
  platform: string
  onPlatformChange: (v: string) => void
  addSubtitles: boolean
  onSubtitlesChange: (v: boolean) => void
  platforms: Record<string, { label: string }>
  disabled?: boolean
}

export default function EditPanel({
  instruction,
  onChange,
  platform,
  onPlatformChange,
  addSubtitles,
  onSubtitlesChange,
  platforms,
  disabled,
}: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Quick presets */}
      <div>
        <Label>Quick presets</Label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
          {PRESETS.map((p) => (
            <button
              key={p.value}
              onClick={() => onChange(p.value)}
              disabled={disabled}
              style={{
                padding: '6px 12px',
                borderRadius: 20,
                fontSize: 12,
                background: instruction === p.value ? 'var(--accent)' : 'var(--bg-card)',
                color: instruction === p.value ? '#fff' : 'var(--text-secondary)',
                border: `1px solid ${instruction === p.value ? 'var(--accent)' : 'var(--border)'}`,
                transition: 'all 0.15s',
                cursor: disabled ? 'not-allowed' : 'pointer',
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Instruction textarea */}
      <div>
        <Label>Edit instruction</Label>
        <textarea
          value={instruction}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Describe what you want to do with the video…"
          disabled={disabled}
          rows={4}
          style={{
            width: '100%',
            marginTop: 8,
            padding: '10px 14px',
            background: 'var(--bg-card)',
            border: `1px solid ${instruction ? 'var(--border-active)' : 'var(--border)'}`,
            borderRadius: 'var(--radius)',
            color: 'var(--text-primary)',
            resize: 'vertical',
            fontSize: 14,
            transition: 'border-color 0.15s',
            opacity: disabled ? 0.6 : 1,
          }}
        />
      </div>

      {/* Platform + subtitles */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <Label>Target platform</Label>
          <select
            value={platform}
            onChange={(e) => onPlatformChange(e.target.value)}
            disabled={disabled}
            style={{
              width: '100%',
              marginTop: 8,
              padding: '9px 12px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              color: 'var(--text-primary)',
              fontSize: 14,
              cursor: disabled ? 'not-allowed' : 'pointer',
            }}
          >
            {Object.entries(platforms).map(([key, p]) => (
              <option key={key} value={key}>{p.label}</option>
            ))}
          </select>
        </div>

        <div style={{ marginTop: 32 }}>
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              cursor: disabled ? 'not-allowed' : 'pointer',
              userSelect: 'none',
              color: 'var(--text-secondary)',
              fontSize: 13,
            }}
          >
            <input
              type="checkbox"
              checked={addSubtitles}
              onChange={(e) => onSubtitlesChange(e.target.checked)}
              disabled={disabled}
              style={{ accentColor: 'var(--accent)', width: 16, height: 16 }}
            />
            <Wand2 size={14} />
            Auto subtitles
          </label>
        </div>
      </div>
    </div>
  )
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
      {children}
    </div>
  )
}
