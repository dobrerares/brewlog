interface TasteBadgeProps {
  taste: 'Balanced' | 'Sour' | 'Bitter' | 'Watery' | 'Astringent'
}

const tasteStyles: Record<string, string> = {
  Balanced: 'bg-[#5A7A5A]/10 text-[#5A7A5A] border-[#5A7A5A]/20',
  Sour: 'bg-[#C49A3C]/10 text-[#C49A3C] border-[#C49A3C]/20',
  Bitter: 'bg-[#B85C4A]/10 text-[#B85C4A] border-[#B85C4A]/20',
  Watery: 'bg-gray-100 text-gray-600 border-gray-200',
  Astringent: 'bg-amber-50 text-amber-700 border-amber-200'
}

export function TasteBadge({ taste }: TasteBadgeProps) {
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${tasteStyles[taste] || ''}`}>
      {taste}
    </span>
  )
}
