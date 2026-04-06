import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useToastStore, toast } from '../stores/toastStore'

describe('Toast Store', () => {
  beforeEach(() => {
    // Clear toasts before each test
    useToastStore.setState({ toasts: [] })
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts with empty toasts', () => {
    const { toasts } = useToastStore.getState()
    expect(toasts).toEqual([])
  })

  it('adds a toast', () => {
    const { addToast } = useToastStore.getState()
    
    const id = addToast({ type: 'success', title: 'Test toast' })
    
    const { toasts } = useToastStore.getState()
    expect(toasts).toHaveLength(1)
    expect(toasts[0].title).toBe('Test toast')
    expect(toasts[0].type).toBe('success')
    expect(toasts[0].id).toBe(id)
  })

  it('removes a toast', () => {
    const { addToast, removeToast } = useToastStore.getState()
    
    const id = addToast({ type: 'error', title: 'Error toast' })
    expect(useToastStore.getState().toasts).toHaveLength(1)
    
    removeToast(id)
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('clears all toasts', () => {
    const { addToast, clearAllToasts } = useToastStore.getState()
    
    addToast({ type: 'success', title: 'Toast 1' })
    addToast({ type: 'error', title: 'Toast 2' })
    addToast({ type: 'warning', title: 'Toast 3' })
    
    expect(useToastStore.getState().toasts).toHaveLength(3)
    
    clearAllToasts()
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('auto-removes toast after duration', () => {
    const { addToast } = useToastStore.getState()
    
    addToast({ type: 'info', title: 'Auto-remove toast', duration: 1000 })
    expect(useToastStore.getState().toasts).toHaveLength(1)
    
    vi.advanceTimersByTime(1000)
    
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('does not auto-remove toast when duration is 0', () => {
    const { addToast } = useToastStore.getState()
    
    addToast({ type: 'info', title: 'Persistent toast', duration: 0 })
    expect(useToastStore.getState().toasts).toHaveLength(1)
    
    vi.advanceTimersByTime(10000)
    
    expect(useToastStore.getState().toasts).toHaveLength(1)
  })
})

describe('Toast helper functions', () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] })
  })

  it('creates success toast', () => {
    toast.success('Success!', 'Operation completed')
    
    const { toasts } = useToastStore.getState()
    expect(toasts[0].type).toBe('success')
    expect(toasts[0].title).toBe('Success!')
    expect(toasts[0].message).toBe('Operation completed')
  })

  it('creates error toast', () => {
    toast.error('Error!', 'Something went wrong')
    
    const { toasts } = useToastStore.getState()
    expect(toasts[0].type).toBe('error')
    expect(toasts[0].title).toBe('Error!')
  })

  it('creates warning toast', () => {
    toast.warning('Warning!', 'Check this out')
    
    const { toasts } = useToastStore.getState()
    expect(toasts[0].type).toBe('warning')
    expect(toasts[0].title).toBe('Warning!')
  })

  it('creates info toast', () => {
    toast.info('Info', 'Just so you know')
    
    const { toasts } = useToastStore.getState()
    expect(toasts[0].type).toBe('info')
    expect(toasts[0].title).toBe('Info')
  })
})
