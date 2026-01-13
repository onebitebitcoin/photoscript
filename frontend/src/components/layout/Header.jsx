import { useLocation } from 'react-router-dom'
import { Menu, Search, User } from 'lucide-react'

function Header() {
  const location = useLocation()

  // 페이지별 타이틀
  const getTitle = () => {
    if (location.pathname === '/') return 'Script Editor'
    if (location.pathname.startsWith('/project/')) return 'Project'
    return 'PhotoScript'
  }

  return (
    <header className="h-14 bg-dark-card border-b border-dark-border flex items-center justify-between px-4">
      {/* 왼쪽: 모바일 메뉴 + 타이틀 */}
      <div className="flex items-center gap-3">
        <button className="md:hidden p-2 text-gray-400 hover:text-white">
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-lg font-medium text-white">{getTitle()}</h1>
      </div>

      {/* 오른쪽: 검색 + 프로필 */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-2 bg-dark-bg border border-dark-border rounded-lg px-3 py-1.5">
          <Search className="w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search scripts..."
            className="bg-transparent text-sm text-white placeholder-gray-500 outline-none w-40"
          />
        </div>
        <button className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-dark-hover">
          <User className="w-5 h-5" />
        </button>
      </div>
    </header>
  )
}

export default Header
