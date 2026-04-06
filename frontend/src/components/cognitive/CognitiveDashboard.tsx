/**
 * Cognitive Dashboard - Temporary Simplified Version
 * 
 * A simplified cognitive dashboard using only existing dependencies.
 * Full version available in CognitiveDashboard.tsx.bak (requires MUI + Recharts)
 */

import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, AlertCircle, CheckCircle, Activity } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

// === Types ===

interface DetectedBias {
  bias_type: string;
  confidence: number;
  signals_matched: string[];
  detection_count: number;
}

interface CognitiveProfile {
  session_id: string;
  detected_biases: DetectedBias[];
  engagement_duration?: number;
  effectiveness_score?: number;
}

interface BiasBreakdown {
  bias_type: string;
  count: number;
  avg_confidence: number;
}

// === Bias Colors ===

const BIAS_COLORS: Record<string, string> = {
  confirmation_bias: 'bg-red-500',
  anchoring: 'bg-orange-500',
  sunk_cost: 'bg-yellow-500',
  dunning_kruger: 'bg-green-500',
  curiosity_gap: 'bg-blue-500',
  loss_aversion: 'bg-purple-500',
  availability_heuristic: 'bg-pink-500',
};

const BIAS_LABELS: Record<string, string> = {
  confirmation_bias: 'Confirmation Bias',
  anchoring: 'Anchoring',
  sunk_cost: 'Sunk Cost',
  dunning_kruger: 'Dunning-Kruger',
  curiosity_gap: 'Curiosity Gap',
  loss_aversion: 'Loss Aversion',
  availability_heuristic: 'Availability',
};

// === Main Component ===

const CognitiveDashboard: React.FC = () => {
  const [profiles, setProfiles] = useState<CognitiveProfile[]>([]);
  const [biasBreakdown, setBiasBreakdown] = useState<BiasBreakdown[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCognitiveData();
  }, []);

  const fetchCognitiveData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/cognitive/profiles?limit=50');
      
      if (!response.ok) {
        throw new Error('Failed to fetch cognitive profiles');
      }
      
      const data = await response.json();
      setProfiles(data.profiles || []);
      
      // Calculate bias breakdown
      const biasMap = new Map<string, { count: number; total_confidence: number }>();
      
      data.profiles?.forEach((profile: CognitiveProfile) => {
        profile.detected_biases?.forEach((bias) => {
          const existing = biasMap.get(bias.bias_type) || { count: 0, total_confidence: 0 };
          biasMap.set(bias.bias_type, {
            count: existing.count + 1,
            total_confidence: existing.total_confidence + bias.confidence,
          });
        });
      });
      
      const breakdown = Array.from(biasMap.entries()).map(([bias_type, data]) => ({
        bias_type,
        count: data.count,
        avg_confidence: data.total_confidence / data.count,
      }));
      
      setBiasBreakdown(breakdown.sort((a, b) => b.count - a.count));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <h3 className="text-red-400 font-semibold">Error Loading Cognitive Data</h3>
            </div>
            <p className="text-red-300 mt-2">{error}</p>
            <button
              onClick={fetchCognitiveData}
              className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-white transition"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Chart data
  const biasChartData = {
    labels: biasBreakdown.map(b => BIAS_LABELS[b.bias_type] || b.bias_type),
    datasets: [
      {
        label: 'Detections',
        data: biasBreakdown.map(b => b.count),
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(139, 92, 246, 0.8)',
          'rgba(236, 72, 153, 0.8)',
        ],
        borderColor: [
          'rgba(239, 68, 68, 1)',
          'rgba(249, 115, 22, 1)',
          'rgba(234, 179, 8, 1)',
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(139, 92, 246, 1)',
          'rgba(236, 72, 153, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Cognitive Bias Detections',
        color: '#e2e8f0',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: '#94a3b8' },
        grid: { color: '#334155' },
      },
      x: {
        ticks: { color: '#94a3b8' },
        grid: { color: '#334155' },
      },
    },
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Brain className="w-8 h-8 text-purple-400" />
              Cognitive Dashboard
            </h1>
            <p className="text-slate-400 mt-1">
              Behavioral analysis and cognitive bias detection
            </p>
          </div>
          <button
            onClick={fetchCognitiveData}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition flex items-center gap-2"
          >
            <Activity className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Brain className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Total Profiles</p>
                <p className="text-2xl font-bold text-white">{profiles.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-cyan-500/20 rounded-lg">
                <TrendingUp className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Unique Biases</p>
                <p className="text-2xl font-bold text-white">{biasBreakdown.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Avg Confidence</p>
                <p className="text-2xl font-bold text-white">
                  {biasBreakdown.length > 0
                    ? `${Math.round(
                        (biasBreakdown.reduce((sum, b) => sum + b.avg_confidence, 0) /
                          biasBreakdown.length) *
                          100
                      )}%`
                    : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500/20 rounded-lg">
                <Activity className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Total Detections</p>
                <p className="text-2xl font-bold text-white">
                  {biasBreakdown.reduce((sum, b) => sum + b.count, 0)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bias Distribution Chart */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Bias Distribution</h2>
            {biasBreakdown.length > 0 ? (
              <Bar data={biasChartData} options={chartOptions} />
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-500">
                No bias data available
              </div>
            )}
          </div>

          {/* Recent Profiles */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Recent Profiles</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {profiles.length > 0 ? (
                profiles.slice(0, 10).map((profile) => (
                  <div
                    key={profile.session_id}
                    className="bg-slate-800/50 rounded p-3 border border-slate-700"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-mono text-cyan-400">
                        {profile.session_id.slice(0, 12)}...
                      </span>
                      <span className="text-xs text-slate-500">
                        {profile.detected_biases?.length || 0} biases
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {profile.detected_biases?.slice(0, 3).map((bias, idx) => (
                        <span
                          key={idx}
                          className={`px-2 py-1 text-xs rounded ${
                            BIAS_COLORS[bias.bias_type] || 'bg-gray-500'
                          } text-white`}
                        >
                          {BIAS_LABELS[bias.bias_type] || bias.bias_type}
                        </span>
                      ))}
                      {profile.detected_biases?.length > 3 && (
                        <span className="px-2 py-1 text-xs rounded bg-slate-700 text-slate-300">
                          +{profile.detected_biases.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-slate-500 py-8">
                  No cognitive profiles available
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 mt-0.5" />
            <div>
              <h3 className="text-blue-400 font-semibold">Cognitive-Behavioral Deception Framework</h3>
              <p className="text-blue-300 text-sm mt-1">
                This dashboard visualizes detected cognitive biases in attacker behavior.
                The CBDF uses 8 cognitive biases and 11 deception strategies to extend attacker engagement by 3-4x.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CognitiveDashboard;
