import { useParams, Link, useNavigate } from 'react-router'
import { useState, useEffect } from 'react'
import { ArrowLeft } from 'lucide-react'
import { beans, methods, grinders, brewers, flavorOptions, tasteOptions } from '../data/mockData'
import { useBrewValidation } from '../hooks/useBrewValidation'
import { useBrewCRUD } from '../hooks/useBrewCRUD'
import { useActivityTracker } from '../hooks/useActivityTracker'
import { ThemeToggle } from '../components/ThemeToggle'

export function BrewForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id
  const { validateForm } = useBrewValidation()
  const { getBrew, createBrew, updateBrew } = useBrewCRUD()
  const { trackVisit } = useActivityTracker()
  useEffect(() => { trackVisit(isEdit ? `/brew/${id}/edit` : '/brew/new') }, [])

  const [formData, setFormData] = useState({
    bean: '',
    method: '',
    date: new Date().toISOString().split('T')[0],
    dose: 0,
    water: 0,
    temp: 0,
    time: '',
    grind: '',
    grinder: '',
    brewer: '',
    yield: 0,
    rating: 0,
    taste: 'Balanced',
    flavorTags: [] as string[],
    notes: ''
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Pre-fill form when editing
  useEffect(() => {
    if (isEdit && id) {
      const brew = getBrew(id)
      if (brew) {
        setFormData({
          bean: brew.bean,
          method: brew.method,
          date: brew.date,
          dose: brew.dose,
          water: brew.water,
          temp: brew.temp,
          time: brew.time,
          grind: brew.grind,
          grinder: brew.grinder,
          brewer: brew.brewer || '',
          yield: brew.yield || 0,
          rating: brew.rating,
          taste: brew.taste,
          flavorTags: brew.flavorTags || [],
          notes: brew.notes || ''
        })
      }
    }
  }, [isEdit, id, getBrew])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: ['dose', 'water', 'temp', 'yield', 'rating'].includes(name) ? parseFloat(value) : value
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const validationErrors = validateForm(formData as any)

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const brewData = {
      ...formData,
      taste: formData.taste as 'Balanced' | 'Sour' | 'Bitter' | 'Watery' | 'Astringent'
    }

    if (isEdit && id) {
      updateBrew(id, brewData)
      navigate(`/brew/${id}`)
    } else {
      createBrew(brewData)
      navigate('/brews')
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <nav style={{ borderColor: 'var(--border-color)' }} className="border-b">
        <div className="max-w-6xl mx-auto px-8 py-4 flex items-center justify-between">
          <Link to="/" style={{ color: 'var(--primary-brown)' }}>
            <h3 className="m-0">BrewLog</h3>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/brews" style={{ color: 'var(--foreground)' }} className="text-sm hover:opacity-60 transition-opacity">
              Brews
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-8 py-12">
        <Link
          to={isEdit ? `/brew/${id}` : '/brews'}
          className="inline-flex items-center gap-2 mb-8 font-medium hover:opacity-60 transition-opacity"
          style={{ color: 'var(--primary-brown)' }}
        >
          <ArrowLeft size={16} /> Back
        </Link>

        <div style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }} className="border rounded-lg p-8">
          <h1 style={{ color: 'var(--primary-dark)' }} className="mb-8">
            {isEdit ? 'Edit Brew Log' : 'Log a New Brew'}
          </h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Bean & Method */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Bean *</label>
                <select
                  name="bean"
                  value={formData.bean}
                  onChange={handleChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors ${
                    errors.bean ? 'border-red-500' : ''
                  }`}
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: errors.bean ? undefined : 'var(--border-color)'
                  }}
                >
                  <option value="">Select bean</option>
                  {beans.map(bean => (
                    <option key={bean} value={bean}>{bean}</option>
                  ))}
                </select>
                {errors.bean && <p style={{ color: 'var(--red)' }} className="text-xs mt-1">{errors.bean}</p>}
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Method *</label>
                <select
                  name="method"
                  value={formData.method}
                  onChange={handleChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors ${
                    errors.method ? 'border-red-500' : ''
                  }`}
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: errors.method ? undefined : 'var(--border-color)'
                  }}
                >
                  <option value="">Select method</option>
                  {methods.map(method => (
                    <option key={method} value={method}>{method}</option>
                  ))}
                </select>
                {errors.method && <p style={{ color: 'var(--red)' }} className="text-xs mt-1">{errors.method}</p>}
              </div>
            </div>

            {/* Date & Grinder */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Date *</label>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                />
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Grinder *</label>
                <select
                  name="grinder"
                  value={formData.grinder}
                  onChange={handleChange}
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                >
                  <option value="">Select grinder</option>
                  {grinders.map(g => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Dose, Water, Temp, Time */}
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Dose (g) *</label>
                <input
                  type="number"
                  name="dose"
                  value={formData.dose}
                  onChange={handleChange}
                  step="0.1"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                />
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Water (g) *</label>
                <input
                  type="number"
                  name="water"
                  value={formData.water}
                  onChange={handleChange}
                  step="1"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                />
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Temp (°C) *</label>
                <input
                  type="number"
                  name="temp"
                  value={formData.temp}
                  onChange={handleChange}
                  step="1"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                />
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Time (MM:SS) *</label>
                <input
                  type="text"
                  name="time"
                  value={formData.time}
                  onChange={handleChange}
                  placeholder="2:30"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                />
              </div>
            </div>

            {/* Grind & Brewer & Yield */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Grind Setting *</label>
                <input
                  type="text"
                  name="grind"
                  value={formData.grind}
                  onChange={handleChange}
                  placeholder="e.g. 22 clicks"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                />
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Brewer</label>
                <select
                  name="brewer"
                  value={formData.brewer}
                  onChange={handleChange}
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                >
                  <option value="">Select brewer</option>
                  {brewers.map(b => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Yield (g)</label>
                <input
                  type="number"
                  name="yield"
                  value={formData.yield}
                  onChange={handleChange}
                  step="1"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors"
                  style={{
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    borderColor: 'var(--border-color)'
                  }}
                />
              </div>
            </div>

            <div style={{ borderColor: 'var(--border-color)' }} className="border-t" />

            {/* Review Section */}
            <div>
              <h3 style={{ color: 'var(--primary-brown)' }} className="text-sm font-semibold uppercase mb-4">Post-Brew Review</h3>

              <div className="space-y-4">
                <div>
                  <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Taste *</label>
                  <div className="flex flex-wrap gap-2">
                    {tasteOptions.map(option => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, taste: option.value }))}
                        className="px-4 py-2 rounded-full text-sm font-medium transition-colors"
                        style={{
                          backgroundColor: formData.taste === option.value ? 'var(--primary-brown)' : 'var(--cream)',
                          color: formData.taste === option.value ? '#FFFFFF' : 'var(--primary-brown)'
                        }}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Rating *</label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map(r => (
                      <button
                        key={r}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, rating: r }))}
                        className="text-3xl transition-transform"
                        style={{
                          opacity: formData.rating >= r ? 1 : 0.3
                        }}
                      >
                        ⭐
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Tasting Notes</label>
                  <div className="flex flex-wrap gap-2">
                    {flavorOptions.map(flavor => (
                      <button
                        key={flavor}
                        type="button"
                        onClick={() =>
                          setFormData(prev => ({
                            ...prev,
                            flavorTags: prev.flavorTags.includes(flavor)
                              ? prev.flavorTags.filter(f => f !== flavor)
                              : [...prev.flavorTags, flavor]
                          }))
                        }
                        className="px-3 py-1 rounded-full text-xs font-medium transition-colors"
                        style={{
                          backgroundColor: formData.flavorTags.includes(flavor) ? 'var(--primary-brown)' : 'var(--cream)',
                          color: formData.flavorTags.includes(flavor) ? '#FFFFFF' : 'var(--primary-brown)'
                        }}
                      >
                        {flavor}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label style={{ color: 'var(--text-muted)' }} className="block text-sm font-medium mb-2">Notes</label>
                  <textarea
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    rows={3}
                    placeholder="How was this cup?"
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none transition-colors resize-none"
                    style={{
                      backgroundColor: 'var(--background)',
                      color: 'var(--foreground)',
                      borderColor: 'var(--border-color)'
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                className="px-8 py-3 text-white rounded-lg hover:opacity-90 font-medium transition-colors"
                style={{ backgroundColor: 'var(--primary-brown)' }}
              >
                {isEdit ? 'Save Changes' : 'Log Brew'}
              </button>
              <Link
                to={isEdit ? `/brew/${id}` : '/brews'}
                className="px-8 py-3 rounded-lg font-medium transition-colors"
                style={{
                  backgroundColor: 'var(--cream)',
                  color: 'var(--primary-brown)'
                }}
              >
                Cancel
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
