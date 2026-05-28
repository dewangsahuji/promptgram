import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import PromptCard from '../components/PromptCard'
import { getUserPrompts } from '../api/social'
import { getUserById } from '../api/auth'
import { toggleFollow } from '../api/social'
import { useAuth } from '../context/AuthContext'

const AVATAR_GRADIENTS = [
  'linear-gradient(135deg,#06b6d4,#0a1837)',
  'linear-gradient(135deg,#D4A017,#f59e0b)',
  'linear-gradient(135deg,#8b5cf6,#4c1d95)',
  'linear-gradient(135deg,#ec4899,#9f1239)',
]

export default function ProfilePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user: me, isAuth } = useAuth()
  const [profile, setProfile] = useState(null)
  const [prompts, setPrompts] = useState([])
  const [following, setFollowing] = useState(false)
  const [loading, setLoading] = useState(true)

  const userId = id || me?.id

  useEffect(() => {
    if (!userId) { navigate('/login'); return }
    Promise.all([
      getUserById(userId).catch(() => null),
      getUserPrompts(userId).catch(() => [])
    ]).then(([u, ps]) => {
      setProfile(u)
      setPrompts(Array.isArray(ps) ? ps : [])
    }).finally(() => setLoading(false))
  }, [userId])

  const handleFollow = async () => {
    if (!isAuth) { navigate('/login'); return }
    setFollowing(f => !f)
    try { await toggleFollow(userId) } catch { setFollowing(f => !f) }
  }

  if (loading) return <div className="profile-page"><div className="loading-state"><div className="spinner" /></div></div>

  const username = profile?.username || 'User'
  const initials = username.slice(0,2).toUpperCase()
  const avatarGrad = AVATAR_GRADIENTS[(initials.charCodeAt(0)||0) % AVATAR_GRADIENTS.length]
  const isMe = me?.id === userId

  return (
    <div className="profile-page">
      <div className="profile-header">
        <div className="profile-banner" />
        <div className="profile-info">
          <div className="profile-avatar" style={{ background: avatarGrad }}>{initials}</div>
          <div className="profile-meta">
            <div className="profile-name">{username}</div>
            <div className="profile-handle">@{profile?.email?.split('@')[0] || username.toLowerCase()}</div>
            <div className="profile-stats">
              <div className="pstat"><div className="pstat-num">{prompts.length}</div><div className="pstat-label">Prompts</div></div>
              <div className="pstat"><div className="pstat-num">—</div><div className="pstat-label">Followers</div></div>
              <div className="pstat"><div className="pstat-num">—</div><div className="pstat-label">Following</div></div>
            </div>
          </div>
          {!isMe && (
            <button
              className={`follow-btn${following ? ' following' : ''}`}
              style={{ padding:'8px 20px', fontSize:'0.82rem', alignSelf:'center' }}
              onClick={handleFollow}
            >
              {following ? '✓ Following' : '+ Follow'}
            </button>
          )}
        </div>
      </div>

      {prompts.length === 0
        ? <div className="empty-state" style={{ marginTop:40 }}>No prompts yet</div>
        : (
          <div className="prompt-grid">
            {prompts.map(p => <PromptCard key={p.id} prompt={p} image={null} />)}
          </div>
        )
      }
    </div>
  )
}
