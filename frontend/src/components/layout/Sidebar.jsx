import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, FolderOpen, Settings, Image } from 'lucide-react'

const menuItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/projects', icon: FolderOpen, label: 'Projects' },
  { path: '/assets', icon: Image, label: 'Assets' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-56 bg-dark-card border-r border-dark-border flex flex-col">
      {/* 로고 */}
      <div className="p-4 border-b border-dark-border">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Image className="w-5 h-5 text-white" />
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

      {/* 하단 새 프로젝트 버튼 */}
      <div className="p-4 border-t border-dark-border">
        <Link
          to="/"
          className="flex items-center justify-center gap-2 w-full py-2 px-4 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
        >
          <span className="text-sm">+ New Project</span>
        </Link>
      </div>
    </div>
  )
}

export default Sidebar
