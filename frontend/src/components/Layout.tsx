import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  Cloud,
  LayoutDashboard,
  ArrowLeftRight,
  ScrollText,
  Webhook,
  LogOut,
  ChevronRight,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/jobs', label: 'Sync Jobs', icon: ArrowLeftRight },
  { to: '/audit', label: 'Audit Logs', icon: ScrollText },
  { to: '/webhooks', label: 'Webhooks', icon: Webhook },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="bg-brand-600 p-2 rounded-lg">
              <Cloud className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-white text-sm">CloudMigrate</p>
              <p className="text-xs text-gray-400">Enterprise Gateway</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
              <ChevronRight className="w-3 h-3 ml-auto opacity-50" />
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center text-xs font-bold text-white">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
              <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-xs text-gray-400 hover:text-red-400 transition-colors w-full px-2 py-1.5 rounded hover:bg-gray-800"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-gray-950">
        <Outlet />
      </main>
    </div>
  )
}
