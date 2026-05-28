import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  Home, TrendingUp, Upload, Search,
  User, LogOut, LogIn, Sparkles,
  Bookmark, Bell, Trophy, Settings
} from 'lucide-react'

const NAV = [
  { icon: Home,       label: 'Feed',     path: '/' },
  { icon: TrendingUp, label: 'Trending', path: '/trending' },
  { icon: Search,     label: 'Search',   path: '/search' },
  { icon: Upload,     label: 'Upload',   path: '/upload' },
  { icon: User,       label: 'Profile',  path: '/me' },
]

const AVATAR_COLORS = [
  'linear-gradient(135deg,#06b6d4,#0c1a3d)',
  'linear-gradient(135deg,#D4A017,#0c1a3d)',
  'linear-gradient(135deg,#8b5cf6,#1d4ed8)',
  'linear-gradient(135deg,#ec4899,#7c3aed)',
]

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout, isAuth } = useAuth()

  const initials = user?.username
    ? user.username.slice(0,2).toUpperCase()
    : 'PG'

  const avatarColor = AVATAR_COLORS[
    (initials.charCodeAt(0) || 0) % AVATAR_COLORS.length
  ]

  const handleLogout = async () => {
    try {
      const { logout: apiLogout } = await import('../api/auth')
      await apiLogout()
    } catch {}
    logout()
    navigate('/login')
  }

  return (
    <div className="pg-sidebar">
      {/* Absolute background glass layer */}
      <div className="sidebar-glass" />

      {/* Content layer sits on top */}
      <div className="sidebar-content">
        {/* Logo */}
        <div className="pg-logo">
          <span className="pg-logo-text">✦ Promptgram</span>
        </div>

        {/* Navigation */}
        <nav className="pg-nav">
          {NAV.map(({ icon: Icon, label, path }) => {
            const active = location.pathname === path ||
              (path !== '/' && location.pathname.startsWith(path))
            return (
              <button
                key={path}
                className={`pg-nav-item${active ? ' active' : ''}`}
                onClick={() => navigate(path)}
              >
                <Icon size={15} />
                <span>{label}</span>
              </button>
            )
          })}
        </nav>

        {/* AI badge */}
        <div className="sidebar-ai-badge">
          <div className="sidebar-ai-badge-title">
            <Sparkles size={11} />
            <span>AI-Powered Search</span>
          </div>
          <div className="sidebar-ai-badge-sub">
            CLIP · Qdrant · NudeNet
          </div>
        </div>

        {/* User area */}
        <div className="pg-user">
          {isAuth ? (
            <>
              <div className="pg-avatar-grad" style={{ background: avatarColor }}>
                {initials}
              </div>
              <div className="pg-user-info">
                <p>{user?.username || 'You'}</p>
                <p>@{user?.username || 'user'}</p>
              </div>
              <button
                className="pg-logout-btn"
                onClick={handleLogout}
                title="Log out"
              >
                <LogOut size={14} />
              </button>
            </>
          ) : (
            <button
              className="pg-nav-item"
              onClick={() => navigate('/login')}
              style={{ width: '100%' }}
            >
              <LogIn size={14} />
              <span>Sign in</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
