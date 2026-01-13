import Sidebar from './Sidebar'
import Header from './Header'

function Layout({ children }) {
  return (
    <div className="flex min-h-screen bg-dark-bg">
      {/* 사이드바 - 모바일에서는 숨김 */}
      <aside className="hidden md:flex">
        <Sidebar />
      </aside>

      {/* 메인 콘텐츠 */}
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout
