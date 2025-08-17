import React, { useState, useEffect } from 'react';
import {
  Box, Paper, TextField, FormControl, InputLabel, Select, MenuItem,
  Grid, Button, Typography, Tabs, Tab, Divider, TableContainer, Table,
  TableHead, TableRow, TableCell, TableBody, Chip, Collapse, IconButton
} from '@mui/material';
import {
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import { theme, combinedStyles } from '../../styles/theme';
import { CodeEditor } from './index';

/**
 * ETL任务编辑器组件
 * 支持不同类型任务的编辑，特别是自定义SQL类型的任务
 * 增加了执行历史标签页
 */
const TaskEditor = ({
  task,
  isNew = false,
  connections,
  taskTypes,
  taskHistory = [],
  onSave,
  onCancel,
  onTest,
  onRunTask,
  getConnectionName,
  getTaskTypeLabel,
  getStatusColor,
  formatDateTime,
  formatDuration
}) => {
  // 初始化任务数据
  const [taskData, setTaskData] = useState({
    name: '',
    description: '',
    task_type: 'mysql_to_postgres',
    source_connection_id: '',
    target_connection_id: '',
    config: JSON.stringify({
      source_table: '',
      target_table: '',
      batch_size: 1000,
      schema: 'raw'
    }, null, 2),
    schedule: '',
    run_immediately: false
  });

  // 当前选中的编辑器标签
  const [currentTab, setCurrentTab] = useState(0);
  
  // 展开/收起状态管理
  const [expandedHistoryId, setExpandedHistoryId] = useState(null);
  
  // 处理历史记录展开/收起
  const handleHistoryExpand = (historyId) => {
    setExpandedHistoryId(expandedHistoryId === historyId ? null : historyId);
  };

  // 当task变化时更新表单数据
  useEffect(() => {
    if (task) {
      setTaskData({
        ...task,
        config: typeof task.config === 'object' ? JSON.stringify(task.config, null, 2) : task.config
      });
      
      // 如果是自定义SQL类型，默认选择SQL编辑器标签
      if (task.task_type === 'custom_sql') {
        setCurrentTab(1);
      }
    }
  }, [task]);

  // 处理表单字段变化
  const handleChange = (e) => {
    const { name, value } = e.target;
    setTaskData(prev => ({
      ...prev,
      [name]: value
    }));

    // 当任务类型变化时，更新配置模板
      if (name === 'task_type') {
        let configTemplate = {};
        
        switch (value) {
          case 'mysql_to_postgres':
            configTemplate = {
              source_table: '',
              target_table: '',
              batch_size: 1000,
              schema: 'raw',
              incremental_field: '',
              incremental_value: ''
            };
            setCurrentTab(0); // 切换到基本配置标签
            break;
          case 'postgres_to_redis':
            configTemplate = {
              source_query: 'SELECT * FROM table_name',
              key_prefix: 'prefix:',
              key_field: 'id',
              expire_seconds: 3600
            };
            setCurrentTab(0);
            break;
          case 'mysql_to_redis':
            configTemplate = {
              source_query: 'SELECT * FROM table_name',
              key_prefix: 'prefix:',
              key_field: 'id',
              expire_seconds: 3600
            };
            setCurrentTab(0);
            break;
          case 'custom_sql':
            configTemplate = {
              sql: '-- 在此输入SQL语句\nSELECT * FROM table_name;'
            };
            setCurrentTab(1); // 切换到SQL编辑器标签
            break;
          default:
            configTemplate = {};
        }
        
        // 如果当前标签页是执行历史，需要根据新的任务类型调整标签页索引
        if ((taskData.task_type === 'custom_sql' && currentTab === 2) || 
            (taskData.task_type !== 'custom_sql' && currentTab === 1)) {
          // 延迟设置，确保DOM已更新
          setTimeout(() => {
            setCurrentTab(value === 'custom_sql' ? 2 : 1);
          }, 0);
        }

      setTaskData(prev => ({
        ...prev,
        config: JSON.stringify(configTemplate, null, 2)
      }));
    }
  };

  // 处理配置变化
  const handleConfigChange = (e) => {
    setTaskData(prev => ({
      ...prev,
      config: e.target.value
    }));
  };

  // 处理SQL变化（针对自定义SQL类型）
  const handleSqlChange = (e) => {
    try {
      const config = JSON.parse(taskData.config);
      config.sql = e.target.value;
      setTaskData(prev => ({
        ...prev,
        config: JSON.stringify(config, null, 2)
      }));
    } catch (error) {
      console.error('解析配置失败:', error);
    }
  };

  // 获取当前SQL（针对自定义SQL类型）
  const getCurrentSql = () => {
    try {
      const config = JSON.parse(taskData.config);
      return config.sql || '';
    } catch (error) {
      return '';
    }
  };

  // 处理保存
  const handleSave = () => {
    try {
      const formattedData = {
        ...taskData,
        // 确保ID作为字符串处理，避免JavaScript大整数精度问题
        source_connection_id: taskData.source_connection_id ? String(taskData.source_connection_id) : '',
        target_connection_id: taskData.target_connection_id ? String(taskData.target_connection_id) : '',
        config: JSON.parse(taskData.config)
      };
      console.log('保存任务数据，确保ID作为字符串:', formattedData);
      onSave(formattedData);
    } catch (error) {
      console.error('解析配置失败:', error);
      alert('配置格式错误，请检查JSON格式');
    }
  };

  // 处理测试SQL（针对自定义SQL类型）
  const handleTestSql = () => {
    try {
      const config = JSON.parse(taskData.config);
      // 确保source_connection_id作为字符串处理，避免JavaScript大整数精度问题
      const connectionIdStr = taskData.source_connection_id ? String(taskData.source_connection_id) : '';
      console.log(`测试SQL，连接ID: ${connectionIdStr}`);
      onTest(connectionIdStr, config.sql);
    } catch (error) {
      console.error('解析配置失败:', error);
      alert('配置格式错误，请检查JSON格式');
    }
  };

  return (
    <Paper className="p-4" elevation={0} variant="outlined">
      <Tabs 
        value={currentTab} 
        onChange={(e, newValue) => setCurrentTab(newValue)}
        className="mb-4"
      >
        <Tab label="基本配置" />
        {taskData.task_type === 'custom_sql' && <Tab label="SQL编辑器" />}
        <Tab label={`执行历史${taskData.task_type === 'custom_sql' ? '' : ''}`} value={taskData.task_type === 'custom_sql' ? 2 : 1} />
      </Tabs>

      {currentTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              label="任务名称"
              name="name"
              value={taskData.name}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth required margin="normal">
              <InputLabel>任务类型</InputLabel>
              <Select
                name="task_type"
                value={taskData.task_type}
                onChange={handleChange}
                label="任务类型"
              >
                {taskTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="描述"
              name="description"
              value={taskData.description || ''}
              onChange={handleChange}
              fullWidth
              multiline
              rows={2}
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth required margin="normal">
              <InputLabel>源连接</InputLabel>
              <Select
                name="source_connection_id"
                value={taskData.source_connection_id}
                onChange={handleChange}
                label="源连接"
              >
                {connections.map((conn) => (
                  <MenuItem key={conn.connection_id} value={conn.connection_id}>
                    {conn.name} ({conn.connection_type})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>目标连接</InputLabel>
              <Select
                name="target_connection_id"
                value={taskData.target_connection_id || ''}
                onChange={handleChange}
                label="目标连接"
              >
                <MenuItem value="">无</MenuItem>
                {connections.map((conn) => (
                  <MenuItem key={conn.connection_id} value={conn.connection_id}>
                    {conn.name} ({conn.connection_type})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="配置 (JSON)"
              value={taskData.config}
              onChange={handleConfigChange}
              fullWidth
              multiline
              rows={8}
              margin="normal"
              required
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              label="调度 (Cron表达式)"
              name="schedule"
              value={taskData.schedule || ''}
              onChange={handleChange}
              fullWidth
              margin="normal"
              helperText="例如: 0 0 * * * (每天午夜执行)"
            />
          </Grid>
          {isNew && (
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>立即执行</InputLabel>
                <Select
                  name="run_immediately"
                  value={taskData.run_immediately}
                  onChange={handleChange}
                  label="立即执行"
                >
                  <MenuItem value={true}>是</MenuItem>
                  <MenuItem value={false}>否</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          )}
        </Grid>
      )}

      {currentTab === 1 && taskData.task_type === 'custom_sql' && (
        <div>
          <Box display="flex" alignItems="center" mb={1}>
            <CodeIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="subtitle1">SQL编辑器</Typography>
          </Box>
          <Typography variant="caption" color="textSecondary" paragraph>
            在此编辑SQL语句，将在PostgreSQL数据库中执行
          </Typography>
          <CodeEditor
            value={getCurrentSql()}
            onChange={(value) => {
              const event = { target: { value } };
              handleSqlChange(event);
            }}
            language="sql"
            theme={"light"}
            height="300px"
          />
          <Box mt={2} display="flex" justifyContent="space-between">
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleTestSql}
              disabled={!taskData.source_connection_id}
              startIcon={<CodeIcon />}
            >
              测试SQL
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              href={`http://localhost:8080/?pgsql=postgres&username=postgres&db=datawarehouse&ns=dw&sql=${encodeURIComponent(getCurrentSql())}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              在Adminer中打开
            </Button>
          </Box>
        </div>
      )}
      
      {(taskData.task_type === 'custom_sql' ? currentTab === 2 : currentTab === 1) && (
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

      <Divider className="my-4" />
      
      <Box display="flex" justifyContent="flex-end" mt={2}>
        <Button onClick={onCancel} className="mr-2">取消</Button>
        {(taskData.task_type === 'custom_sql' ? currentTab === 2 : currentTab === 1) && !isNew && task && task.status !== 'running' && (
          <Button 
            onClick={() => {
              onRunTask(task.task_id);
              // 保持在执行历史标签页并延迟刷新历史记录
                setTimeout(() => {
                  // 根据任务类型设置正确的标签页索引
                  setCurrentTab(taskData.task_type === 'custom_sql' ? 2 : 1);
                }, 500);
            }} 
            color="primary" 
            variant="outlined"
            className="mr-2"
          >
            运行任务
          </Button>
        )}
        <Button onClick={handleSave} variant="contained" color="primary">保存</Button>
      </Box>
    </Paper>
  );
};

export default TaskEditor;