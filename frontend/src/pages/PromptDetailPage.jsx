import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Heart, Eye, Download, ArrowLeft, Copy, Bookmark, MessageCircle, Zap, Check } from 'lucide-react'
import { getPrompt, getImages } from '../api/prompts'
import { toggleLike, getComments, addComment } from '../api/social'
import { useAuth } from '../context/AuthContext'

const MODEL_LABELS = { claude: 'Claude', gpt: 'GPT-4o', gemini: 'Gemini', llama: 'Llama' }
const MODEL_BADGE  = { claude: 'badge-claude', gpt: 'badge-gpt', gemini: 'badge-gemini', llama: 'badge-llama' }
const AVATAR_GRADS = [
  'linear-gradient(135deg,#06B6D4,#0284C7)',
  'linear-gradient(135deg,#0a2250,#0284C7)',
  'linear-gradient(135deg,#B8860B,#F5D76E)',
  'linear-gradient(135deg,#8b5cf6,#4c1d95)',
]

function getModelKey(m) {
  if (!m) return null
  const l = m.toLowerCase()
  if (l.includes('claude')) return 'claude'
  if (l.includes('gpt') || l.includes('openai')) return 'gpt'
  if (l.includes('gemini')) return 'gemini'
  if (l.includes('llama')) return 'llama'
  return null
}

function getTimeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = (Date.now() - new Date(dateStr)) / 1000
  if (diff < 60)    return 'just now'
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function PromptDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAuth } = useAuth()
  const [prompt, setPrompt] = useState(null)
  const [images, setImages] = useState([])
  const [comments, setComments] = useState([])
  const [liked, setLiked] = useState(false)
  const [commentText, setCommentText] = useState('')
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [imgError, setImgError] = useState(false)

  useEffect(() => {
    Promise.all([
      getPrompt(id),
      getImages(id).catch(() => []),
      getComments(id).catch(() => []),
    ]).then(([p, imgs, cmts]) => {
      setPrompt(p)
      setImages(Array.isArray(imgs) ? imgs : [])
      setComments(Array.isArray(cmts) ? cmts : [])
    }).finally(() => setLoading(false))
  }, [id])

  const handleLike = async () => {
    if (!isAuth) { navigate('/login'); return }
    setLiked(l => !l)
    try { await toggleLike(id) } catch { setLiked(l => !l) }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(prompt?.prompt_text || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleComment = async (e) => {
    e.preventDefault()
    if (!commentText.trim() || !isAuth) return
    try {
      const c = await addComment(id, commentText.trim())
      setComments(cs => [...cs, c])
      setCommentText('')
    } catch {}
  }

  if (loading) return (
    <div className="detail-page">
      <div className="loading-state"><div className="spinner" /><span>Loading…</span></div>
    </div>
  )
  if (!prompt) return (
    <div className="detail-page">
      <div className="empty-state">Prompt not found.</div>
    </div>
  )

  const mk = getModelKey(prompt.model_used)
  const image = images[0]
  const imageUrl = image?.thumbnail_url || image?.s3_url || prompt.thumbnail_url
  const username = prompt.username || 'Anonymous'
  const initials = username.slice(0, 2).toUpperCase()
  const avatarGrad = AVATAR_GRADS[(initials.charCodeAt(0) || 65) % AVATAR_GRADS.length]
  const likeCount = (prompt.likes_count ?? 0) + (liked ? 1 : 0)

  return (
    <div className="detail-page">
      {/* Back button */}
      <button className="detail-back-btn" onClick={() => navigate(-1)}>
        <ArrowLeft size={14} /> Back
      </button>

      <div className="detail-card">
        <div className="card-crown" />

        {/* Hero image */}
        {imageUrl && !imgError ? (
          <div className="detail-hero">
            <img
              src={imageUrl}
              alt={prompt.title}
              className="detail-hero-img"
              onError={() => setImgError(true)}
            />
          </div>
        ) : (
          <div className="detail-hero-placeholder">
            <Zap size={48} />
          </div>
        )}

        <div className="detail-body">
          {/* Author row */}
          <div className="detail-author-row">
            <div className="detail-avatar" style={{ background: avatarGrad }}>
              {initials}
            </div>
            <div>
              <p className="detail-username">{username}</p>
              <p className="detail-time">{getTimeAgo(prompt.created_at)}</p>
            </div>
            {mk && (
              <span className={`model-badge ${MODEL_BADGE[mk]}`} style={{ marginLeft: 'auto' }}>
                {MODEL_LABELS[mk]}
              </span>
            )}
          </div>

          {/* Title */}
          <h1 className="detail-title">{prompt.title}</h1>

          {/* Prompt text */}
          <div className="detail-prompt-block">
            <div className="detail-prompt-label">Prompt</div>
            <p className="detail-prompt-text">{prompt.prompt_text}</p>
          </div>

          {/* Tags */}
          {prompt.tags?.length > 0 && (
            <div className="hashtag-row" style={{ marginBottom: 16 }}>
              {prompt.tags.map(t => (
                <span key={t} className="hashtag">#{t}</span>
              ))}
            </div>
          )}

          {/* Stats + Actions */}
          <div className="detail-actions">
            <button className={`detail-action-btn${liked ? ' liked' : ''}`} onClick={handleLike}>
              <Heart size={15} fill={liked ? '#e24b4a' : 'none'} />
              <span>{likeCount}</span>
            </button>
            <button className="detail-action-btn">
              <Eye size={15} />
              <span>{prompt.views ?? 0}</span>
            </button>
            <button className="detail-action-btn">
              <Download size={15} />
              <span>{prompt.downloads ?? 0}</span>
            </button>
            <div style={{ flex: 1 }} />
            <button className={`detail-action-btn${copied ? ' copied' : ''}`} onClick={handleCopy}>
              {copied ? <Check size={15} /> : <Copy size={15} />}
              <span>{copied ? 'Copied!' : 'Copy Prompt'}</span>
            </button>
            <button className="detail-action-btn">
              <Bookmark size={15} />
            </button>
          </div>

          <div className="gold-divider" style={{ margin: '16px 0' }} />

          {/* Comments */}
          <div className="detail-comments">
            <div className="detail-comments-title">
              <MessageCircle size={14} />
              Comments ({comments.length})
            </div>

            <div className="comment-list">
              {comments.length === 0 ? (
                <p className="detail-no-comments">No comments yet. Be the first!</p>
              ) : (
                comments.map((c, i) => (
                  <div key={c.id || i} className="comment-item">
                    <div
                      className="comment-avatar"
                      style={{ background: AVATAR_GRADS[(c.username || 'U').charCodeAt(0) % AVATAR_GRADS.length] }}
                    >
                      {(c.username || 'U').slice(0, 2).toUpperCase()}
                    </div>
                    <div className="comment-body">
                      <div className="comment-author">@{c.username || 'anon'}</div>
                      <div className="comment-text">{c.body}</div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {isAuth ? (
              <form className="comment-form" onSubmit={handleComment}>
                <textarea
                  className="comment-input"
                  rows={2}
                  placeholder="Add a comment…"
                  value={commentText}
                  onChange={e => setCommentText(e.target.value)}
                />
                <button className="comment-send-btn" type="submit">Send</button>
              </form>
            ) : (
              <p className="detail-no-comments" style={{ marginTop: 8 }}>
                <button onClick={() => navigate('/login')} style={{ color: 'var(--cyan)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-base)', fontSize: 'inherit' }}>
                  Sign in
                </button> to leave a comment.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
