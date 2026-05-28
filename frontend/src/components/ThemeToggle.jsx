import { useTheme } from '../context/ThemeContext'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return (
    <button className="theme-toggle" onClick={toggle} title="Toggle dark/light mode">
      {theme === 'dark'
        ? <><Sun size={13} /> Light</>
        : <><Moon size={13} /> Dark</>
      }
    </button>
  )
}
