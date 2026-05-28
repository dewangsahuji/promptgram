import { useState } from 'react'
import { Search, Sparkles, ImageOff } from 'lucide-react'
import { searchPrompts } from '../api/prompts'
import PromptCard from '../components/PromptCard'

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
      const data = await searchPrompts(query.trim(), 1, 20)
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
          placeholder="🔍  Search by prompts, tags, or titles…"
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
            <Search size={40} style={{ color:'var(--cyan)' }} />
            <span style={{ fontSize:'0.9rem', fontWeight:600 }}>Text Search</span>
            <span style={{ fontSize:'0.78rem', color:'var(--text-muted)', textAlign:'center', maxWidth:300 }}>
              Find prompts by searching their text, tags, or titles
            </span>
          </div>
        </>
      )}

      {loading && <div className="loading-state"><div className="spinner" /><span>Searching…</span></div>}

      {searched && !loading && results.length === 0 && (
        <div className="empty-state">
          <ImageOff size={32} style={{ color:'var(--text-muted)' }} />
          <span>No results found for your query.</span>
        </div>
      )}

      {!loading && results.length > 0 && (
        <>
          <div style={{ fontSize:'0.78rem', color:'var(--text-muted)', marginBottom:16 }}>
            {results.length} results for <strong style={{ color:'var(--cyan)' }}>"{query}"</strong>
          </div>
          <div className="prompt-grid">
            {results.map(r => (
              <PromptCard key={r.id} prompt={r} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
