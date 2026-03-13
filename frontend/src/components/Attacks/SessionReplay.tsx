import { useState, useEffect, useRef, useCallback } from 'react'
import { Play, Pause, SkipForward, SkipBack, RotateCcw, Terminal, Clock, Globe, Server } from 'lucide-react'
import { Session, SessionCommand } from '../../hooks/useApi'
import { format, formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

interface SessionReplayProps {
  session: Session | null
  isLoading?: boolean
}

function SessionReplay({ session, isLoading }: SessionReplayProps) {
  const [currentCommandIndex, setCurrentCommandIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [displayedCommands, setDisplayedCommands] = useState<SessionCommand[]>([])
  const terminalRef = useRef<HTMLDivElement>(null)
  const playIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const commands = session?.commands || []

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [displayedCommands])

  // Playback control
  const stopPlayback = useCallback(() => {
    if (playIntervalRef.current) {
      clearInterval(playIntervalRef.current)
      playIntervalRef.current = null
    }
    setIsPlaying(false)
  }, [])

  const startPlayback = useCallback(() => {
    if (commands.length === 0) return

    setIsPlaying(true)
    playIntervalRef.current = setInterval(() => {
      setCurrentCommandIndex((prev) => {
        const next = prev + 1
        if (next >= commands.length) {
          stopPlayback()
          return prev
        }
        return next
      })
    }, 1000 / playbackSpeed)
  }, [commands.length, playbackSpeed, stopPlayback])

  useEffect(() => {
    if (isPlaying) {
      stopPlayback()
      startPlayback()
    }
    return () => {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current)
      }
    }
  }, [playbackSpeed, isPlaying, startPlayback, stopPlayback])

  // Update displayed commands
  useEffect(() => {
    setDisplayedCommands(commands.slice(0, currentCommandIndex + 1))
  }, [currentCommandIndex, commands])

  // Reset on session change
  useEffect(() => {
    setCurrentCommandIndex(0)
    setDisplayedCommands([])
    stopPlayback()
  }, [session?.id, stopPlayback])

  const handlePlayPause = () => {
    if (isPlaying) {
      stopPlayback()
    } else {
      if (currentCommandIndex >= commands.length - 1) {
        setCurrentCommandIndex(0)
      }
      startPlayback()
    }
  }

  const handleReset = () => {
    stopPlayback()
    setCurrentCommandIndex(0)
    setDisplayedCommands([])
  }

  const handleNext = () => {
    stopPlayback()
    setCurrentCommandIndex((prev) => Math.min(prev + 1, commands.length - 1))
  }

  const handlePrev = () => {
    stopPlayback()
    setCurrentCommandIndex((prev) => Math.max(prev - 1, 0))
  }

  if (isLoading) {
    return (
      <div className="card h-full">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-dark-700 rounded" />
          <div className="h-64 w-full bg-dark-700 rounded" />
        </div>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="card h-full flex items-center justify-center">
        <div className="text-center text-dark-400">
          <Terminal className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>Select a session to replay</p>
          <p className="text-sm mt-1">Session replay will appear here</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-dark-100">Session Replay</h3>
          <p className="text-sm text-dark-400">
            Session ID: <span className="font-mono">{session.id.slice(0, 8)}...</span>
          </p>
        </div>

        <div className="flex items-center gap-4 text-sm text-dark-400">
          <span className="flex items-center gap-1">
            <Globe className="w-4 h-4" />
            {session.source_ip}
          </span>
          <span className="flex items-center gap-1">
            <Server className="w-4 h-4" />
            {session.protocol}
          </span>
        </div>
      </div>

      {/* Session Info */}
      <div className="grid grid-cols-4 gap-4 mb-4 p-3 bg-dark-800/50 rounded-lg">
        <div>
          <p className="text-xs text-dark-400">Started</p>
          <p className="text-sm text-dark-200">
            {format(new Date(session.started_at), 'HH:mm:ss')}
          </p>
        </div>
        <div>
          <p className="text-xs text-dark-400">Duration</p>
          <p className="text-sm text-dark-200">
            {session.duration ? formatDistanceToNow(new Date(Date.now() - session.duration * 1000)) : 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-xs text-dark-400">Bytes Sent</p>
          <p className="text-sm text-dark-200">{session.bytes_sent.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-dark-400">Bytes Received</p>
          <p className="text-sm text-dark-200">{session.bytes_received.toLocaleString()}</p>
        </div>
      </div>

      {/* Terminal */}
      <div className="terminal flex-1 mb-4">
        <div className="terminal-header">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="w-3 h-3 rounded-full bg-green-500" />
          </div>
          <span className="text-sm text-dark-400 ml-2">Session Terminal</span>
        </div>
        <div ref={terminalRef} className="terminal-body h-64">
          {displayedCommands.length === 0 ? (
            <p className="text-dark-400">Press play to start replay...</p>
          ) : (
            displayedCommands.map((cmd, index) => (
              <div key={index} className="mb-2">
                <div className="flex items-center gap-2 text-cyber-400">
                  <span className="text-dark-500">$</span>
                  <span className="font-mono">{cmd.command}</span>
                </div>
                {cmd.response && (
                  <pre className="mt-1 pl-4 text-dark-300 font-mono text-sm whitespace-pre-wrap">
                    {cmd.response}
                  </pre>
                )}
              </div>
            ))
          )}
          {isPlaying && (
            <span className="inline-block w-2 h-4 bg-cyber-400 animate-pulse" />
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="p-2 rounded-lg hover:bg-dark-700 text-dark-300 hover:text-dark-100 transition-colors"
            title="Reset"
          >
            <RotateCcw className="w-5 h-5" />
          </button>

          <button
            onClick={handlePrev}
            disabled={currentCommandIndex === 0}
            className="p-2 rounded-lg hover:bg-dark-700 text-dark-300 hover:text-dark-100 transition-colors disabled:opacity-50"
            title="Previous"
          >
            <SkipBack className="w-5 h-5" />
          </button>

          <button
            onClick={handlePlayPause}
            disabled={commands.length === 0}
            className={clsx(
              'p-3 rounded-lg transition-colors',
              isPlaying
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'bg-cyber-500/20 text-cyber-400 hover:bg-cyber-500/30'
            )}
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          </button>

          <button
            onClick={handleNext}
            disabled={currentCommandIndex >= commands.length - 1}
            className="p-2 rounded-lg hover:bg-dark-700 text-dark-300 hover:text-dark-100 transition-colors disabled:opacity-50"
            title="Next"
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-dark-400">Speed:</span>
            <select
              value={playbackSpeed}
              onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
              className="input py-1 px-2 text-sm"
            >
              <option value="0.5">0.5x</option>
              <option value="1">1x</option>
              <option value="2">2x</option>
              <option value="4">4x</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-dark-400" />
            <span className="text-sm text-dark-300">
              {currentCommandIndex + 1} / {commands.length} commands
            </span>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-4 h-1 bg-dark-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-cyber-500 transition-all"
          style={{ width: `${((currentCommandIndex + 1) / commands.length) * 100}%` }}
        />
      </div>
    </div>
  )
}

export default SessionReplay