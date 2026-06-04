import { useParams, Link, useNavigate } from 'react-router'
import { useState, useEffect } from 'react'
import { ArrowLeft, AlertCircle } from 'lucide-react'
import { beans, methods, grinders, brewers, flavorOptions, tasteOptions } from '../data/mockData'
import { useBrewValidation } from '../hooks/useBrewValidation'
import { useBrewCRUD } from '../hooks/useBrewCRUD'
import { useActivityTracker } from '../hooks/useActivityTracker'
import { Navbar } from '../components/Navbar'
import { StarRating } from '../components/StarRating'
import { FlavorTag } from '../components/FlavorTag'
import type { BrewLog } from '../data/mockData'

type BrewFormData = Omit<BrewLog, 'id'>

function ErrorMessage({ message }: { message?: string }) {
  if (!message) return null
  return (
    <div className="flex items-center gap-1 mt-1 text-xs text-red-600">
      <AlertCircle size={12} />
      <span>{message}</span>
    </div>
  )
}

export function BrewForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id
  const { validateForm } = useBrewValidation()
  const { getBrew, createBrew, updateBrew } = useBrewCRUD()
  const { trackVisit } = useActivityTracker()
  useEffect(() => { trackVisit(isEdit ? `/brew/${id}/edit` : '/brew/new') }, [id, isEdit, trackVisit])

  const [formData, setFormData] = useState<BrewFormData>({
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
    flavorTags: [],
    notes: ''
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  useEffect(() => {
    if (isEdit && id) {
      const timer = window.setTimeout(() => {
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
      }, 0)
      return () => window.clearTimeout(timer)
    }
  }, [isEdit, id, getBrew])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: ['dose', 'water', 'temp', 'yield', 'rating'].includes(name) ? parseFloat(value) : value
    }))
    if (touched[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const handleBlur = (name: string) => {
    setTouched(prev => ({ ...prev, [name]: true }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const validationErrors = validateForm(formData)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      const allTouched: Record<string, boolean> = {}
      Object.keys(validationErrors).forEach(k => { allTouched[k] = true })
      setTouched(prev => ({ ...prev, ...allTouched }))
      return
    }
    if (isEdit && id) {
      updateBrew(id, formData)
      navigate(`/brew/${id}`)
    } else {
      createBrew(formData)
      navigate('/brews')
    }
  }

  const inputClass = (field: string) =>
    `w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
      touched[field] && errors[field] ? 'border-red-500' : ''
    }`

  const inputStyle = (field: string) => ({
    backgroundColor: 'var(--background)',
    color: 'var(--foreground)',
    borderColor: touched[field] && errors[field] ? undefined : 'var(--border-color)'
  })

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <Navbar type="app" />

      <div className="max-w-3xl mx-auto px-4 sm:px-8 py-8">
        <Link
          to={isEdit ? `/brew/${id}` : '/brews'}
          className="inline-flex items-center gap-1 text-sm hover:underline mb-6"
          style={{ color: 'var(--primary-brown)' }}
        >
          <ArrowLeft size={16} /> Back
        </Link>

        <div className="rounded-xl border p-6 sm:p-8 animate-fadeIn" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
          <h1 className="text-2xl mb-8" style={{ fontFamily: 'var(--font-heading)' }}>
            {isEdit ? 'Edit brew log' : 'Log a new brew'}
          </h1>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Top grid: Date, Method, Bean, Grinder, Grind, Brewer */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Date</label>
                <input type="date" name="date" value={formData.date} onChange={handleChange}
                  className={inputClass('date')} style={inputStyle('date')} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Method <span className="text-red-500">*</span></label>
                <select name="method" value={formData.method} onChange={handleChange} onBlur={() => handleBlur('method')}
                  className={inputClass('method')} style={inputStyle('method')}>
                  <option value="">Select method</option>
                  {methods.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
                <ErrorMessage message={touched.method ? errors.method : undefined} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Bean <span className="text-red-500">*</span></label>
                <select name="bean" value={formData.bean} onChange={handleChange} onBlur={() => handleBlur('bean')}
                  className={inputClass('bean')} style={inputStyle('bean')}>
                  <option value="">Select bean</option>
                  {beans.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
                <ErrorMessage message={touched.bean ? errors.bean : undefined} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Grinder <span className="text-red-500">*</span></label>
                <select name="grinder" value={formData.grinder} onChange={handleChange} onBlur={() => handleBlur('grinder')}
                  className={inputClass('grinder')} style={inputStyle('grinder')}>
                  <option value="">Select grinder</option>
                  {grinders.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
                <ErrorMessage message={touched.grinder ? errors.grinder : undefined} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Grind setting <span className="text-red-500">*</span></label>
                <input type="text" name="grind" placeholder="e.g. 24 clicks" value={formData.grind} onChange={handleChange} onBlur={() => handleBlur('grind')}
                  className={inputClass('grind')} style={inputStyle('grind')} />
                <ErrorMessage message={touched.grind ? errors.grind : undefined} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Brewer</label>
                <select name="brewer" value={formData.brewer} onChange={handleChange}
                  className={inputClass('brewer')} style={inputStyle('brewer')}>
                  <option value="">Select brewer</option>
                  {brewers.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
            </div>

            <div className="h-px" style={{ backgroundColor: 'var(--border-color)' }} />

            {/* Brew params */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Dose (g) <span className="text-red-500">*</span></label>
                <input type="number" name="dose" step="0.1" value={formData.dose} onChange={handleChange} onBlur={() => handleBlur('dose')}
                  className={inputClass('dose')} style={inputStyle('dose')} />
                <ErrorMessage message={touched.dose ? errors.dose : undefined} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Water (g) <span className="text-red-500">*</span></label>
                <input type="number" name="water" step="1" value={formData.water} onChange={handleChange} onBlur={() => handleBlur('water')}
                  className={inputClass('water')} style={inputStyle('water')} />
                <ErrorMessage message={touched.water ? errors.water : undefined} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Temp (°C) <span className="text-red-500">*</span></label>
                <input type="number" name="temp" step="1" value={formData.temp} onChange={handleChange} onBlur={() => handleBlur('temp')}
                  className={inputClass('temp')} style={inputStyle('temp')} />
                <ErrorMessage message={touched.temp ? errors.temp : undefined} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Brew time <span className="text-red-500">*</span></label>
                <input type="text" name="time" placeholder="e.g. 2:30" value={formData.time} onChange={handleChange} onBlur={() => handleBlur('time')}
                  className={inputClass('time')} style={inputStyle('time')} />
                <ErrorMessage message={touched.time ? errors.time : undefined} />
              </div>
              <div>
                <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Yield (g, optional)</label>
                <input type="number" name="yield" step="1" value={formData.yield} onChange={handleChange}
                  className={inputClass('yield')} style={inputStyle('yield')} />
              </div>
            </div>

            <div className="h-px" style={{ backgroundColor: 'var(--border-color)' }} />

            {/* Post-brew review */}
            <div>
              <p className="text-xs font-semibold mb-4 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
                Post-brew review
              </p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    How did it taste? <span className="text-red-500">*</span>
                  </label>
                  <div className="flex flex-wrap gap-3">
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
                  <label className="block text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    Rating <span className="text-red-500">*</span>
                  </label>
                  <StarRating
                    rating={formData.rating}
                    size={28}
                    interactive
                    onChange={(r) => setFormData(prev => ({ ...prev, rating: r }))}
                  />
                  <ErrorMessage message={touched.rating ? errors.rating : undefined} />
                </div>

                <div>
                  <label className="block text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    Tasting notes
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {flavorOptions.map(flavor => (
                      <FlavorTag
                        key={flavor}
                        label={flavor}
                        selected={formData.flavorTags.includes(flavor)}
                        onClick={() =>
                          setFormData(prev => ({
                            ...prev,
                            flavorTags: prev.flavorTags.includes(flavor)
                              ? prev.flavorTags.filter(f => f !== flavor)
                              : [...prev.flavorTags, flavor]
                          }))
                        }
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Notes</label>
                  <textarea
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    rows={3}
                    placeholder="How was this cup?"
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors resize-none"
                    style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row items-center gap-4 pt-4">
              <button
                type="submit"
                className="w-full sm:w-auto px-8 py-3 text-white rounded-lg hover:opacity-90 transition-colors font-medium"
                style={{ backgroundColor: 'var(--primary-brown)' }}
              >
                {isEdit ? 'Save changes' : 'Log brew'}
              </button>
              <Link
                to={isEdit ? `/brew/${id}` : '/brews'}
                className="w-full sm:w-auto text-center px-8 py-3 rounded-lg transition-colors"
                style={{ color: 'var(--primary-brown)' }}
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
