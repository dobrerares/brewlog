import { useState, useEffect } from 'react'
import { Link } from 'react-router'
import { BarChart3, Coffee, Star, Target, Plus, Trash2, Pencil } from 'lucide-react'
import { PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import { Navbar } from '../components/Navbar'
import { StarRating } from '../components/StarRating'
import { TasteBadge } from '../components/TasteBadge'
import { DeleteConfirmModal } from '../components/DeleteConfirmModal'
import { useBrewCRUD } from '../hooks/useBrewCRUD'
import { useActivityTracker } from '../hooks/useActivityTracker'
import type { BrewLog } from '../data/mockData'

export function Statistics() {
  const { getBrews, deleteBrew } = useBrewCRUD()
  const brews = getBrews()
  const { trackVisit } = useActivityTracker()
  useEffect(() => { trackVisit('/dashboard') }, [])

  const [selectedBrewDNA, setSelectedBrewDNA] = useState<string | null>(brews[0]?.id || null)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

  const handleDelete = () => {
    if (deleteTarget) {
      deleteBrew(deleteTarget)
      setDeleteTarget(null)
    }
  }

  // Compute stats from live CRUD data
  const totalBrews = brews.length
  const avgRating = totalBrews > 0 ? (brews.reduce((sum, b) => sum + b.rating, 0) / totalBrews).toFixed(1) : '0'

  const methodDistribution = brews.reduce((acc, b) => {
    acc[b.method] = (acc[b.method] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const tasteDistribution = brews.reduce((acc, b) => {
    acc[b.taste] = (acc[b.taste] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const ratingDistribution = brews.reduce((acc, b) => {
    const key = `${b.rating}★`
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const beanCounts = brews.reduce((acc, b) => {
    acc[b.bean] = (acc[b.bean] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const topBeanEntry = Object.entries(beanCounts).sort((a, b) => b[1] - a[1])[0] || ['—', 0]

  // Chart data
  const COLORS = ['#6B4226', '#C4704B', '#E9B949', '#8C7B6B', '#D4A574', '#5A7A5A']

  const tasteColors: Record<string, string> = {
    Balanced: '#5A7A5A', Sour: '#C49A3C', Bitter: '#B85C4A', Watery: '#8C7B6B', Astringent: '#D4A574'
  }

  const methodData = Object.entries(methodDistribution).map(([name, value]) => ({ name, value }))
  const tasteData = Object.entries(tasteDistribution).map(([name, value]) => ({ name, value, color: tasteColors[name] || '#8C7B6B' }))
  const ratingData = Object.entries(ratingDistribution).map(([name, count]) => ({ name, count }))

  // Brew DNA radar
  const generateBrewDNA = (brew: BrewLog) => {
    const maxDose = Math.max(...brews.map(b => b.dose), 1)
    const maxWater = Math.max(...brews.map(b => b.water), 1)
    return [
      { parameter: 'Dose', value: (brew.dose / maxDose) * 100 },
      { parameter: 'Water', value: (brew.water / maxWater) * 100 },
      { parameter: 'Temp', value: (brew.temp / 100) * 100 },
      { parameter: 'Time', value: Math.min(((parseInt(brew.time.split(':')[0]) * 60 + parseInt(brew.time.split(':')[1])) / 360) * 100, 100) },
      { parameter: 'Rating', value: (brew.rating / 5) * 100 },
      { parameter: 'Grind', value: Math.min((parseFloat(brew.grind) / 40) * 100, 100) },
    ]
  }

  if (totalBrews === 0) {
    return (
      <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
        <Navbar type="app" />
        <div className="max-w-4xl mx-auto px-8 py-20 text-center">
          <Coffee size={48} className="mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
          <p className="mb-6" style={{ color: 'var(--text-muted)' }}>No brews logged yet. Start brewing to see statistics!</p>
          <Link
            to="/brew/new"
            className="inline-flex items-center gap-2 px-6 py-3 text-white rounded-lg hover:opacity-90 transition-colors font-medium"
            style={{ backgroundColor: 'var(--primary-brown)' }}
          >
            <Plus size={20} /> Log your first brew
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <Navbar type="app" />

      <div className="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl mb-2" style={{ fontFamily: 'var(--font-heading)', color: 'var(--primary-dark)' }}>
              Dashboard
            </h1>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Charts update live as you add, edit, or delete brews
            </p>
          </div>
          <Link
            to="/brew/new"
            className="flex items-center gap-2 px-6 py-3 text-white rounded-lg hover:opacity-90 transition-colors font-medium"
            style={{ backgroundColor: 'var(--primary-brown)' }}
          >
            <Plus size={20} /> New brew
          </Link>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-8">
          <div className="rounded-xl border p-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: '#6B422615' }}>
                <Coffee size={24} style={{ color: 'var(--primary-brown)' }} />
              </div>
              <div>
                <p className="text-2xl font-bold" style={{ color: 'var(--primary-dark)' }}>{totalBrews}</p>
                <p className="text-xs uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Total Brews</p>
              </div>
            </div>
          </div>
          <div className="rounded-xl border p-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: '#C4704B15' }}>
                <Star size={24} style={{ color: 'var(--accent-terracotta)' }} />
              </div>
              <div>
                <p className="text-2xl font-bold" style={{ color: 'var(--primary-dark)' }}>{avgRating}</p>
                <p className="text-xs uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Avg Rating</p>
              </div>
            </div>
          </div>
          <div className="rounded-xl border p-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: '#E9B94915' }}>
                <Target size={24} style={{ color: 'var(--yellow)' }} />
              </div>
              <div>
                <p className="text-lg font-bold" style={{ color: 'var(--primary-dark)' }}>{topBeanEntry[0]}</p>
                <p className="text-xs uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Top Bean ({topBeanEntry[1]} brews)</p>
              </div>
            </div>
          </div>
        </div>

        {/* Side-by-side: Charts (left) + Data Table (right) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* LEFT: Charts */}
          <div className="space-y-6 animate-fadeIn">
            {/* Methods Pie */}
            <div className="rounded-xl border p-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
              <h2 className="text-lg font-semibold mb-4" style={{ fontFamily: 'var(--font-heading)', color: 'var(--primary-dark)' }}>
                Brewing Methods
              </h2>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={methodData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                    outerRadius={90}
                    dataKey="value"
                  >
                    {methodData.map((_, index) => (
                      <Cell key={`method-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Taste Bar */}
            <div className="rounded-xl border p-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
              <h2 className="text-lg font-semibold mb-4" style={{ fontFamily: 'var(--font-heading)', color: 'var(--primary-dark)' }}>
                Taste Distribution
              </h2>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={tasteData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {tasteData.map((entry, index) => (
                      <Cell key={`taste-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Rating Distribution */}
            <div className="rounded-xl border p-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
              <h2 className="text-lg font-semibold mb-4" style={{ fontFamily: 'var(--font-heading)', color: 'var(--primary-dark)' }}>
                Rating Distribution
              </h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={ratingData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="var(--primary-brown)" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* RIGHT: Interactive Data Table */}
          <div className="space-y-6 animate-fadeIn" style={{ animationDelay: '0.1s' }}>
            {/* All Brews Table with CRUD actions */}
            <div className="rounded-xl border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
              <div className="p-6 border-b flex items-center justify-between" style={{ borderColor: 'var(--border-color)' }}>
                <h2 className="text-lg font-semibold" style={{ fontFamily: 'var(--font-heading)', color: 'var(--primary-dark)' }}>
                  All Brews
                </h2>
                <span className="text-xs px-3 py-1 rounded-full" style={{ backgroundColor: 'var(--cream)', color: 'var(--text-muted)' }}>
                  {totalBrews} entries
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr style={{ backgroundColor: 'var(--background)' }}>
                      <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Bean</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Method</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Rating</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Taste</th>
                      <th className="w-20"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {brews.map(brew => (
                      <tr key={brew.id} className="border-t transition-colors hover:opacity-80" style={{ borderColor: 'var(--border-color)' }}>
                        <td className="px-4 py-3 text-sm font-medium" style={{ color: 'var(--foreground)' }}>
                          <Link to={`/brew/${brew.id}`} className="hover:underline" style={{ color: 'var(--foreground)' }}>
                            {brew.bean}
                          </Link>
                          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                            {new Date(brew.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </p>
                        </td>
                        <td className="px-4 py-3 text-sm" style={{ color: 'var(--text-muted)' }}>{brew.method}</td>
                        <td className="px-4 py-3"><StarRating rating={brew.rating} size={14} /></td>
                        <td className="px-4 py-3"><TasteBadge taste={brew.taste} /></td>
                        <td className="px-4 py-3">
                          <div className="flex gap-2 items-center justify-end">
                            <Link to={`/brew/${brew.id}/edit`} className="hover:opacity-70 transition-opacity" style={{ color: 'var(--text-muted)' }}>
                              <Pencil size={14} />
                            </Link>
                            <button
                              onClick={() => setDeleteTarget(brew.id)}
                              className="hover:opacity-70 transition-opacity"
                              style={{ color: 'var(--red)' }}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Bean Rankings */}
            <div className="rounded-xl border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
              <div className="p-6 border-b" style={{ borderColor: 'var(--border-color)' }}>
                <h2 className="text-lg font-semibold" style={{ fontFamily: 'var(--font-heading)', color: 'var(--primary-dark)' }}>
                  Bean Rankings
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr style={{ backgroundColor: 'var(--background)' }}>
                      <th className="text-center px-4 py-3 text-xs font-semibold uppercase tracking-wide w-12" style={{ color: 'var(--text-muted)' }}>#</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Bean</th>
                      <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Brews</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(beanCounts).sort((a, b) => b[1] - a[1]).map(([bean, count], index) => (
                      <tr key={bean} className="border-t" style={{ borderColor: 'var(--border-color)' }}>
                        <td className="px-4 py-3 text-center text-lg">
                          {index === 0 && '🥇'}{index === 1 && '🥈'}{index === 2 && '🥉'}
                          {index > 2 && <span className="text-sm font-bold" style={{ color: 'var(--text-muted)' }}>{index + 1}</span>}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium" style={{ color: 'var(--foreground)' }}>{bean}</td>
                        <td className="px-4 py-3 text-sm text-right" style={{ color: 'var(--foreground)' }}>{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        {/* Brew DNA — full width below */}
        <div className="rounded-xl p-6 sm:p-8 text-white animate-fadeIn" style={{ background: 'linear-gradient(135deg, var(--primary-brown), var(--primary-dark))', animationDelay: '0.2s' }}>
          <div className="flex items-center gap-3 mb-6">
            <BarChart3 size={28} />
            <div>
              <h2 className="text-2xl font-bold" style={{ fontFamily: 'var(--font-heading)', color: '#fff' }}>
                Brew DNA
              </h2>
              <p className="text-sm text-white/80">
                Unique fingerprint of each brew's parameters
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            {brews.slice(0, 4).map((brew) => (
              <button
                key={brew.id}
                onClick={() => setSelectedBrewDNA(brew.id)}
                className={`p-4 rounded-lg transition-all ${
                  selectedBrewDNA === brew.id
                    ? 'bg-white shadow-lg'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
                style={{ color: selectedBrewDNA === brew.id ? 'var(--primary-brown)' : '#fff' }}
              >
                <p className="font-semibold text-sm mb-1">{brew.bean}</p>
                <p className="text-xs opacity-80">{brew.method}</p>
              </button>
            ))}
          </div>

          {selectedBrewDNA && brews.find(b => b.id === selectedBrewDNA) && (
            <div className="bg-white/10 backdrop-blur rounded-lg p-6">
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={generateBrewDNA(brews.find(b => b.id === selectedBrewDNA)!)}>
                  <PolarGrid stroke="white" strokeOpacity={0.3} />
                  <PolarAngleAxis dataKey="parameter" stroke="white" fontSize={12} />
                  <PolarRadiusAxis stroke="white" strokeOpacity={0.3} />
                  <Radar name="Brew DNA" dataKey="value" stroke="#E9B949" fill="#E9B949" fillOpacity={0.6} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#2D2017', border: 'none', borderRadius: '8px', color: 'white' }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
      />
    </div>
  )
}
