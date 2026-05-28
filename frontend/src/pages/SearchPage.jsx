import { useState } from 'react'
import { Search, Sparkles, ImageOff } from 'lucide-react'
import { semanticSearch } from '../api/prompts'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searched, setSearched] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true); setSearched(true)
    try {
      const data = await semanticSearch(query.trim(), 20)
      setResults(Array.isArray(data) ? data : [])
    } catch { setResults([]) }
    finally { setLoading(false) }
  }

  const SUGGESTIONS = ['cyberpunk cityscape','ethereal fantasy forest','neon portrait','space nebula','anime warrior']

  return (
    <div className="search-page">
      <form className="search-bar-wrap" onSubmit={handleSearch}>
        <input
          className="search-input"
          placeholder="🔍  Describe what you're looking for… (AI-powered semantic search)"
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <button className="search-btn" type="submit" disabled={loading}>
          {loading ? '…' : <Search size={15} />}
        </button>
      </form>

      {!searched && (
        <>
          <div className="search-tag">Try searching for:</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:8, marginBottom:24 }}>
            {SUGGESTIONS.map(s => (
              <button
                key={s}
                className="tag"
                style={{ cursor:'pointer', padding:'6px 14px', fontSize:'0.8rem' }}
                onClick={() => { setQuery(s); }}
              >
                {s}
              </button>
            ))}
          </div>
          <div className="empty-state">
            <Sparkles size={40} style={{ color:'var(--cyan)' }} />
            <span style={{ fontSize:'0.9rem', fontWeight:600 }}>AI Semantic Search</span>
            <span style={{ fontSize:'0.78rem', color:'var(--text-muted)', textAlign:'center', maxWidth:300 }}>
              Uses CLIP ViT-B/32 to understand the meaning of your query and find visually similar images
            </span>
          </div>
        </>
      )}

      {loading && <div className="loading-state"><div className="spinner" /><span>Searching with CLIP…</span></div>}

      {searched && !loading && results.length === 0 && (
        <div className="empty-state">
          <ImageOff size={32} style={{ color:'var(--text-muted)' }} />
          <span>No results — try uploading some images first so AI can index them</span>
        </div>
      )}

      {!loading && results.length > 0 && (
        <>
          <div style={{ fontSize:'0.78rem', color:'var(--text-muted)', marginBottom:16 }}>
            {results.length} results for <strong style={{ color:'var(--cyan)' }}>"{query}"</strong>
          </div>
          <div className="prompt-grid">
            {results.map(r => (
              <div key={r.image_id} className="pg-card" style={{ padding:14 }}>
                <div className="card-crown" />
                <div style={{ padding:'10px 14px' }}>
                  <div style={{ fontSize:'0.78rem', color:'var(--text-muted)', fontFamily:'var(--font-mono)' }}>
                    Image ID: {r.image_id?.slice(0,8)}…
                  </div>
                  <div style={{ display:'flex', alignItems:'center', gap:6, marginTop:6 }}>
                    <div style={{ height:6, flex:1, background:'rgba(6,182,212,0.1)', borderRadius:3 }}>
                      <div style={{ height:'100%', width:`${(r.score*100).toFixed(0)}%`, background:'var(--cyan)', borderRadius:3 }} />
                    </div>
                    <span style={{ fontSize:'0.72rem', color:'var(--cyan)', fontWeight:700 }}>
                      {(r.score*100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
