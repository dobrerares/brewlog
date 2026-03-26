import { AlertTriangle, X } from 'lucide-react'

interface DeleteConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title?: string
  message?: string
}

export function DeleteConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title = 'Delete brew log?',
  message = 'This action cannot be undone. This brew log will be permanently deleted from your history.'
}: DeleteConfirmModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fadeIn">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 animate-fadeIn"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative rounded-xl shadow-lg max-w-md w-full mx-4 p-8 animate-scaleIn"
        style={{ backgroundColor: 'var(--card)' }}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 transition-colors"
          style={{ color: 'var(--text-muted)' }}
        >
          <X size={20} />
        </button>

        <div className="flex items-start gap-4 mb-6">
          <div className="flex-shrink-0 w-12 h-12 rounded-full bg-[#FEF3F2] flex items-center justify-center">
            <AlertTriangle size={24} className="text-[#D92D20]" />
          </div>
          <div>
            <h2 className="text-xl font-semibold mb-2" style={{ fontFamily: 'var(--font-heading)', color: 'var(--foreground)' }}>
              {title}
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
              {message}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-lg transition-colors border font-medium"
            style={{
              backgroundColor: 'var(--card)',
              color: 'var(--primary-brown)',
              borderColor: 'var(--border-color)'
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-5 py-2.5 bg-[#D92D20] text-white rounded-lg hover:bg-[#B42318] transition-colors font-medium"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
