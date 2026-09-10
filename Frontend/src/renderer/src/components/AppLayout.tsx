import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { LayoutDashboard, History, BarChart2, Settings, LogOut, UserCircle } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/context', label: 'Context', icon: UserCircle },
  { to: '/history', label: 'History', icon: History },
  { to: '/analytics', label: 'Analytics', icon: BarChart2 },
  { to: '/settings', label: 'Settings', icon: Settings }
]

export default function AppLayout({ children }: { children: React.ReactNode }): React.JSX.Element {
  const { logout } = useAuthStore()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
      {/* Sidebar */}
      <nav className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col py-6 px-3 shrink-0">
        <p className="text-white font-semibold text-lg px-3 mb-6 tracking-wide">ATHENURA</p>

        <div className="flex-1 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}
