/**
 * Cognitive-Behavioral Deception Framework - Dashboard Components
 * 
 * React components for visualizing cognitive profiles and deception metrics.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Button,
  IconButton,
  Tooltip,
  Badge,
  Alert,
  Stack,
  Divider,
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Timer as TimerIcon,
  Terminal as TerminalIcon,
  Shield as ShieldIcon,
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from 'recharts';

// === Types ===

interface DetectedBias {
  bias_type: string;
  confidence: number;
  signals_matched: string[];
  signal_scores: Record<string, number>;
  detection_count: number;
}

interface MentalModel {
  beliefs: Record<string, any>;
  knowledge: string[];
  goals: string[];
  expectations: Record<string, any>;
  confidence: number;
}

interface CognitiveMetrics {
  overconfidence_score: number;
  persistence_score: number;
  tunnel_vision_score: number;
  curiosity_score: number;
  exploration_diversity: number;
  error_tolerance: number;
  learning_rate: number;
}

interface DeceptionMetrics {
  total_applied: number;
  successful: number;
  success_rate: number;
  suspicion_level: number;
}

interface CognitiveProfile {
  session_id: string;
  detected_biases: DetectedBias[];
  mental_model: MentalModel;
  metrics: CognitiveMetrics;
  deception: DeceptionMetrics;
}

interface Strategy {
  name: string;
  bias_type: string;
  description: string;
  effectiveness_score: number;
  priority: number;
  is_active: boolean;
}

// === Bias Colors ===

const BIAS_COLORS: Record<string, string> = {
  confirmation_bias: '#ef4444',
  anchoring: '#f97316',
  sunk_cost: '#eab308',
  dunning_kruger: '#22c55e',
  curiosity_gap: '#3b82f6',
  loss_aversion: '#8b5cf6',
  availability_heuristic: '#ec4899',
  authority_bias: '#06b6d4',
};

const BIAS_LABELS: Record<string, string> = {
  confirmation_bias: 'Confirmation Bias',
  anchoring: 'Anchoring',
  sunk_cost: 'Sunk Cost',
  dunning_kruger: 'Dunning-Kruger',
  curiosity_gap: 'Curiosity Gap',
  loss_aversion: 'Loss Aversion',
  availability_heuristic: 'Availability',
  authority_bias: 'Authority Bias',
};

// === Cognitive Profile Panel ===

interface CognitiveProfilePanelProps {
  sessionId: string;
  profile?: CognitiveProfile;
  onRefresh?: () => void;
}

export const CognitiveProfilePanel: React.FC<CognitiveProfilePanelProps> = ({
  sessionId,
  profile,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState(0);

  if (!profile) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="center" minHeight={300}>
            <Typography color="text.secondary">
              No cognitive profile available for this session
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        avatar={<PsychologyIcon color="primary" />}
        title="Cognitive Profile"
        subheader={`Session: ${sessionId.slice(0, 8)}...`}
        action={
          onRefresh && (
            <IconButton onClick={onRefresh}>
              <RefreshIcon />
            </IconButton>
          )
        }
      />
      <CardContent>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ mb: 2 }}>
          <Tab label="Biases" />
          <Tab label="Mental Model" />
          <Tab label="Metrics" />
        </Tabs>

        {activeTab === 0 && (
          <BiasesTab biases={profile.detected_biases} />
        )}
        {activeTab === 1 && (
          <MentalModelTab mentalModel={profile.mental_model} />
        )}
        {activeTab === 2 && (
          <MetricsTab metrics={profile.metrics} deception={profile.deception} />
        )}
      </CardContent>
    </Card>
  );
};

// === Biases Tab ===

interface BiasesTabProps {
  biases: DetectedBias[];
}

const BiasesTab: React.FC<BiasesTabProps> = ({ biases }) => {
  const sortedBiases = [...biases].sort((a, b) => b.confidence - a.confidence);

  return (
    <Box>
      {sortedBiases.length === 0 ? (
        <Alert severity="info">No cognitive biases detected yet</Alert>
      ) : (
        <Stack spacing={2}>
          {sortedBiases.map((bias) => (
            <BiasCard key={bias.bias_type} bias={bias} />
          ))}
        </Stack>
      )}
    </Box>
  );
};

interface BiasCardProps {
  bias: DetectedBias;
}

const BiasCard: React.FC<BiasCardProps> = ({ bias }) => {
  const color = BIAS_COLORS[bias.bias_type] || '#6b7280';
  const label = BIAS_LABELS[bias.bias_type] || bias.bias_type;
  const confidencePercent = Math.round(bias.confidence * 100);

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
        <Box display="flex" alignItems="center" gap={1}>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              bgcolor: color,
            }}
          />
          <Typography variant="subtitle1" fontWeight="medium">
            {label}
          </Typography>
        </Box>
        <Chip
          label={`${confidencePercent}%`}
          size="small"
          sx={{
            bgcolor: color,
            color: 'white',
            fontWeight: 'bold',
          }}
        />
      </Box>
      
      <LinearProgress
        variant="determinate"
        value={confidencePercent}
        sx={{
          mb: 1,
          height: 8,
          borderRadius: 4,
          bgcolor: `${color}20`,
          '& .MuiLinearProgress-bar': {
            bgcolor: color,
            borderRadius: 4,
          },
        }}
      />
      
      <Box display="flex" gap={0.5} flexWrap="wrap">
        {bias.signals_matched.slice(0, 3).map((signal) => (
          <Chip
            key={signal}
            label={signal.replace(/_/g, ' ')}
            size="small"
            variant="outlined"
            sx={{ fontSize: '0.7rem' }}
          />
        ))}
        {bias.detection_count > 1 && (
          <Chip
            label={`x${bias.detection_count}`}
            size="small"
            color="primary"
            sx={{ fontSize: '0.7rem' }}
          />
        )}
      </Box>
    </Paper>
  );
};

// === Mental Model Tab ===

interface MentalModelTabProps {
  mentalModel: MentalModel;
}

const MentalModelTab: React.FC<MentalModelTabProps> = ({ mentalModel }) => {
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Beliefs
          </Typography>
          <Stack spacing={1}>
            {Object.entries(mentalModel.beliefs).map(([key, value]) => (
              <Box key={key} display="flex" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  {key.replace(/_/g, ' ')}:
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {String(value)}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Paper>
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Inferred Goals
          </Typography>
          <Stack spacing={1}>
            {mentalModel.goals.length > 0 ? (
              mentalModel.goals.map((goal) => (
                <Chip
                  key={goal}
                  icon={<TrendingUpIcon />}
                  label={goal.replace(/_/g, ' ')}
                  variant="outlined"
                  color="warning"
                  size="small"
                />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No goals inferred yet
              </Typography>
            )}
          </Stack>
        </Paper>
      </Grid>

      <Grid item xs={12}>
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Knowledge Gained
          </Typography>
          <Box display="flex" gap={0.5} flexWrap="wrap">
            {mentalModel.knowledge.length > 0 ? (
              mentalModel.knowledge.map((k) => (
                <Chip key={k} label={k} size="small" variant="outlined" />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No knowledge tracked yet
              </Typography>
            )}
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );
};

// === Metrics Tab ===

interface MetricsTabProps {
  metrics: CognitiveMetrics;
  deception: DeceptionMetrics;
}

const MetricsTab: React.FC<MetricsTabProps> = ({ metrics, deception }) => {
  const metricItems = [
    { label: 'Overconfidence', value: metrics.overconfidence_score, color: '#ef4444' },
    { label: 'Persistence', value: metrics.persistence_score, color: '#f97316' },
    { label: 'Tunnel Vision', value: metrics.tunnel_vision_score, color: '#eab308' },
    { label: 'Curiosity', value: metrics.curiosity_score, color: '#22c55e' },
    { label: 'Exploration', value: metrics.exploration_diversity, color: '#3b82f6' },
    { label: 'Error Tolerance', value: metrics.error_tolerance, color: '#8b5cf6' },
  ];

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Cognitive Metrics
          </Typography>
          <Stack spacing={2}>
            {metricItems.map((item) => (
              <Box key={item.label}>
                <Box display="flex" justifyContent="space-between" mb={0.5}>
                  <Typography variant="body2">{item.label}</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {Math.round(item.value * 100)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={item.value * 100}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    bgcolor: `${item.color}20`,
                    '& .MuiLinearProgress-bar': {
                      bgcolor: item.color,
                      borderRadius: 3,
                    },
                  }}
                />
              </Box>
            ))}
          </Stack>
        </Paper>
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Deception Effectiveness
          </Typography>
          <Stack spacing={2}>
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2">Total Applied</Typography>
              <Typography variant="h6">{deception.total_applied}</Typography>
            </Box>
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2">Successful</Typography>
              <Typography variant="h6" color="success.main">
                {deception.successful}
              </Typography>
            </Box>
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2">Success Rate</Typography>
              <Typography variant="h6">
                {Math.round(deception.success_rate * 100)}%
              </Typography>
            </Box>
            <Divider />
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="body2">Suspicion Level</Typography>
              <Chip
                label={deception.suspicion_level < 0.3 ? 'Low' : deception.suspicion_level < 0.7 ? 'Medium' : 'High'}
                color={deception.suspicion_level < 0.3 ? 'success' : deception.suspicion_level < 0.7 ? 'warning' : 'error'}
                size="small"
              />
            </Box>
          </Stack>
        </Paper>
      </Grid>
    </Grid>
  );
};

// === Deception Strategy Dashboard ===

interface StrategyDashboardProps {
  strategies?: Strategy[];
  effectiveness?: {
    total_strategies: number;
    overall_success_rate: number;
    top_strategies: Array<{
      name: string;
      bias_type: string;
      effectiveness: number;
    }>;
  };
}

export const StrategyDashboard: React.FC<StrategyDashboardProps> = ({
  strategies,
  effectiveness,
}) => {
  const [filterBias, setFilterBias] = useState<string | null>(null);

  const filteredStrategies = strategies?.filter((s) =>
    filterBias ? s.bias_type === filterBias : true
  );

  return (
    <Card>
      <CardHeader
        avatar={<ShieldIcon color="primary" />}
        title="Deception Strategies"
        subheader={`${strategies?.length || 0} strategies available`}
      />
      <CardContent>
        <Grid container spacing={2}>
          {/* Filter Chips */}
          <Grid item xs={12}>
            <Box display="flex" gap={1} flexWrap="wrap">
              <Chip
                label="All"
                onClick={() => setFilterBias(null)}
                color={filterBias === null ? 'primary' : 'default'}
              />
              {Object.keys(BIAS_COLORS).map((bias) => (
                <Chip
                  key={bias}
                  label={BIAS_LABELS[bias] || bias}
                  onClick={() => setFilterBias(bias)}
                  color={filterBias === bias ? 'primary' : 'default'}
                  size="small"
                />
              ))}
            </Box>
          </Grid>

          {/* Top Strategies Chart */}
          {effectiveness && (
            <Grid item xs={12}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Top Performing Strategies
                </Typography>
                <Box height={200}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={effectiveness.top_strategies}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[0, 1]} />
                      <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 12 }} />
                      <RechartsTooltip />
                      <Bar
                        dataKey="effectiveness"
                        fill="#3b82f6"
                        radius={[0, 4, 4, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </Paper>
            </Grid>
          )}

          {/* Strategy Table */}
          <Grid item xs={12}>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Strategy</TableCell>
                    <TableCell>Bias Type</TableCell>
                    <TableCell align="right">Effectiveness</TableCell>
                    <TableCell align="center">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredStrategies?.map((strategy) => (
                    <TableRow key={strategy.name}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {strategy.name.replace(/_/g, ' ')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={BIAS_LABELS[strategy.bias_type] || strategy.bias_type}
                          size="small"
                          sx={{
                            bgcolor: BIAS_COLORS[strategy.bias_type] || '#6b7280',
                            color: 'white',
                            fontSize: '0.7rem',
                          }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {Math.round(strategy.effectiveness_score * 100)}%
                      </TableCell>
                      <TableCell align="center">
                        {strategy.is_active ? (
                          <CheckCircleIcon color="success" fontSize="small" />
                        ) : (
                          <WarningIcon color="warning" fontSize="small" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// === Cognitive Bias Distribution Chart ===

interface BiasDistributionProps {
  biases: DetectedBias[];
}

export const BiasDistributionChart: React.FC<BiasDistributionProps> = ({ biases }) => {
  const data = biases.map((bias) => ({
    name: BIAS_LABELS[bias.bias_type] || bias.bias_type,
    value: bias.confidence,
    color: BIAS_COLORS[bias.bias_type] || '#6b7280',
  }));

  return (
    <Card>
      <CardHeader title="Bias Distribution" />
      <CardContent>
        <Box height={250}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Legend />
              <RechartsTooltip />
            </PieChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

// === Export All Components ===

export default {
  CognitiveProfilePanel,
  StrategyDashboard,
  BiasDistributionChart,
};