import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getTrending } from '../api/prompts'
import { useAuth } from '../context/AuthContext'

// Gold splashes using percentage positions (matching reference)
const SPLASH_DEFS = [
  { w: 110, h: 110, x: '10%',  y: '5%',  blur: 28, opacity: 0.22, color: 'rgba(212,160,23,1)'  },
  { w: 80,  h: 80,  x: '55%',  y: '12%', blur: 20, opacity: 0.16, color: 'rgba(245,215,110,1)' },
  { w: 140, h: 140, x: '-15%', y: '38%', blur: 35, opacity: 0.18, color: 'rgba(184,134,11,1)'  },
  { w: 60,  h: 60,  x: '70%',  y: '50%', blur: 16, opacity: 0.20, color: 'rgba(240,192,64,1)'  },
  { w: 100, h: 100, x: '30%',  y: '68%', blur: 30, opacity: 0.14, color: 'rgba(200,144,10,1)'  },
  { w: 70,  h: 70,  x: '80%',  y: '78%', blur: 18, opacity: 0.18, color: 'rgba(212,160,23,1)'  },
  { w: 50,  h: 50,  x: '5%',   y: '88%', blur: 14, opacity: 0.13, color: 'rgba(245,215,110,1)' },
]

const AVATAR_GRADIENTS = [
  'linear-gradient(135deg,#06B6D4,#0a2250)',
  'linear-gradient(135deg,#D4A017,#B8860B)',
  'linear-gradient(135deg,#0284C7,#4A6080)',
  'linear-gradient(135deg,#8b5cf6,#4c1d95)',
  'linear-gradient(135deg,#ec4899,#9f1239)',
]

const SUGGESTED_USERS = [
  { name: 'Amira Ahm.',  handle: 'amira_ahm',   prompts: 920 },
  { name: 'Luca Nero',   handle: 'luca_nero',    prompts: 614 },
  { name: 'Sara Jeon',   handle: 'sara_jeon',    prompts: 488 },
  { name: 'Dev Thakur',  handle: 'dev_thakur',   prompts: 342 },
  { name: 'Noor Levi',   handle: 'noor_levi',    prompts: 291 },
]

export default function RightPanel() {
  const [trending, setTrending] = useState([])
  const [followed, setFollowed] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    getTrending()
      .then(d => setTrending(Array.isArray(d) ? d.slice(0, 5) : []))
      .catch(() => {})
  }, [])

  return (
    <div className="pg-right" id="rightPanel">
      {/* Ambient gold splashes */}
      {SPLASH_DEFS.map((s, i) => (
        <div
          key={i}
          className="gold-splash"
          style={{
            position: 'absolute',
            width: s.w,
            height: s.h,
            left: s.x,
            top: s.y,
            borderRadius: '50%',
            pointerEvents: 'none',
            filter: `blur(${s.blur}px)`,
            opacity: s.opacity,
            background: `radial-gradient(circle, ${s.color} 0%, transparent 70%)`,
          }}
        />
      ))}

      {/* Content on top of splashes */}
      <div style={{ position: 'relative', zIndex: 1 }}>

        {/* Stats */}
        <div className="right-section-title">Your Stats</div>
        <div className="stat-grid">
          {[
            { num: '—', label: 'Prompts' },
            { num: '—', label: 'Likes' },
            { num: '—', label: 'Saved' },
            { num: '—', label: 'Followers' },
          ].map(s => (
            <div key={s.label} className="stat-box">
              <span className="stat-num">{s.num}</span>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="gold-divider" />

        {/* Trending Tags */}
        <div className="right-section-title" style={{ marginTop: 14 }}>Trending Tags</div>
        <div className="trend-list">
          {trending.length === 0
            ? [
                { rank: 1, name: '#chainofthought', sub: '4.2k posts' },
                { rank: 2, name: '#roleplay',       sub: '3.8k posts' },
                { rank: 3, name: '#writing',        sub: '2.9k posts' },
                { rank: 4, name: '#code',           sub: '2.1k posts' },
                { rank: 5, name: '#persona',        sub: '1.7k posts' },
              ].map(item => (
                <div key={item.rank} className="trend-item">
                  <span className="trend-rank">{item.rank}</span>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: 12, fontWeight: 500, color: '#0c1a3d' }}>{item.name}</p>
                    <p style={{ fontSize: 10, color: '#4A6080' }}>{item.sub}</p>
                  </div>
                </div>
              ))
            : trending.map((p, i) => (
                <div
                  key={p.id}
                  className="trend-item"
                  onClick={() => navigate(`/prompt/${p.id}`)}
                >
                  <span className="trend-rank">{i + 1}</span>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <p style={{ fontSize: 12, fontWeight: 500, color: '#0c1a3d', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.title}</p>
                    <p style={{ fontSize: 10, color: '#4A6080' }}>{p.views ?? 0} views</p>
                  </div>
                </div>
              ))
          }
        </div>

        <div className="gold-divider" />

        {/* Suggested Users */}
        <div className="right-section-title" style={{ marginTop: 14 }}>Suggested</div>
        <div className="suggest-list">
          {SUGGESTED_USERS.map((u, i) => (
            <div key={u.handle} className="suggest-item">
              <div
                className="s-av"
                style={{ background: AVATAR_GRADIENTS[i % AVATAR_GRADIENTS.length] }}
              >
                {u.name.slice(0, 2).toUpperCase()}
              </div>
              <div className="suggest-info" style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 11, fontWeight: 500, color: '#0c1a3d', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{u.name}</p>
                <p style={{ fontSize: 10, color: '#4A6080' }}>{u.prompts} prompts</p>
              </div>
              <button
                className={`follow-btn${followed[u.handle] ? ' following' : ''}`}
                onClick={() => setFollowed(f => ({ ...f, [u.handle]: !f[u.handle] }))}
              >
                {followed[u.handle] ? 'Following' : 'Follow'}
              </button>
            </div>
          ))}
        </div>

      </div>
    </div>
  )
}
