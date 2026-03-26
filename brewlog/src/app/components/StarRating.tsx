import { Star } from 'lucide-react'

interface StarRatingProps {
  rating: number
  maxRating?: number
  size?: number
  interactive?: boolean
  onChange?: (rating: number) => void
}

export function StarRating({
  rating,
  maxRating = 5,
  size = 16,
  interactive = false,
  onChange
}: StarRatingProps) {
  const handleClick = (value: number) => {
    if (interactive && onChange) {
      onChange(value)
    }
  }

  return (
    <div className="flex gap-0.5" data-testid="star-rating">
      {Array.from({ length: maxRating }, (_, i) => {
        const starValue = i + 1
        const isFilled = starValue <= rating

        return (
          <button
            key={i}
            type="button"
            onClick={() => handleClick(starValue)}
            disabled={!interactive}
            className={interactive ? 'cursor-pointer hover:scale-110 transition-transform' : 'cursor-default'}
          >
            <Star
              size={size}
              className={isFilled ? 'fill-[#C4704B] text-[#C4704B]' : 'fill-[#E8DDD1] text-[#E8DDD1]'}
            />
          </button>
        )
      })}
    </div>
  )
}
