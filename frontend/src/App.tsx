import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Honeypots from './pages/Honeypots'
import Attacks from './pages/Attacks'
import Settings from './pages/Settings'
import AIMonitor from './pages/AIMonitor'
import CognitiveDashboard from './pages/CognitiveDashboard'
import Login from './pages/Login'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, token, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    )
  }

  if (!user || !token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  const { user, token } = useAuth()

  return (
    <Routes>
      <Route 
        path="/login" 
        element={user && token ? <Navigate to="/" replace /> : <Login />} 
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/honeypots"
        element={
          <ProtectedRoute>
            <Layout>
              <Honeypots />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/attacks"
        element={
          <ProtectedRoute>
            <Layout>
              <Attacks />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-monitor"
        element={
          <ProtectedRoute>
            <Layout>
              <AIMonitor />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/cognitive"
        element={
          <ProtectedRoute>
            <Layout>
              <CognitiveDashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Layout>
              <Settings />
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App