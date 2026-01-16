function Layout({ children }) {
  return (
    <div className="min-h-screen bg-dark-bg">
      <main className="min-h-screen">
        {children}
      </main>
    </div>
  )
}

export default Layout
