import type { BrewLog } from '../data/mockData'

interface ValidationErrors {
  [key: string]: string
}

const REQUIRED_FIELDS = ['bean', 'method', 'date', 'dose', 'water', 'temp', 'time', 'grind', 'grinder', 'rating', 'taste']

export function useBrewValidation() {
  const validateField = (field: string, value: BrewLog[keyof BrewLog] | null | undefined): string => {
    // Required field check
    if (REQUIRED_FIELDS.includes(field) && (value === '' || value === null || value === undefined || value === 0)) {
      return `${field.charAt(0).toUpperCase() + field.slice(1)} is required`
    }

    // Numeric validations
    switch (field) {
      case 'dose':
        if (typeof value === 'number' && value <= 0) {
          return 'Dose must be greater than 0'
        }
        break

      case 'water':
        if (typeof value === 'number' && value <= 0) {
          return 'Water must be greater than 0'
        }
        break

      case 'temp':
        if (typeof value === 'number' && (value < 80 || value > 100)) {
          return 'Temperature must be between 80-100°C'
        }
        break

      case 'rating':
        if (typeof value === 'number' && (value < 1 || value > 5)) {
          return 'Rating must be between 1 and 5'
        }
        break

      case 'time':
        if (value && !/^\d{1,2}:\d{2}$/.test(String(value))) {
          return 'Brew time must be in MM:SS format'
        }
        break
    }

    return ''
  }

  const validateForm = (brew: Partial<BrewLog>): ValidationErrors => {
    const errors: ValidationErrors = {}

    // Field-level validation
    REQUIRED_FIELDS.forEach(field => {
      const error = validateField(field, brew[field as keyof BrewLog])
      if (error) errors[field] = error
    })

    // Business rule: dose/water ratio (10-20x)
    if (brew.dose && brew.water && !errors.dose && !errors.water) {
      const ratio = brew.water / brew.dose
      if (ratio < 10 || ratio > 20) {
        errors.water = `Water should be 10-20x the dose (currently ${ratio.toFixed(1)}x). E.g., 15g dose → 150-300g water`
      }
    }

    // Business rule: temp to method constraints
    if (brew.method && brew.temp && !errors.temp) {
      const methodTempMap: Record<string, { min: number; max: number }> = {
        'Espresso': { min: 85, max: 100 },
        'V60': { min: 90, max: 96 },
        'Chemex': { min: 90, max: 96 },
        'AeroPress': { min: 85, max: 100 },
        'French Press': { min: 90, max: 100 }
      }

      const constraint = methodTempMap[brew.method]
      if (constraint && (brew.temp < constraint.min || brew.temp > constraint.max)) {
        errors.temp = `${brew.method} requires ${constraint.min}-${constraint.max}°C (${brew.temp}°C is outside range)`
      }
    }

    // Cross-field: low rating requires notes
    if (brew.rating && brew.rating < 3 && !brew.notes) {
      errors.notes = 'Please add notes for low-rated brews to improve future brews'
    }

    return errors
  }

  return {
    validateField,
    validateForm
  }
}
