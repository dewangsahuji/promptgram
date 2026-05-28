import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Heart, MessageCircle, Copy, Bookmark } from 'lucide-react'
import { toggleLike } from '../api/social'
import { useAuth } from '../context/AuthContext'

const MODEL_BADGE = {
  claude:  'badge-claude',
  gpt:     'badge-gpt',
  gemini:  'badge-gemini',
  llama:   'badge-llama',
}

const AVATAR_GRADIENTS = [
  'linear-gradient(135deg,#06B6D4,#0284C7)',
  'linear-gradient(135deg,#0a2250,#0284C7)',
  'linear-gradient(135deg,#B8860B,#F5D76E)',
  'linear-gradient(135deg,#4A6080,#0c1a3d)',
  'linear-gradient(135deg,#8b5cf6,#4c1d95)',
]

function getModelKey(modelUsed) {
  if (!modelUsed) return null
  const m = modelUsed.toLowerCase()
  if (m.includes('claude')) return 'claude'
  if (m.includes('gpt') || m.includes('openai')) return 'gpt'
  if (m.includes('gemini')) return 'gemini'
  if (m.includes('llama')) return 'llama'
  return null
}

function getTimeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = (Date.now() - new Date(dateStr)) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function PromptCard({ prompt }) {
  const navigate = useNavigate()
  const { isAuth } = useAuth()
  const [liked, setLiked] = useState(false)
  const [likeCount, setLikeCount] = useState(prompt.likes_count ?? 0)
  const [copied, setCopied] = useState(false)

  const modelKey = getModelKey(prompt.model_used)
  const badgeClass = modelKey ? MODEL_BADGE[modelKey] : 'badge-default'
  const modelLabel = modelKey
    ? { claude: 'Claude', gpt: 'GPT-4o', gemini: 'Gemini', llama: 'Llama' }[modelKey]
    : (prompt.model_used || 'AI')

  const handleLike = async (e) => {
    e.stopPropagation()
    if (!isAuth) { navigate('/login'); return }
    setLiked(l => !l)
    setLikeCount(c => liked ? c - 1 : c + 1)
    try { await toggleLike(prompt.id) } catch {
      setLiked(l => !l)
      setLikeCount(c => liked ? c + 1 : c - 1)
    }
  }

  const handleCopy = (e) => {
    e.stopPropagation()
    navigator.clipboard.writeText(prompt.prompt_text || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const username = prompt.username || 'Anonymous'
  const initials = username.slice(0, 2).toUpperCase()
  const avatarGrad = AVATAR_GRADIENTS[(initials.charCodeAt(0) || 65) % AVATAR_GRADIENTS.length]
  const timeAgo = getTimeAgo(prompt.created_at)
  const imageUrl = prompt.images?.[0]?.thumbnail_url || prompt.images?.[0]?.s3_url || prompt.thumbnail_url

  return (
    <div className="pg-card" onClick={() => navigate(`/prompt/${prompt.id}`)}>
      <div className="card-crown" />

      {/* Thumbnail image — shown when available */}
      {imageUrl && (
        <div className="card-image-wrap">
          <img
            src={imageUrl}
            alt={prompt.title}
            className="card-thumb"
            loading="lazy"
            onError={e => { e.target.style.display = 'none'; e.target.parentNode.style.display = 'none' }}
          />
        </div>
      )}

      <div className="card-body">
        {/* Card head: avatar + author + model badge */}
        <div className="card-head">
          <div className="card-avatar" style={{ background: avatarGrad }}>
            {initials}
          </div>
          <div className="card-author">
            <p>{username}</p>
            <p>@{username.toLowerCase().replace(/\s+/g, '_')}{timeAgo ? ` · ${timeAgo}` : ''}</p>
          </div>
          <span className={`model-badge ${badgeClass}`}>{modelLabel}</span>
        </div>

        {/* Prompt text block */}
        <div className="prompt-block">{prompt.prompt_text}</div>

        {/* Tags */}
        {prompt.tags?.length > 0 && (
          <div className="hashtag-row">
            {prompt.tags.slice(0, 4).map(t => (
              <span key={t} className="hashtag" onClick={e => e.stopPropagation()}>#{t}</span>
            ))}
          </div>
        )}

        {/* Action bar */}
        <div className="card-actions" onClick={e => e.stopPropagation()}>
          <button
            className={`action-btn${liked ? ' liked' : ''}`}
            onClick={handleLike}
            title={liked ? 'Unlike' : 'Like'}
          >
            <Heart size={13} fill={liked ? '#e24b4a' : 'none'} />
            <span>{likeCount}</span>
          </button>

          <button
            className="action-btn"
            onClick={e => { e.stopPropagation(); navigate(`/prompt/${prompt.id}`) }}
            title="Comment"
          >
            <MessageCircle size={13} />
            <span>{prompt.comments_count ?? 0}</span>
          </button>

          <div className="spacer" />

          <button
            className={`action-btn${copied ? ' liked' : ''}`}
            onClick={handleCopy}
            title={copied ? 'Copied!' : 'Copy prompt'}
          >
            <Copy size={13} />
            {copied && <span>Copied!</span>}
          </button>

          <button className="action-btn" onClick={e => e.stopPropagation()} title="Save">
            <Bookmark size={13} />
          </button>
        </div>
      </div>
    </div>
  )
}
