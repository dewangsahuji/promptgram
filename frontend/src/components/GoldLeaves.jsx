import { useEffect, useRef } from 'react'
import { useTheme } from '../context/ThemeContext'

const LEAF_SHAPES = [
  'M0,10 C2,4 8,0 12,5 C16,10 12,20 6,18 C0,16 -2,16 0,10 Z',
  'M6,0 C10,2 14,8 12,14 C10,20 2,20 0,14 C-2,8 2,-2 6,0 Z',
  'M0,6 C4,-2 14,0 14,8 C14,16 8,18 4,14 C0,10 -4,14 0,6 Z',
]
const GOLD_SHADES = [
  '#F5D76E','#D4A017','#B8860B','#E6C84A','#C9960E','#F0CC50',
]
const NS = 'http://www.w3.org/2000/svg'

export default function GoldLeaves() {
  const containerRef = useRef(null)
  const { theme } = useTheme()

  useEffect(() => {
    // Only show leaves in dark mode
    if (theme === 'light') return
    const container = containerRef.current
    if (!container) return

    const leaves = []

    for (let i = 0; i < 22; i++) {
      // Create SVG element
      const svg = document.createElementNS(NS, 'svg')
      const w = 14 + Math.random() * 10
      const h = w * 1.4
      svg.setAttribute('width', w)
      svg.setAttribute('height', h)
      svg.setAttribute('viewBox', '0 0 14 20')
      svg.style.position = 'absolute'
      svg.classList.add('gold-leaf')

      // Unique blur filter
      const filterId = `leaf-blur-${i}`
      const defs = document.createElementNS(NS, 'defs')
      const filter = document.createElementNS(NS, 'filter')
      filter.setAttribute('id', filterId)
      const blur = document.createElementNS(NS, 'feGaussianBlur')
      blur.setAttribute('stdDeviation', (0.3 + Math.random() * 1.4).toFixed(2))
      filter.appendChild(blur)
      defs.appendChild(filter)
      svg.appendChild(defs)

      // Leaf path
      const path = document.createElementNS(NS, 'path')
      path.setAttribute('d', LEAF_SHAPES[Math.floor(Math.random() * LEAF_SHAPES.length)])
      path.setAttribute('fill', GOLD_SHADES[Math.floor(Math.random() * GOLD_SHADES.length)])
      path.setAttribute('filter', `url(#${filterId})`)
      path.setAttribute('opacity', '0.82')
      svg.appendChild(path)

      // Vein line
      const vein = document.createElementNS(NS, 'line')
      vein.setAttribute('x1', '7'); vein.setAttribute('y1', '1')
      vein.setAttribute('x2', '7'); vein.setAttribute('y2', '19')
      vein.setAttribute('stroke', GOLD_SHADES[0])
      vein.setAttribute('stroke-width', '0.6')
      vein.setAttribute('opacity', '0.22')
      svg.appendChild(vein)

      // Random starting position
      const startX = Math.random() * window.innerWidth
      const startY = Math.random() * window.innerHeight
      svg.style.left = `${startX}px`
      svg.style.top  = `${startY}px`

      // CSS custom props for animation trajectory
      const dx = (Math.random() - 0.5) * 200
      const dy = 300 + Math.random() * 300
      const r0 = Math.random() * 360
      const r1 = r0 + (Math.random() - 0.5) * 540
      const dur = 8 + Math.random() * 14
      svg.style.setProperty('--dx', `${dx}px`)
      svg.style.setProperty('--dy', `${dy}px`)
      svg.style.setProperty('--r0', `${r0}deg`)
      svg.style.setProperty('--r1', `${r1}deg`)
      svg.style.animationDuration = `${dur}s`
      svg.style.animationDelay = `${-Math.random() * dur}s`

      // Re-randomize on each iteration end
      const onIteration = () => {
        const newStartX = Math.random() * window.innerWidth
        const newStartY = -20 - Math.random() * 100
        svg.style.left = `${newStartX}px`
        svg.style.top  = `${newStartY}px`
        svg.style.setProperty('--dx', `${(Math.random() - 0.5) * 200}px`)
        svg.style.setProperty('--dy', `${300 + Math.random() * 300}px`)
        svg.style.setProperty('--r0', `${Math.random() * 360}deg`)
        svg.style.setProperty('--r1', `${Math.random() * 720}deg`)
      }

      svg.addEventListener('animationiteration', onIteration)
      container.appendChild(svg)
      leaves.push({ svg, onIteration })
    }

    return () => {
      leaves.forEach(({ svg, onIteration }) => {
        svg.removeEventListener('animationiteration', onIteration)
        svg.remove()
      })
    }
  }, [theme])

  return <div ref={containerRef} className="leaf-container" aria-hidden />
}
