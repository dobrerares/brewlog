import { Coffee } from 'lucide-react'
import { Link } from 'react-router'

interface LogoProps {
  size?: 'small' | 'large'
  link?: boolean
}

export function Logo({ size = 'small', link = true }: LogoProps) {
  const iconSize = size === 'large' ? 32 : 24
  const textSize = size === 'large' ? 'text-3xl' : 'text-xl'

  const content = (
    <div className="flex items-center gap-2">
      <Coffee size={iconSize} style={{ color: 'var(--primary-brown)' }} strokeWidth={2} />
      <span className={textSize} style={{ fontFamily: 'var(--font-heading)', color: 'var(--primary-brown)' }}>
        BrewLog
      </span>
    </div>
  )

  if (link) {
    return (
      <Link to="/" className="hover:opacity-80 transition-opacity">
        {content}
      </Link>
    )
  }

  return content
}
