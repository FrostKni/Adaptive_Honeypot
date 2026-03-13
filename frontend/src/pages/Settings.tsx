import { useState, useEffect } from 'react'
import {
  Settings as SettingsIcon,
  Bell,
  Shield,
  Database,
  Globe,
  Save,
  RotateCcw,
  Key,
  Server,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Cpu,
  HardDrive,
  MemoryStick,
  Clock,
  Container,
  Send,
  Eye,
  EyeOff,
  Brain,
  Sparkles,
  Zap,
} from 'lucide-react'
import clsx from 'clsx'
import {
  useSettings,
  useUpdateSettings,
  useSystemStatus,
  useResetSettings,
  useChangePassword,
  useTestWebhook,
  useTestAIProvider,
  type UserSettings,
  type AIProviderConfig,
} from '../hooks/useApi'

function Settings() {
  // API hooks
  const { data: savedSettings, isLoading } = useSettings()
  const { data: systemStatus } = useSystemStatus()
  const updateSettings = useUpdateSettings()
  const resetSettings = useResetSettings()
  const changePassword = useChangePassword()
  const testWebhook = useTestWebhook()

  // Local state for editing
  const [settings, setSettings] = useState<UserSettings>({
    notifications: {
      emailAlerts: true,
      criticalAlerts: true,
      dailyDigest: false,
      slackWebhook: '',
    },
    security: {
      autoAdaptation: true,
      maxHoneypots: 10,
      sessionTimeout: 30,
      blockMaliciousIPs: true,
    },
    display: {
      theme: 'dark',
      compactView: false,
      autoRefresh: true,
      refreshInterval: 10,
    },
    api: {
      apiKey: '',
      apiEndpoint: 'http://localhost:8000/api/v1',
      wsEndpoint: 'ws://localhost:8000/api/v1/ws',
    },
    ai: {
      activeProvider: 'local',
      local: {
        enabled: true,
        apiKey: '',
        baseUrl: 'https://api.ai.oac/v1',
        model: 'DeepSeek',
      },
      openai: {
        enabled: false,
        apiKey: '',
        baseUrl: 'https://api.openai.com/v1',
        model: 'gpt-4-turbo-preview',
      },
      anthropic: {
        enabled: false,
        apiKey: '',
        baseUrl: 'https://api.anthropic.com',
        model: 'claude-3-opus-20240229',
      },
      gemini: {
        enabled: false,
        apiKey: '',
        baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
        model: 'gemini-1.5-pro',
      },
      analysisEnabled: true,
      autoAnalyze: true,
      analysisInterval: 30,
      threatThreshold: 0.6,
    },
  })

  const [saved, setSaved] = useState(false)
  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'security' | 'api' | 'ai'>('general')
  const [showApiKey, setShowApiKey] = useState(false)
  const [webhookTestResult, setWebhookTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [passwordForm, setPasswordForm] = useState({ current: '', new: '', confirm: '' })
  const [passwordError, setPasswordError] = useState('')
  const [aiTestResult, setAiTestResult] = useState<{ provider: string; success: boolean; message: string } | null>(null)
  
  const testAIProvider = useTestAIProvider()

  // Load saved settings into local state
  useEffect(() => {
    if (savedSettings) {
      setSettings(savedSettings)
    }
  }, [savedSettings])

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(settings)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
  }

  const handleReset = async () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      try {
        const defaults = await resetSettings.mutateAsync()
        setSettings(defaults)
        setSaved(true)
        setTimeout(() => setSaved(false), 3000)
      } catch (error) {
        console.error('Failed to reset settings:', error)
      }
    }
  }

  const handleTestWebhook = async () => {
    if (!settings.notifications.slackWebhook) {
      setWebhookTestResult({ success: false, message: 'Please enter a webhook URL first' })
      return
    }
    try {
      const result = await testWebhook.mutateAsync(settings.notifications.slackWebhook)
      setWebhookTestResult(result)
      setTimeout(() => setWebhookTestResult(null), 5000)
    } catch (error) {
      setWebhookTestResult({ success: false, message: 'Failed to test webhook' })
    }
  }

  const handleChangePassword = async () => {
    setPasswordError('')
    
    if (!passwordForm.current || !passwordForm.new || !passwordForm.confirm) {
      setPasswordError('All fields are required')
      return
    }
    
    if (passwordForm.new !== passwordForm.confirm) {
      setPasswordError('New passwords do not match')
      return
    }
    
    if (passwordForm.new.length < 6) {
      setPasswordError('Password must be at least 6 characters')
      return
    }

    try {
      await changePassword.mutateAsync({
        currentPassword: passwordForm.current,
        newPassword: passwordForm.new,
      })
      setPasswordForm({ current: '', new: '', confirm: '' })
      alert('Password changed successfully!')
    } catch (error: any) {
      setPasswordError(error?.message || 'Failed to change password')
    }
  }

  const tabs = [
    { id: 'general', label: 'General', icon: <SettingsIcon className="w-4 h-4" /> },
    { id: 'notifications', label: 'Notifications', icon: <Bell className="w-4 h-4" /> },
    { id: 'security', label: 'Security', icon: <Shield className="w-4 h-4" /> },
    { id: 'api', label: 'API', icon: <Key className="w-4 h-4" /> },
    { id: 'ai', label: 'AI', icon: <Brain className="w-4 h-4" /> },
  ]

  const handleTestAIProvider = async (provider: string) => {
    setAiTestResult(null)
    try {
      const result = await testAIProvider.mutateAsync(provider)
      setAiTestResult({ provider, ...result })
      setTimeout(() => setAiTestResult(null), 5000)
    } catch (error) {
      setAiTestResult({ provider, success: false, message: 'Failed to test provider' })
    }
  }

  const updateAIProvider = (provider: 'local' | 'openai' | 'anthropic' | 'gemini', config: Partial<AIProviderConfig>) => {
    setSettings({
      ...settings,
      ai: {
        ...settings.ai,
        [provider]: { ...settings.ai[provider], ...config },
      },
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-cyber-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-100">Settings</h1>
          <p className="text-dark-400">Manage your honeypot system configuration</p>
        </div>
        <div className="flex items-center gap-3">
          {saved && (
            <div className="flex items-center gap-2 text-green-400 animate-fade-in">
              <CheckCircle className="w-5 h-5" />
              <span>Saved successfully</span>
            </div>
          )}
          <button onClick={handleReset} className="btn-secondary flex items-center gap-2" disabled={resetSettings.isPending}>
            {resetSettings.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
            Reset
          </button>
          <button onClick={handleSave} className="btn-primary flex items-center gap-2" disabled={updateSettings.isPending}>
            {updateSettings.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Changes
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-700 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors',
              activeTab === tab.id
                ? 'bg-dark-800 text-cyber-400 border-b-2 border-cyber-400'
                : 'text-dark-400 hover:text-dark-100 hover:bg-dark-800/50'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {/* General Settings */}
          {activeTab === 'general' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-dark-100 mb-6">Display Settings</h2>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-dark-200">Compact View</p>
                    <p className="text-sm text-dark-400">Reduce spacing in tables and cards</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.display.compactView}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          display: { ...settings.display, compactView: e.target.checked },
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-dark-200">Auto Refresh</p>
                    <p className="text-sm text-dark-400">Automatically refresh data</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.display.autoRefresh}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          display: { ...settings.display, autoRefresh: e.target.checked },
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                  </label>
                </div>

                <div>
                  <label className="block font-medium text-dark-200 mb-2">
                    Refresh Interval (seconds)
                  </label>
                  <input
                    type="number"
                    value={settings.display.refreshInterval}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        display: { ...settings.display, refreshInterval: parseInt(e.target.value) || 10 },
                      })
                    }
                    className="input w-32"
                    min={5}
                    max={60}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Notification Settings */}
          {activeTab === 'notifications' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-dark-100 mb-6">Notification Settings</h2>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-dark-200">Email Alerts</p>
                    <p className="text-sm text-dark-400">Receive attack notifications via email</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notifications.emailAlerts}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          notifications: { ...settings.notifications, emailAlerts: e.target.checked },
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-dark-200">Critical Alerts Only</p>
                    <p className="text-sm text-dark-400">Only notify for critical severity attacks</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notifications.criticalAlerts}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          notifications: { ...settings.notifications, criticalAlerts: e.target.checked },
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-dark-200">Daily Digest</p>
                    <p className="text-sm text-dark-400">Receive daily summary of activity</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notifications.dailyDigest}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          notifications: { ...settings.notifications, dailyDigest: e.target.checked },
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                  </label>
                </div>

                <div>
                  <label className="block font-medium text-dark-200 mb-2">Slack Webhook URL</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={settings.notifications.slackWebhook}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          notifications: { ...settings.notifications, slackWebhook: e.target.value },
                        })
                      }
                      placeholder="https://hooks.slack.com/services/..."
                      className="input flex-1"
                    />
                    <button
                      onClick={handleTestWebhook}
                      disabled={testWebhook.isPending}
                      className="btn-secondary flex items-center gap-2"
                    >
                      {testWebhook.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                      Test
                    </button>
                  </div>
                  {webhookTestResult && (
                    <p className={clsx('mt-2 text-sm', webhookTestResult.success ? 'text-green-400' : 'text-red-400')}>
                      {webhookTestResult.message}
                    </p>
                  )}
                </div>

                {/* Test Notification */}
                <div className="pt-4 border-t border-dark-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-dark-200">Test Notifications</p>
                      <p className="text-sm text-dark-400">Send a test notification to verify the system</p>
                    </div>
                    <button
                      onClick={() => {
                        // Trigger test notification via custom event
                        window.dispatchEvent(new CustomEvent('test-notification'))
                      }}
                      className="btn-primary flex items-center gap-2"
                    >
                      <Bell className="w-4 h-4" />
                      Test Notification
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Security Settings */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="card">
                <h2 className="text-lg font-semibold text-dark-100 mb-6">Security Settings</h2>
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-dark-200">Auto Adaptation</p>
                      <p className="text-sm text-dark-400">Allow system to automatically adapt defenses</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.security.autoAdaptation}
                        onChange={(e) =>
                          setSettings({
                            ...settings,
                            security: { ...settings.security, autoAdaptation: e.target.checked },
                          })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-dark-200">Block Malicious IPs</p>
                      <p className="text-sm text-dark-400">Automatically block known malicious IPs</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.security.blockMaliciousIPs}
                        onChange={(e) =>
                          setSettings({
                            ...settings,
                            security: { ...settings.security, blockMaliciousIPs: e.target.checked },
                          })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                    </label>
                  </div>

                  <div>
                    <label className="block font-medium text-dark-200 mb-2">Maximum Honeypots</label>
                    <input
                      type="number"
                      value={settings.security.maxHoneypots}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          security: { ...settings.security, maxHoneypots: parseInt(e.target.value) || 10 },
                        })
                      }
                      className="input w-32"
                      min={1}
                      max={100}
                    />
                  </div>

                  <div>
                    <label className="block font-medium text-dark-200 mb-2">
                      Session Timeout (minutes)
                    </label>
                    <input
                      type="number"
                      value={settings.security.sessionTimeout}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          security: { ...settings.security, sessionTimeout: parseInt(e.target.value) || 30 },
                        })
                      }
                      className="input w-32"
                      min={5}
                      max={120}
                    />
                  </div>
                </div>
              </div>

              {/* Password Change */}
              <div className="card">
                <h2 className="text-lg font-semibold text-dark-100 mb-6">Change Password</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block font-medium text-dark-200 mb-2">Current Password</label>
                    <input
                      type="password"
                      value={passwordForm.current}
                      onChange={(e) => setPasswordForm({ ...passwordForm, current: e.target.value })}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-dark-200 mb-2">New Password</label>
                    <input
                      type="password"
                      value={passwordForm.new}
                      onChange={(e) => setPasswordForm({ ...passwordForm, new: e.target.value })}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-dark-200 mb-2">Confirm New Password</label>
                    <input
                      type="password"
                      value={passwordForm.confirm}
                      onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                      className="input"
                    />
                  </div>
                  {passwordError && (
                    <p className="text-sm text-red-400">{passwordError}</p>
                  )}
                  <button
                    onClick={handleChangePassword}
                    disabled={changePassword.isPending}
                    className="btn-primary flex items-center gap-2"
                  >
                    {changePassword.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
                    Change Password
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* API Settings */}
          {activeTab === 'api' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-dark-100 mb-6">API Configuration</h2>
              <div className="space-y-6">
                <div>
                  <label className="block font-medium text-dark-200 mb-2">API Key</label>
                  <div className="relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      value={settings.api.apiKey}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          api: { ...settings.api, apiKey: e.target.value },
                        })
                      }
                      placeholder="Enter your API key"
                      className="input pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-200"
                    >
                      {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-dark-200 mb-2">API Endpoint</label>
                  <input
                    type="text"
                    value={settings.api.apiEndpoint}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        api: { ...settings.api, apiEndpoint: e.target.value },
                      })
                    }
                    className="input font-mono"
                  />
                </div>

                <div>
                  <label className="block font-medium text-dark-200 mb-2">WebSocket Endpoint</label>
                  <input
                    type="text"
                    value={settings.api.wsEndpoint}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        api: { ...settings.api, wsEndpoint: e.target.value },
                      })
                    }
                    className="input font-mono"
                  />
                </div>
              </div>
            </div>
          )}

          {/* AI Settings */}
          {activeTab === 'ai' && (
            <div className="space-y-6">
              {/* AI Analysis Settings */}
              <div className="card">
                <div className="flex items-center gap-2 mb-6">
                  <Sparkles className="w-5 h-5 text-cyber-400" />
                  <h2 className="text-lg font-semibold text-dark-100">AI Analysis Settings</h2>
                </div>
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-dark-200">Enable AI Analysis</p>
                      <p className="text-sm text-dark-400">Use AI to analyze attack patterns</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.ai.analysisEnabled}
                        onChange={(e) =>
                          setSettings({
                            ...settings,
                            ai: { ...settings.ai, analysisEnabled: e.target.checked },
                          })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-dark-200">Auto-Analyze Attacks</p>
                      <p className="text-sm text-dark-400">Automatically analyze new attack sessions</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.ai.autoAnalyze}
                        onChange={(e) =>
                          setSettings({
                            ...settings,
                            ai: { ...settings.ai, autoAnalyze: e.target.checked },
                          })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                    </label>
                  </div>

                  <div>
                    <label className="block font-medium text-dark-200 mb-2">
                      Analysis Interval (seconds)
                    </label>
                    <input
                      type="number"
                      value={settings.ai.analysisInterval}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          ai: { ...settings.ai, analysisInterval: parseInt(e.target.value) || 30 },
                        })
                      }
                      className="input w-32"
                      min={10}
                      max={300}
                    />
                  </div>

                  <div>
                    <label className="block font-medium text-dark-200 mb-2">
                      Threat Threshold (0.0 - 1.0)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={settings.ai.threatThreshold}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          ai: { ...settings.ai, threatThreshold: parseFloat(e.target.value) || 0.6 },
                        })
                      }
                      className="input w-32"
                      min={0}
                      max={1}
                    />
                    <p className="text-sm text-dark-400 mt-1">Minimum threat score to trigger alerts</p>
                  </div>
                </div>
              </div>

              {/* Active Provider */}
              <div className="card">
                <div className="flex items-center gap-2 mb-6">
                  <Zap className="w-5 h-5 text-yellow-400" />
                  <h2 className="text-lg font-semibold text-dark-100">Active AI Provider</h2>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {(['local', 'openai', 'anthropic', 'gemini'] as const).map((provider) => (
                    <button
                      key={provider}
                      onClick={() =>
                        setSettings({
                          ...settings,
                          ai: { ...settings.ai, activeProvider: provider },
                        })
                      }
                      className={clsx(
                        'p-3 rounded-lg border transition-all text-center',
                        settings.ai.activeProvider === provider
                          ? 'border-cyber-500 bg-cyber-500/10 text-cyber-400'
                          : 'border-dark-600 bg-dark-800 text-dark-300 hover:border-dark-500'
                      )}
                    >
                      <span className="capitalize font-medium">{provider}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Provider Configs */}
              {(['local', 'openai', 'anthropic', 'gemini'] as const).map((provider) => (
                <div key={provider} className="card">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                      <Brain className="w-5 h-5 text-cyber-400" />
                      <h2 className="text-lg font-semibold text-dark-100 capitalize">{provider} Configuration</h2>
                    </div>
                    <div className="flex items-center gap-3">
                      {aiTestResult?.provider === provider && (
                        <span className={clsx('text-sm', aiTestResult.success ? 'text-green-400' : 'text-red-400')}>
                          {aiTestResult.message}
                        </span>
                      )}
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={settings.ai[provider].enabled}
                          onChange={(e) => updateAIProvider(provider, { enabled: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyber-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyber-500"></div>
                      </label>
                    </div>
                  </div>
                  
                  {settings.ai[provider].enabled && (
                    <div className="space-y-4">
                      <div>
                        <label className="block font-medium text-dark-200 mb-2">Base URL</label>
                        <input
                          type="text"
                          value={settings.ai[provider].baseUrl}
                          onChange={(e) => updateAIProvider(provider, { baseUrl: e.target.value })}
                          className="input font-mono"
                          placeholder="API endpoint URL"
                        />
                      </div>
                      
                      {provider !== 'local' && (
                        <div>
                          <label className="block font-medium text-dark-200 mb-2">API Key</label>
                          <input
                            type="password"
                            value={settings.ai[provider].apiKey}
                            onChange={(e) => updateAIProvider(provider, { apiKey: e.target.value })}
                            className="input"
                            placeholder="Enter API key"
                          />
                        </div>
                      )}
                      
                      <div>
                        <label className="block font-medium text-dark-200 mb-2">Model</label>
                        <input
                          type="text"
                          value={settings.ai[provider].model}
                          onChange={(e) => updateAIProvider(provider, { model: e.target.value })}
                          className="input"
                          placeholder="Model name"
                        />
                      </div>
                      
                      <button
                        onClick={() => handleTestAIProvider(provider)}
                        disabled={testAIProvider.isPending}
                        className="btn-secondary flex items-center gap-2"
                      >
                        {testAIProvider.isPending ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Send className="w-4 h-4" />
                        )}
                        Test Connection
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* System Status */}
          <div className="card">
            <h3 className="text-lg font-semibold text-dark-100 mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-dark-400" />
                  <span className="text-sm text-dark-300">API Server</span>
                </div>
                <span className={clsx(
                  'badge',
                  systemStatus?.apiServer === 'online' ? 'badge-active' : 'badge-inactive'
                )}>
                  {systemStatus?.apiServer || 'Unknown'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-dark-400" />
                  <span className="text-sm text-dark-300">Database</span>
                </div>
                <span className={clsx(
                  'badge',
                  systemStatus?.database === 'connected' ? 'badge-active' : 'badge-inactive'
                )}>
                  {systemStatus?.database || 'Unknown'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-dark-400" />
                  <span className="text-sm text-dark-300">WebSocket</span>
                </div>
                <span className={clsx(
                  'badge',
                  systemStatus?.websocket === 'active' ? 'badge-active' : 'badge-inactive'
                )}>
                  {systemStatus?.websocket || 'Unknown'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Container className="w-4 h-4 text-dark-400" />
                  <span className="text-sm text-dark-300">Containers</span>
                </div>
                <span className="badge badge-active">{systemStatus?.honeypotContainers || 0}</span>
              </div>
            </div>
          </div>

          {/* System Metrics */}
          <div className="card">
            <h3 className="text-lg font-semibold text-dark-100 mb-4">System Metrics</h3>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-300">CPU</span>
                  </div>
                  <span className="text-sm font-medium text-dark-200">{systemStatus?.cpuPercent || 0}%</span>
                </div>
                <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={clsx(
                      'h-full rounded-full transition-all',
                      (systemStatus?.cpuPercent || 0) > 80 ? 'bg-red-500' :
                      (systemStatus?.cpuPercent || 0) > 50 ? 'bg-yellow-500' : 'bg-green-500'
                    )}
                    style={{ width: `${systemStatus?.cpuPercent || 0}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <MemoryStick className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-300">Memory</span>
                  </div>
                  <span className="text-sm font-medium text-dark-200">{systemStatus?.memoryPercent || 0}%</span>
                </div>
                <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={clsx(
                      'h-full rounded-full transition-all',
                      (systemStatus?.memoryPercent || 0) > 80 ? 'bg-red-500' :
                      (systemStatus?.memoryPercent || 0) > 50 ? 'bg-yellow-500' : 'bg-blue-500'
                    )}
                    style={{ width: `${systemStatus?.memoryPercent || 0}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <HardDrive className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-300">Disk</span>
                  </div>
                  <span className="text-sm font-medium text-dark-200">{systemStatus?.diskPercent || 0}%</span>
                </div>
                <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={clsx(
                      'h-full rounded-full transition-all',
                      (systemStatus?.diskPercent || 0) > 80 ? 'bg-red-500' :
                      (systemStatus?.diskPercent || 0) > 50 ? 'bg-yellow-500' : 'bg-purple-500'
                    )}
                    style={{ width: `${systemStatus?.diskPercent || 0}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-dark-700">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-dark-400" />
                  <span className="text-sm text-dark-300">Uptime</span>
                </div>
                <span className="text-sm font-medium text-dark-200">{systemStatus?.uptime || '-'}</span>
              </div>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="card border-red-500/30">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h3 className="text-lg font-semibold text-dark-100">Danger Zone</h3>
            </div>
            <p className="text-sm text-dark-400 mb-4">
              These actions are irreversible. Please proceed with caution.
            </p>
            <div className="space-y-3">
              <button className="w-full btn-secondary text-yellow-400 border-yellow-500/30 hover:bg-yellow-500/10">
                Clear All Sessions
              </button>
              <button className="w-full btn-secondary text-red-400 border-red-500/30 hover:bg-red-500/10">
                Delete All Honeypots
              </button>
              <button className="w-full btn-danger">Reset System</button>
            </div>
          </div>

          {/* Version Info */}
          <div className="card">
            <h3 className="text-sm font-medium text-dark-300 mb-3">Version Information</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-dark-400">Dashboard</span>
                <span className="text-dark-200">v1.0.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">API</span>
                <span className="text-dark-200">v1.0.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Last Updated</span>
                <span className="text-dark-200">{new Date().toISOString().split('T')[0]}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings