import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Typography, Grid, Paper, Chip, TableContainer, Table,
  TableHead, TableRow, TableCell, TableBody, Tabs, Tab, Box,
  Collapse, IconButton, TextField, Divider
} from '@mui/material';
import {
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon
} from '@mui/icons-material';

/**
 * ETL任务详情组件
 * 显示任务详情、SQL编辑器和执行历史
 */
const TaskDetail = ({
  open,
  onClose,
  task,
  taskHistory,
  onRunTask,
  getConnectionName,
  getTaskTypeLabel,
  getStatusColor,
  formatDateTime,
  formatDuration
}) => {
  // 标签页状态
  const [tabValue, setTabValue] = useState(0);
  
  // 展开/收起状态管理
  const [expandedHistoryId, setExpandedHistoryId] = useState(null);
  
  // SQL编辑器状态
  const [sqlContent, setSqlContent] = useState('');
  
  // 处理标签页切换
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // 处理历史记录展开/收起
  const handleHistoryExpand = (historyId) => {
    setExpandedHistoryId(expandedHistoryId === historyId ? null : historyId);
  };
  
  // 初始化SQL编辑器内容
  React.useEffect(() => {
    if (task && task.task_type === 'custom_sql' && task.config && task.config.sql) {
      setSqlContent(task.config.sql);
    }
  }, [task]);
  
  if (!task) return null;
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>任务详情: {task.name}</DialogTitle>
      <DialogContent>
        {/* 标签页导航 */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="任务详情标签页">
            <Tab label="基本配置" />
            <Tab label="SQL编辑器" disabled={task.task_type !== 'custom_sql'} />
            <Tab label="执行历史" />
          </Tabs>
        </Box>
        
        {/* 基本配置标签页 */}
        {tabValue === 0 && (
          <Box>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">任务ID</Typography>
                <Typography variant="body2">{task.task_id}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">任务类型</Typography>
                <Typography variant="body2">{getTaskTypeLabel(task.task_type)}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">源连接</Typography>
                <Typography variant="body2">{getConnectionName(task.source_connection_id)}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">目标连接</Typography>
                <Typography variant="body2">
                  {task.target_connection_id ? getConnectionName(task.target_connection_id) : '-'}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">状态</Typography>
                <Chip 
                  label={task.status} 
                  color={getStatusColor(task.status)} 
                  size="small" 
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">调度</Typography>
                <Typography variant="body2">{task.schedule || '-'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2">描述</Typography>
                <Typography variant="body2">{task.description || '-'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2">配置</Typography>
                <Paper variant="outlined" sx={{ p: 1, maxHeight: 200, overflow: 'auto' }}>
                  <pre>{JSON.stringify(task.config, null, 2)}</pre>
                </Paper>
              </Grid>
              {task.error_message && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="error">错误信息</Typography>
                  <Paper variant="outlined" sx={{ p: 1, bgcolor: '#fff8f8' }}>
                    <Typography variant="body2" color="error">{task.error_message}</Typography>
                  </Paper>
                </Grid>
              )}
            </Grid>
          </Box>
        )}
        
        {/* SQL编辑器标签页 */}
        {tabValue === 1 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>SQL查询</Typography>
            <TextField
              fullWidth
              multiline
              rows={10}
              variant="outlined"
              value={sqlContent}
              onChange={(e) => setSqlContent(e.target.value)}
              sx={{ fontFamily: 'monospace' }}
              placeholder="输入SQL查询语句..."
            />
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="contained" color="primary">
                测试SQL
              </Button>
            </Box>
          </Box>
        )}
        
        {/* 执行历史标签页 */}
        {tabValue === 2 && (
          <Box>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox"></TableCell>
                    <TableCell>开始时间</TableCell>
                    <TableCell>结束时间</TableCell>
                    <TableCell>状态</TableCell>
                    <TableCell>处理行数</TableCell>
                    <TableCell>持续时间</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {taskHistory.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center">暂无执行历史</TableCell>
                    </TableRow>
                  ) : (
                    taskHistory.map((history) => (
                      <React.Fragment key={history.history_id}>
                        <TableRow>
                          <TableCell padding="checkbox">
                            <IconButton
                              aria-label="展开详情"
                              size="small"
                              onClick={() => handleHistoryExpand(history.history_id)}
                            >
                              {expandedHistoryId === history.history_id ? 
                                <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                            </IconButton>
                          </TableCell>
                          <TableCell>{formatDateTime(history.start_time)}</TableCell>
                          <TableCell>{formatDateTime(history.end_time)}</TableCell>
                          <TableCell>
                            <Chip 
                              label={history.status} 
                              color={getStatusColor(history.status)} 
                              size="small" 
                            />
                          </TableCell>
                          <TableCell>{history.rows_processed}</TableCell>
                          <TableCell>{formatDuration(history.start_time, history.end_time)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                            <Collapse in={expandedHistoryId === history.history_id} timeout="auto" unmountOnExit>
                              <Box sx={{ margin: 1 }}>
                                <Typography variant="subtitle2" gutterBottom component="div">
                                  执行日志
                                </Typography>
                                {history.error_message ? (
                                  <Paper variant="outlined" sx={{ p: 2, bgcolor: '#fff8f8', maxHeight: 300, overflow: 'auto' }}>
                                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', color: 'error.main' }}>
                                      {history.error_message}
                                    </Typography>
                                  </Paper>
                                ) : (
                                  <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f5f5f5', maxHeight: 300, overflow: 'auto' }}>
                                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                                      任务执行成功，处理了 {history.rows_processed} 行数据。
                                      开始时间: {formatDateTime(history.start_time)}
                                      结束时间: {formatDateTime(history.end_time)}
                                      持续时间: {formatDuration(history.start_time, history.end_time)}
                                    </Typography>
                                  </Paper>
                                )}
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      </React.Fragment>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>关闭</Button>
        {tabValue === 0 && task.status !== 'running' && (
          <Button 
            onClick={() => {
              onRunTask(task.task_id);
              // 运行任务后切换到执行历史标签页
              setTabValue(2);
            }} 
            color="primary" 
            variant="contained"
          >
            运行任务
          </Button>
        )}
        {tabValue === 1 && (
          <Button 
            onClick={() => {
              // 保存SQL内容到任务配置
              const updatedTask = {
                ...task,
                config: {
                  ...task.config,
                  sql: sqlContent
                }
              };
              // 这里需要添加保存SQL的逻辑
              console.log('保存SQL:', updatedTask);
            }} 
            color="primary" 
            variant="contained"
          >
            保存SQL
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default TaskDetail;