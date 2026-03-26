interface FlavorTagProps {
  label: string
  selected?: boolean
  onClick?: () => void
}

export function FlavorTag({ label, selected = false, onClick }: FlavorTagProps) {
  const baseStyles = 'inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium border transition-colors'
  const styles = selected
    ? 'bg-[#F5EDE3] text-[#6B4226] border-[#E8DDD1]'
    : 'bg-white text-[#8C7B6B] border-[#E8DDD1] hover:bg-[#FAF6F1]'

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={`${baseStyles} ${styles} cursor-pointer`}>
        {label}
      </button>
    )
  }

  return (
    <span className={`${baseStyles} ${styles}`}>
      {label}
    </span>
  )
}
