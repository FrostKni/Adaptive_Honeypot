import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Honeypots from '../pages/Honeypots'

// Mock react-query hooks
const mockUseQuery = vi.fn()
vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query')
  return {
    ...actual,
    useQuery: () => mockUseQuery(),
    useMutation: () => ({ mutate: vi.fn(), isPending: false }),
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  }
})

const mockHoneypots = {
  items: [
    {
      id: 'test-id-1',
      name: 'SSH Honeypot',
      type: 'ssh',
      port: 2222,
      status: 'running',
      interaction_level: 'high',
      total_sessions: 10,
      total_attacks: 5,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'test-id-2',
      name: 'HTTP Honeypot',
      type: 'http',
      port: 8080,
      status: 'stopped',
      interaction_level: 'medium',
      total_sessions: 5,
      total_attacks: 2,
      created_at: '2024-01-02T00:00:00Z',
    },
  ],
  total: 2,
}

const renderWithProviders = (component: React.ReactNode) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Honeypots Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('token', 'test-token')
  })

  it('renders loading state', () => {
    mockUseQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
    })
    
    renderWithProviders(<Honeypots />)
    
    expect(screen.getByText('Loading honeypots...')).toBeInTheDocument()
  })

  it('renders honeypot list after loading', async () => {
    mockUseQuery.mockReturnValue({
      data: mockHoneypots,
      isLoading: false,
    })
    
    renderWithProviders(<Honeypots />)
    
    expect(screen.getByText('Honeypots')).toBeInTheDocument()
    expect(screen.getByText('Manage your honeypot fleet')).toBeInTheDocument()
  })

  it('renders deploy button', () => {
    mockUseQuery.mockReturnValue({
      data: mockHoneypots,
      isLoading: false,
    })
    
    renderWithProviders(<Honeypots />)
    
    expect(screen.getByText('Deploy Honeypot')).toBeInTheDocument()
  })

  it('opens deploy modal when clicking deploy button', async () => {
    mockUseQuery.mockReturnValue({
      data: mockHoneypots,
      isLoading: false,
    })
    
    renderWithProviders(<Honeypots />)
    
    const deployButton = screen.getByText('Deploy Honeypot')
    fireEvent.click(deployButton)
    
    expect(screen.getByText('Deploy New Honeypot')).toBeInTheDocument()
  })
})
