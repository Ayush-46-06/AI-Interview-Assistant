import { useSettingsStore } from '../store/settingsStore'
import AppLayout from '../components/AppLayout'

export default function SettingsPage(): React.JSX.Element {
  const { settings, update, isSaving, error } = useSettingsStore()

  async function handleScreenInvisibilityToggle() {
    const enabling = !settings.screen_invisibility_enabled

    if (enabling && !settings.disclaimer_accepted) {
      // Must accept disclaimer before enabling
      const confirmed = window.confirm(
        'Screen invisibility hides this window from screen capture tools.\n\n' +
        'Use this ethically and only in permitted environments. ' +
        'By continuing, you accept this disclaimer.\n\nEnable screen invisibility?'
      )
      if (!confirmed) return
      await update({
        screen_invisibility_enabled: true,
        disclaimer_accepted: true
      })
    } else {
      await update({ screen_invisibility_enabled: enabling })
    }
  }

  return (
    <AppLayout>
      <div className="p-8 max-w-xl">
        <h1 className="text-2xl font-semibold text-white mb-6">Settings</h1>

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 text-sm px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm font-medium">Screen Invisibility</p>
                <p className="text-gray-400 text-xs mt-0.5">
                  Hides this window from screen capture and recording tools.
                </p>
              </div>
              <button
                onClick={handleScreenInvisibilityToggle}
                disabled={isSaving}
                className={`relative w-10 h-6 rounded-full transition-colors focus:outline-none ${
                  settings.screen_invisibility_enabled ? 'bg-blue-600' : 'bg-gray-700'
                } disabled:opacity-50`}
              >
                <span
                  className={`block w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                    settings.screen_invisibility_enabled ? 'translate-x-5' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            {settings.screen_invisibility_enabled && (
              <p className="text-amber-400 text-xs mt-2">
                ⚠ Screen invisibility is enabled. Native OS integration implemented in Phase 3.
              </p>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
