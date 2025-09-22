// App shell: header + theme toggle + Todo page
import TodoPage from './pages/TodoPage.jsx'
import ThemeToggle from './components/ThemeToggle.jsx'

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Simple header with brand color and theme toggle */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200/70 dark:border-gray-800/70 bg-white/60 dark:bg-charcoal/60 backdrop-blur">
        <h1 className="text-xl font-semibold tracking-tight">
          <span className="text-accent">Todo</span> App
        </h1>
        <ThemeToggle />
      </header>
      {/* Main content renders the Todo page */}
      <main className="flex-1">
        <TodoPage />
      </main>
    </div>
  )
}

export default App
