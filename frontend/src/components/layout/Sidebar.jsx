import { Link, useLocation, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Settings, FileText, LogOut } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

const menuItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

function Sidebar({ onNavigate }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
    if (onNavigate) onNavigate()
  }

  return (
    <div className="w-56 h-screen bg-dark-card border-r border-dark-border flex flex-col">
      {/* 로고 */}
      <div className="p-4 border-b border-dark-border">
        <Link to="/" onClick={onNavigate} className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-semibold text-white">PhotoScript</span>
        </Link>
      </div>

      {/* 메뉴 */}
      <nav className="flex-1 p-2">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path
          const Icon = item.icon

          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={onNavigate}
              className={`
                flex items-center gap-3 px-3 py-2 rounded-lg mb-1
                transition-colors duration-200
                ${isActive
                  ? 'bg-primary text-white'
                  : 'text-gray-400 hover:bg-dark-hover hover:text-white'
                }
              `}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm">{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* 로그아웃 버튼 */}
      <div className="p-4 border-t border-dark-border">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg w-full text-gray-400 hover:bg-dark-hover hover:text-white transition-colors duration-200"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-sm">Logout</span>
        </button>
      </div>
    </div>
  )
}

export default Sidebar
