import { Sun, Moon } from 'lucide-react'
import { useAppStore } from '../stores/appStore'
import clsx from 'clsx'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useAppStore()

  return (
    <button
      onClick={toggleTheme}
      className={clsx(
        'p-2.5 rounded-xl transition-all duration-200',
        'border hover:scale-105 active:scale-95',
        theme === 'dark' 
          ? 'bg-slate-800/50 border-slate-700/50 text-slate-300 hover:bg-slate-700/50 hover:text-yellow-400'
          : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200 hover:text-amber-500'
      )}
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark' ? (
        <Sun className="w-5 h-5 transition-transform hover:rotate-45" />
      ) : (
        <Moon className="w-5 h-5 transition-transform hover:-rotate-12" />
      )}
    </button>
  )
}

// Alternative: Dropdown theme selector
export function ThemeSelector() {
  const { theme, setTheme } = useAppStore()

  return (
    <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-800/50 border border-slate-700/50">
      <button
        onClick={() => setTheme('light')}
        className={clsx(
          'p-2 rounded-md transition-all',
          theme === 'light' 
            ? 'bg-white text-slate-900 shadow-sm' 
            : 'text-slate-400 hover:text-white'
        )}
        title="Light mode"
        aria-label="Light mode"
      >
        <Sun className="w-4 h-4" />
      </button>
      <button
        onClick={() => setTheme('dark')}
        className={clsx(
          'p-2 rounded-md transition-all',
          theme === 'dark' 
            ? 'bg-slate-700 text-white shadow-sm' 
            : 'text-slate-400 hover:text-white'
        )}
        title="Dark mode"
        aria-label="Dark mode"
      >
        <Moon className="w-4 h-4" />
      </button>
    </div>
  )
}
