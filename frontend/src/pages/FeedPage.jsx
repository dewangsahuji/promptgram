import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import PromptCard from '../components/PromptCard'
import { listPrompts, getTrending } from '../api/prompts'
import { Sparkles, Plus } from 'lucide-react'

function FeedBackground() {
  return (
    <div className="pg-feed-bg">
      <div className="orb orb1" />
      <div className="orb orb2" />
      <div className="orb orb3" />
      {[...Array(6)].map((_, i) => (
        <div
          key={i}
          className="dust"
          style={{
            left: `${15 + i * 14}%`,
            top: `${75 + (i % 3) * 7}%`,
            animationDuration: `${6 + i * 1.1}s`,
            animationDelay: `${i * 1.2}s`,
          }}
        />
      ))}
    </div>
  )
}

const TABS = [
  { key: 'recent',   label: 'Recent' },
  { key: 'trending', label: 'Trending' },
]

export default function FeedPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState('recent')   // default to recent so data shows immediately
  const [prompts, setPrompts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const req = tab === 'trending' ? getTrending() : listPrompts(1, 30)
    req
      .then(d => setPrompts(Array.isArray(d) ? d : []))
      .catch(() => setPrompts([]))
      .finally(() => setLoading(false))
  }, [tab])

  return (
    <div className="pg-feed">
      <FeedBackground />
      <div className="pg-feed-inner">
        <div className="feed-header">
          <h2>{tab === 'trending' ? 'Trending' : 'Recent'}</h2>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {TABS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                style={{
                  padding: '5px 12px',
                  borderRadius: 20,
                  border: 'none',
                  fontSize: 11,
                  fontWeight: 500,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-base)',
                  transition: 'all 0.2s',
                  background: tab === key ? 'rgba(6,182,212,0.12)' : 'transparent',
                  color: tab === key ? '#06B6D4' : '#4A6080',
                  boxShadow: tab === key ? '0 0 0 1px rgba(6,182,212,0.25)' : 'none',
                }}
              >
                {label}
              </button>
            ))}
            <button className="pg-share-btn" onClick={() => navigate('/upload')}>
              <Plus size={13} />
              Share
            </button>
          </div>
        </div>

        {loading && (
          <div className="loading-state">
            <div className="spinner" />
            <span>Loading prompts…</span>
          </div>
        )}

        {!loading && prompts.length === 0 && (
          <div className="empty-state">
            <Sparkles size={32} style={{ color: '#06B6D4' }} />
            <p>No prompts yet — be the first to share one!</p>
            <button className="pg-share-btn" style={{ marginTop: 12 }} onClick={() => navigate('/upload')}>
              <Plus size={13} /> Share a Prompt
            </button>
          </div>
        )}

        {!loading && prompts.length > 0 && (
          <div className="prompt-grid">
            {prompts.map(p => (
              <PromptCard key={p.id} prompt={p} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
