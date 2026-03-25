import { describe, it, expect } from 'vitest'
import { useBrewValidation } from '../useBrewValidation'

describe('useBrewValidation', () => {
  const { validateField, validateForm } = useBrewValidation()

  describe('validateField', () => {
    describe('required fields', () => {
      it('should reject empty required fields', () => {
        expect(validateField('bean', '')).toContain('required')
        expect(validateField('method', '')).toContain('required')
        expect(validateField('dose', 0)).toContain('required')
      })

      it('should accept non-empty required fields', () => {
        expect(validateField('bean', 'Ethiopian Yirgacheffe')).toBe('')
        expect(validateField('method', 'V60')).toBe('')
        expect(validateField('dose', 18)).toBe('')
      })

      it('should reject null/undefined required fields', () => {
        expect(validateField('bean', null)).toContain('required')
        expect(validateField('date', undefined)).toContain('required')
      })
    })

    describe('numeric validations', () => {
      it('should reject dose <= 0', () => {
        // 0 is treated as required field not provided
        expect(validateField('dose', 0)).toContain('required')
        // Negative values trigger the > 0 check
        expect(validateField('dose', -5)).toContain('greater than 0')
      })

      it('should accept dose > 0', () => {
        expect(validateField('dose', 18)).toBe('')
        expect(validateField('dose', 0.1)).toBe('')
      })

      it('should reject water <= 0', () => {
        // 0 is treated as required field not provided
        expect(validateField('water', 0)).toContain('required')
        // Negative values trigger the > 0 check
        expect(validateField('water', -100)).toContain('greater than 0')
      })

      it('should accept water > 0', () => {
        expect(validateField('water', 300)).toBe('')
      })

      it('should reject temperature outside 80-100°C', () => {
        expect(validateField('temp', 70)).toContain('80-100')
        expect(validateField('temp', 105)).toContain('80-100')
      })

      it('should accept temperature within 80-100°C', () => {
        expect(validateField('temp', 80)).toBe('')
        expect(validateField('temp', 90)).toBe('')
        expect(validateField('temp', 100)).toBe('')
      })

      it('should reject rating outside 1-5', () => {
        // 0 is treated as required field not provided
        expect(validateField('rating', 0)).toContain('required')
        // Values outside 1-5 trigger the range check
        expect(validateField('rating', 6)).toContain('1 and 5')
      })

      it('should accept rating within 1-5', () => {
        expect(validateField('rating', 1)).toBe('')
        expect(validateField('rating', 5)).toBe('')
        expect(validateField('rating', 3)).toBe('')
      })
    })

    describe('time format validation', () => {
      it('should reject invalid time formats', () => {
        expect(validateField('time', '2-30')).toContain('MM:SS')
        expect(validateField('time', '230')).toContain('MM:SS')
        expect(validateField('time', '02:30:00')).toContain('MM:SS')
        expect(validateField('time', 'abc')).toContain('MM:SS')
      })

      it('should accept valid MM:SS format', () => {
        expect(validateField('time', '2:30')).toBe('')
        expect(validateField('time', '02:30')).toBe('')
        expect(validateField('time', '30:45')).toBe('')
      })

      it('should reject empty time for required field', () => {
        // Time is in REQUIRED_FIELDS, so empty string is invalid
        expect(validateField('time', '')).toContain('required')
      })
    })

    describe('non-required fields', () => {
      it('should not require brewer field', () => {
        expect(validateField('brewer', '')).toBe('')
        expect(validateField('brewer', null)).toBe('')
      })
    })
  })

  describe('validateForm', () => {
    const validBrew = {
      bean: 'Ethiopian',
      method: 'V60',
      date: '2024-01-01',
      dose: 18,
      water: 300,
      temp: 90,
      time: '3:00',
      grind: '22 clicks',
      grinder: 'Baratza Encore',
      rating: 4,
      taste: 'Balanced' as const
    }

    it('should accept valid brew data', () => {
      const errors = validateForm(validBrew)
      expect(Object.keys(errors)).toHaveLength(0)
    })

    describe('business rule: dose/water ratio 10-20x', () => {
      it('should reject ratio < 10x', () => {
        const brew = { ...validBrew, dose: 30, water: 250 } // 8.3x ratio
        const errors = validateForm(brew)
        expect(errors.water).toContain('10-20x')
      })

      it('should reject ratio > 20x', () => {
        const brew = { ...validBrew, dose: 15, water: 350 } // 23.3x ratio
        const errors = validateForm(brew)
        expect(errors.water).toContain('10-20x')
      })

      it('should accept ratio 10x-20x', () => {
        const brew10x = { ...validBrew, dose: 20, water: 200 }
        const brew15x = { ...validBrew, dose: 20, water: 300 }
        const brew20x = { ...validBrew, dose: 20, water: 400 }
        expect(validateForm(brew10x).water).toBeUndefined()
        expect(validateForm(brew15x).water).toBeUndefined()
        expect(validateForm(brew20x).water).toBeUndefined()
      })
    })

    describe('business rule: temp constraints by method', () => {
      it('should enforce Espresso 85-100°C', () => {
        const espresso84 = { ...validBrew, method: 'Espresso', temp: 84 }
        expect(validateForm(espresso84).temp).toContain('85-100')

        const espresso90 = { ...validBrew, method: 'Espresso', temp: 90 }
        expect(validateForm(espresso90).temp).toBeUndefined()
      })

      it('should enforce V60 90-96°C', () => {
        const v6089 = { ...validBrew, method: 'V60', temp: 89 }
        expect(validateForm(v6089).temp).toContain('90-96')

        const v6093 = { ...validBrew, method: 'V60', temp: 93 }
        expect(validateForm(v6093).temp).toBeUndefined()
      })

      it('should enforce Chemex 90-96°C', () => {
        const chemex89 = { ...validBrew, method: 'Chemex', temp: 89 }
        expect(validateForm(chemex89).temp).toContain('90-96')
      })

      it('should enforce AeroPress 85-100°C', () => {
        const aeropress90 = { ...validBrew, method: 'AeroPress', temp: 90 }
        expect(validateForm(aeropress90).temp).toBeUndefined()
      })

      it('should enforce French Press 90-100°C', () => {
        const frenchPress95 = { ...validBrew, method: 'French Press', temp: 95 }
        expect(validateForm(frenchPress95).temp).toBeUndefined()
      })
    })

    describe('cross-field rule: low rating requires notes', () => {
      it('should require notes for rating < 3', () => {
        const lowRatingNoNotes = { ...validBrew, rating: 2, notes: '' }
        const errors = validateForm(lowRatingNoNotes)
        expect(errors.notes).toContain('low-rated')
      })

      it('should not require notes for rating >= 3', () => {
        const goodRatingNoNotes = { ...validBrew, rating: 3, notes: '' }
        const errors = validateForm(goodRatingNoNotes)
        expect(errors.notes).toBeUndefined()
      })

      it('should accept low rating with notes', () => {
        const lowRatingWithNotes = { ...validBrew, rating: 1, notes: 'Too bitter' }
        const errors = validateForm(lowRatingWithNotes)
        expect(errors.notes).toBeUndefined()
      })
    })

    describe('multiple errors', () => {
      it('should return all field errors', () => {
        const invalidBrew = {
          bean: '',
          method: '',
          date: '2024-01-01',
          dose: 0,
          water: 0,
          temp: 50,
          time: 'invalid',
          grind: '',
          grinder: '',
          rating: 6,
          taste: 'Sour' as const
        }
        const errors = validateForm(invalidBrew)
        expect(Object.keys(errors).length).toBeGreaterThan(5)
        expect(errors.bean).toBeDefined()
        expect(errors.dose).toBeDefined()
        expect(errors.temp).toBeDefined()
        expect(errors.rating).toBeDefined()
      })
    })
  })
})
