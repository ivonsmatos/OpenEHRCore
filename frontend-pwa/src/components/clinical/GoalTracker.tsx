import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as UncheckedIcon,
  TrendingUp as ImprovingIcon,
  TrendingDown as WorseningIcon,
  TrendingFlat as NoChangeIcon,
  Add as AddIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface GoalTarget {
  id: string;
  measure?: any;
  target_display: string;
  due_date?: string;
  detail_quantity_value?: number;
  detail_quantity_unit?: string;
  detail_quantity_comparator?: string;
}

interface Goal {
  id: string;
  identifier: string;
  lifecycle_status: string;
  lifecycle_status_display: string;
  achievement_status?: string;
  achievement_status_display?: string;
  description_text: string;
  subject_id: string;
  start_date?: string;
  status_date?: string;
  priority?: string;
  targets_count: number;
  created_at: string;
  targets?: GoalTarget[];
}

interface GoalTrackerProps {
  patientId: string;
  onGoalUpdate?: () => void;
}

const GoalTracker: React.FC<GoalTrackerProps> = ({ patientId, onGoalUpdate }) => {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [activeOnly, setActiveOnly] = useState(true);

  useEffect(() => {
    fetchGoals();
  }, [patientId, activeOnly]);

  const fetchGoals = async () => {
    try {
      setLoading(true);
      const activeParam = activeOnly ? '&active_only=true' : '';
      const response = await axios.get(
        `/api/v1/goals/patient/${patientId}/?${activeParam}`
      );
      setGoals(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching goals:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGoalDetails = async (goalId: string) => {
    try {
      const response = await axios.get(`/api/v1/goals/${goalId}/`);
      setSelectedGoal(response.data);
      setDialogOpen(true);
    } catch (error) {
      console.error('Error fetching goal details:', error);
    }
  };

  const handleActivate = async (goalId: string) => {
    try {
      await axios.post(`/api/v1/goals/${goalId}/activate/`, {
        note: 'Objetivo ativado pelo sistema',
      });
      fetchGoals();
      if (onGoalUpdate) onGoalUpdate();
    } catch (error) {
      console.error('Error activating goal:', error);
    }
  };

  const handleAchieve = async (goalId: string, achievementStatus: string) => {
    try {
      await axios.post(`/api/v1/goals/${goalId}/achieve/`, {
        achievement_status: achievementStatus,
        note: `Objetivo marcado como ${achievementStatus}`,
      });
      fetchGoals();
      if (onGoalUpdate) onGoalUpdate();
      setDialogOpen(false);
    } catch (error) {
      console.error('Error achieving goal:', error);
    }
  };

  const getLifecycleColor = (status: string) => {
    const colorMap: { [key: string]: 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' } = {
      'proposed': 'default',
      'planned': 'info',
      'accepted': 'primary',
      'active': 'success',
      'on-hold': 'warning',
      'completed': 'default',
      'cancelled': 'error',
      'rejected': 'error',
    };
    return colorMap[status] || 'default';
  };

  const getAchievementIcon = (status?: string) => {
    switch (status) {
      case 'improving':
        return <ImprovingIcon color="success" />;
      case 'worsening':
        return <WorseningIcon color="error" />;
      case 'no-change':
        return <NoChangeIcon color="warning" />;
      case 'achieved':
        return <CheckCircleIcon color="success" />;
      default:
        return <UncheckedIcon />;
    }
  };

  const calculateProgress = (goal: Goal): number => {
    // Simplificado: baseado no achievement_status
    if (goal.achievement_status === 'achieved') return 100;
    if (goal.achievement_status === 'improving') return 70;
    if (goal.achievement_status === 'in-progress') return 50;
    if (goal.achievement_status === 'worsening') return 30;
    if (goal.lifecycle_status === 'proposed') return 0;
    return 50;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Não definido';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  if (loading) {
    return <Box p={2}>Carregando objetivos...</Box>;
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={2} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h6">Objetivos Terapêuticos</Typography>
        <Box>
          <Chip
            label="Apenas Ativos"
            onClick={() => setActiveOnly(!activeOnly)}
            color={activeOnly ? 'primary' : 'default'}
            size="small"
          />
        </Box>
      </Box>

      {/* Goals List */}
      <Grid container spacing={2}>
        {goals.map((goal) => {
          const progress = calculateProgress(goal);
          
          return (
            <Grid item xs={12} md={6} key={goal.id}>
              <Card
                onClick={() => fetchGoalDetails(goal.id)}
                sx={{ cursor: 'pointer', '&:hover': { boxShadow: 3 } }}
              >
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {goal.description_text}
                    </Typography>
                    {getAchievementIcon(goal.achievement_status)}
                  </Box>

                  <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                    <Chip
                      label={goal.lifecycle_status_display}
                      size="small"
                      color={getLifecycleColor(goal.lifecycle_status)}
                    />
                    {goal.achievement_status && (
                      <Chip
                        label={goal.achievement_status_display}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    {goal.priority && (
                      <Chip label={goal.priority} size="small" variant="outlined" />
                    )}
                  </Box>

                  {/* Progress Bar */}
                  <Box mb={1}>
                    <Box display="flex" justifyContent="space-between" mb={0.5}>
                      <Typography variant="caption" color="textSecondary">
                        Progresso
                      </Typography>
                      <Typography variant="caption" fontWeight="bold">
                        {progress}%
                      </Typography>
                    </Box>
                    <LinearProgress variant="determinate" value={progress} />
                  </Box>

                  {/* Metadata */}
                  <Box display="flex" justifyContent="space-between" mt={1}>
                    <Typography variant="caption" color="textSecondary">
                      Início: {formatDate(goal.start_date)}
                    </Typography>
                    {goal.targets_count > 0 && (
                      <Typography variant="caption" color="textSecondary">
                        {goal.targets_count} meta{goal.targets_count > 1 ? 's' : ''}
                      </Typography>
                    )}
                  </Box>

                  {/* Quick Actions */}
                  {goal.lifecycle_status === 'proposed' && (
                    <Button
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleActivate(goal.id);
                      }}
                      sx={{ mt: 1 }}
                    >
                      Ativar Objetivo
                    </Button>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Goal Details Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        {selectedGoal && (
          <>
            <DialogTitle>
              <Box display="flex" justifyContent="space-between" alignItems="start">
                <Typography variant="h6">{selectedGoal.description_text}</Typography>
                <Box display="flex" gap={1}>
                  <Chip
                    label={selectedGoal.lifecycle_status_display}
                    size="small"
                    color={getLifecycleColor(selectedGoal.lifecycle_status)}
                  />
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              {/* Target List */}
              {selectedGoal.targets && selectedGoal.targets.length > 0 && (
                <Box mb={3}>
                  <Typography variant="subtitle2" gutterBottom>
                    Metas:
                  </Typography>
                  <List dense>
                    {selectedGoal.targets.map((target) => (
                      <ListItem key={target.id}>
                        <ListItemText
                          primary={target.target_display}
                          secondary={target.due_date ? `Prazo: ${formatDate(target.due_date)}` : null}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* Metadata */}
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    <strong>Data Início:</strong> {formatDate(selectedGoal.start_date)}
                  </Typography>
                </Grid>
                {selectedGoal.status_date && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Última Atualização:</strong> {formatDate(selectedGoal.status_date)}
                    </Typography>
                  </Grid>
                )}
                {selectedGoal.achievement_status && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Status de Alcance:</strong> {selectedGoal.achievement_status_display}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </DialogContent>
            <DialogActions>
              {selectedGoal.lifecycle_status === 'active' && (
                <>
                  <Button onClick={() => handleAchieve(selectedGoal.id, 'achieved')} color="success">
                    Marcar como Alcançado
                  </Button>
                  <Button onClick={() => handleAchieve(selectedGoal.id, 'not-achieved')} color="error">
                    Não Alcançado
                  </Button>
                </>
              )}
              <Button onClick={() => setDialogOpen(false)}>Fechar</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {goals.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography variant="body1" color="textSecondary">
            Nenhum objetivo encontrado
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default GoalTracker;
