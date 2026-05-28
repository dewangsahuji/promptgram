import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { CloudUpload, CheckCircle, ImagePlus, X } from 'lucide-react'
import { createPrompt, uploadImage } from '../api/prompts'
import { useAuth } from '../context/AuthContext'

const MODELS = ['GPT-4o', 'Claude 3.5 Sonnet', 'Gemini 1.5 Pro', 'Llama 3.1', 'Other']

export default function UploadPage() {
  const { isAuth } = useAuth()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [form, setForm] = useState({ title: '', prompt_text: '', model_used: MODELS[0], tags: '' })
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [drag, setDrag] = useState(false)
  const [progress, setProgress] = useState(0)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  if (!isAuth) { navigate('/login'); return null }

  const handleFile = (f) => {
    if (!f) return
    if (f.size > 10 * 1024 * 1024) { setError('File too large. Max 10 MB.'); return }
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setError('')
  }

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDrag(false)
    handleFile(e.dataTransfer?.files?.[0])
  }, [])

  const onFileChange = (e) => {
    handleFile(e.target.files?.[0])
    // Reset so same file can be re-selected
    e.target.value = ''
  }

  const removeImage = (e) => {
    e.stopPropagation()
    setFile(null)
    setPreview(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const tags = form.tags.split(',').map(t => t.trim()).filter(Boolean)
      const prompt = await createPrompt({ ...form, tags })
      if (file) await uploadImage(prompt.id, file, setProgress)
      setSuccess(true)
      setTimeout(() => navigate(`/prompt/${prompt.id}`), 1200)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally { setLoading(false) }
  }

  return (
    <div className="upload-page">
      <div className="upload-card">
        <div className="upload-card-crown" />
        <div className="upload-card-body">
          <h2>✦ Share a Prompt</h2>

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={onFileChange}
          />

          {/* Dropzone */}
          <div
            className={`dropzone${drag ? ' drag-active' : ''}`}
            onDragOver={e => { e.preventDefault(); setDrag(true) }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
          >
            {preview ? (
              <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
                <img src={preview} className="dropzone-preview" alt="preview" />
                <button
                  type="button"
                  onClick={removeImage}
                  style={{
                    position: 'absolute', top: 8, right: 8,
                    background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%',
                    width: 28, height: 28, display: 'flex', alignItems: 'center',
                    justifyContent: 'center', cursor: 'pointer', color: 'white',
                  }}
                >
                  <X size={14} />
                </button>
              </div>
            ) : (
              <>
                <div className="dropzone-icon"><ImagePlus size={40} color="var(--cyan)" /></div>
                <div className="dropzone-text">Drag & drop your image here</div>
                <div className="dropzone-hint">PNG, JPG, WebP · max 10 MB</div>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    marginTop: 12,
                    padding: '8px 20px',
                    background: 'linear-gradient(135deg, var(--cyan), #0891b2)',
                    border: 'none',
                    borderRadius: 8,
                    color: 'white',
                    fontWeight: 700,
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-base)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <CloudUpload size={15} /> Choose Image
                </button>
              </>
            )}
          </div>

          {/* If image selected, also show a "Change Image" link */}
          {preview && (
            <div style={{ textAlign: 'center', marginBottom: 12 }}>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                style={{ fontSize: '0.75rem', color: 'var(--cyan)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-base)' }}
              >
                Change image
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Prompt title</label>
              <input className="form-input" placeholder="A cyberpunk city at dusk…"
                value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))} required />
            </div>

            <div className="form-group">
              <label>Prompt text</label>
              <textarea className="form-input" rows={5}
                placeholder="Write the full prompt you used to generate this image…"
                style={{ resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
                value={form.prompt_text}
                onChange={e => setForm(f => ({...f, prompt_text: e.target.value}))} required />
            </div>

            <div className="form-group">
              <label>AI Model</label>
              <select className="form-input" value={form.model_used}
                onChange={e => setForm(f => ({...f, model_used: e.target.value}))}>
                {MODELS.map(m => <option key={m}>{m}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>Tags <span style={{color:'var(--text-muted)',fontWeight:400}}>(comma separated)</span></label>
              <input className="form-input" placeholder="fantasy, landscape, night"
                value={form.tags} onChange={e => setForm(f => ({...f, tags: e.target.value}))} />
            </div>

            {progress > 0 && progress < 100 && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ height: 4, background: 'rgba(6,182,212,0.15)', borderRadius: 2 }}>
                  <div style={{ height: '100%', width: `${progress}%`, background: 'var(--cyan)', borderRadius: 2, transition: 'width 0.3s' }} />
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>Uploading… {progress}%</div>
              </div>
            )}

            {error && <div className="form-error" style={{ marginBottom: 10 }}>{error}</div>}

            {success
              ? <div style={{ display:'flex', alignItems:'center', gap:8, color:'var(--cyan)', fontWeight:700 }}>
                  <CheckCircle size={18} /> Published! Redirecting…
                </div>
              : <button className="btn-primary" type="submit" disabled={loading}>
                  {loading ? 'Publishing…' : '✦ Publish Prompt'}
                </button>
            }
          </form>
        </div>
      </div>
    </div>
  )
}
