import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import Sidebar from './components/Sidebar'
import RightPanel from './components/RightPanel'
import GoldLeaves from './components/GoldLeaves'
import ThemeToggle from './components/ThemeToggle'
import FeedPage from './pages/FeedPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import UploadPage from './pages/UploadPage'
import SearchPage from './pages/SearchPage'
import PromptDetailPage from './pages/PromptDetailPage'
import ProfilePage from './pages/ProfilePage'

// Auth/Signup are full-page — no sidebar/right panel layout
const FULL_PAGE_ROUTES = ['/login', '/signup']

function AppLayout({ children }) {
  return (
    <div className="pg-root">
      <Sidebar />
      {children}
      <RightPanel />
      <GoldLeaves />
      <ThemeToggle />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            {/* Full-page routes (no sidebar) */}
            <Route path="/login"  element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            {/* App layout routes */}
            <Route path="/" element={
              <AppLayout><FeedPage /></AppLayout>
            } />
            <Route path="/trending" element={
              <AppLayout><FeedPage /></AppLayout>
            } />
            <Route path="/upload" element={
              <AppLayout><UploadPage /></AppLayout>
            } />
            <Route path="/search" element={
              <AppLayout><SearchPage /></AppLayout>
            } />
            <Route path="/prompt/:id" element={
              <AppLayout><PromptDetailPage /></AppLayout>
            } />
            <Route path="/profile/:id" element={
              <AppLayout><ProfilePage /></AppLayout>
            } />
            <Route path="/me" element={
              <AppLayout><ProfilePage /></AppLayout>
            } />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
