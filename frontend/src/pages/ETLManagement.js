import React, { useState, useEffect } from 'react';
// 移除未使用的Redux导入
import {
  Box, Button, Typography, Paper, Snackbar, Alert, CircularProgress,
  Drawer, List, ListItem, ListItemText, Divider, IconButton, Chip, Dialog, DialogTitle, DialogContent, DialogActions, 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tabs, Tab
} from '@mui/material';
import {
  Add as AddIcon, Refresh as RefreshIcon, Storage as StorageIcon,
  Menu as MenuIcon, PlayArrow as PlayArrowIcon, Info as InfoIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import api from '../utils/api';
// 保留样式导入，可能在JSX中使用
import { theme, combinedStyles } from '../styles/theme';
import {
  TaskEditor, TaskDetail, ConnectionManager, SqlExecutor
} from '../components/etl';

const ETLManagement = () => {
  // 状态管理
  const [tasks, setTasks] = useState([]);
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [openConnectionDialog, setOpenConnectionDialog] = useState(false);
  const [openTaskDetailDialog, setOpenTaskDetailDialog] = useState(false);
  const [openSqlExecutorDialog, setOpenSqlExecutorDialog] = useState(false);
  // 移除任务执行结果对话框状态
  const [selectedTask, setSelectedTask] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [isCreatingTask, setIsCreatingTask] = useState(false);
  const [taskHistory, setTaskHistory] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [drawerOpen, setDrawerOpen] = useState(true);
  // 保留这个状态变量，因为在testSql函数中使用了
  const [sqlTestResult, setSqlTestResult] = useState(null);
  
  // 任务类型选项
  const taskTypes = [
    { value: 'mysql_to_postgres', label: 'MySQL到PostgreSQL' },
    { value: 'postgres_to_redis', label: 'PostgreSQL到Redis' },
    { value: 'mysql_to_redis', label: 'MySQL到Redis' },
    { value: 'custom_sql', label: '自定义SQL' }
  ];
  
  // 连接类型选项
  const connectionTypes = [
    { value: 'mysql', label: 'MySQL' },
    { value: 'postgres', label: 'PostgreSQL' },
    { value: 'redis', label: 'Redis' }
  ];
  
  // 加载任务列表
  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/etl/tasks');
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setSnackbar({
        open: true,
        message: '加载任务列表失败: ' + (error.message || '未知错误'),
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  // 加载连接列表
  const fetchConnections = async () => {
    try {
      const response = await api.get('/api/etl/connections');
      setConnections(response.data);
    } catch (error) {
      console.error('Error fetching connections:', error);
      setSnackbar({
        open: true,
        message: '加载连接列表失败: ' + (error.message || '未知错误'),
        severity: 'error'
      });
    }
  };
  
  // 获取任务执行历史
  const fetchTaskHistory = async (taskId) => {
    try {
      // 确保taskId作为字符串处理，避免JavaScript大整数精度问题
      const taskIdStr = String(taskId);
      console.log(`获取任务历史ID: ${taskIdStr}`);
      
      const response = await api.get(`/api/etl/tasks/${taskIdStr}/history`);
      setTaskHistory(response.data);
    } catch (error) {
      console.error('Error fetching task history:', error);
      setSnackbar({
        open: true,
        message: '获取任务历史失败: ' + (error.message || '未知错误'),
        severity: 'error'
      });
    }
  };
  
  // 创建新任务
  const createTask = async (taskData) => {
    try {
      // 确保connection_id作为字符串处理，避免JavaScript大整数精度问题
      console.log(`创建任务，源连接ID: ${taskData.source_connection_id}，目标连接ID: ${taskData.target_connection_id}`);
      
      await api.post('/api/etl/tasks', {
        ...taskData,
        // 确保ID作为字符串处理
        source_connection_id: taskData.source_connection_id ? String(taskData.source_connection_id) : '',
        target_connection_id: taskData.target_connection_id ? String(taskData.target_connection_id) : ''
      });
      
      setSnackbar({
        open: true,
        message: '任务创建成功',
        severity: 'success'
      });
      fetchTasks();
      setIsCreatingTask(false);
      setEditingTask(null);
    } catch (error) {
      console.error('Error creating task:', error);
      setSnackbar({
        open: true,
        message: '创建任务失败: ' + (error.response?.data?.detail || error.message),
        severity: 'error'
      });
    }
  };

  // 更新任务
  const updateTask = async (taskData) => {
    try {
      // 确保task_id作为字符串处理，避免JavaScript大整数精度问题
      const taskId = String(taskData.task_id);
      console.log(`更新任务ID: ${taskId}，源连接ID: ${taskData.source_connection_id}，目标连接ID: ${taskData.target_connection_id}`);
      
      // 这里需要后端提供更新任务的API
      // 假设API为 PUT /api/etl/tasks/{task_id}
      await api.put(`/api/etl/tasks/${taskId}`, {
        ...taskData,
        // 再次确保ID作为字符串处理
        task_id: taskId,
        source_connection_id: taskData.source_connection_id ? String(taskData.source_connection_id) : '',
        target_connection_id: taskData.target_connection_id ? String(taskData.target_connection_id) : ''
      });
      
      setSnackbar({
        open: true,
        message: '任务更新成功',
        severity: 'success'
      });
      fetchTasks();
      setEditingTask(null);
    } catch (error) {
      console.error('Error updating task:', error);
      setSnackbar({
        open: true,
        message: '更新任务失败: ' + (error.response?.data?.detail || error.message),
        severity: 'error'
      });
    }
  };
  
  // 创建新连接
  const createConnection = async (connectionData) => {
    try {
      await api.post('/api/etl/connections', connectionData);
      setOpenConnectionDialog(false);
      setSnackbar({
        open: true,
        message: '连接创建成功',
        severity: 'success'
      });
      fetchConnections();
    } catch (error) {
      console.error('Error creating connection:', error);
      setSnackbar({
        open: true,
        message: '创建连接失败: ' + (error.response?.data?.detail || error.message),
        severity: 'error'
      });
    }
  };
  
  // 运行任务
  const runTask = async (taskId) => {
    try {
      // 确保taskId作为字符串处理，避免JavaScript大整数精度问题
      const taskIdStr = String(taskId);
      console.log(`运行任务ID: ${taskIdStr}`);
      
      await api.post(`/api/etl/tasks/${taskIdStr}/run`);
      setSnackbar({
        open: true,
        message: '任务已启动',
        severity: 'info'
      });
      fetchTasks();
    } catch (error) {
      console.error('Error running task:', error);
      setSnackbar({
        open: true,
        message: '启动任务失败: ' + (error.message || '未知错误'),
        severity: 'error'
      });
    }
  };
  
  // 取消任务 - 当前未使用，但保留以备将来使用
  /*
  const cancelTask = async (taskId) => {
    try {
      await api.post(`/api/etl/tasks/${taskId}/cancel`);
      setSnackbar({
        open: true,
        message: '任务已取消',
        severity: 'info'
      });
      fetchTasks();
    } catch (error) {
      console.error('Error cancelling task:', error);
      setSnackbar({
        open: true,
        message: '取消任务失败: ' + (error.message || '未知错误'),
        severity: 'error'
      });
    }
  };
  */
  
  // 删除任务 - 当前未使用，但保留以备将来使用
  /*
  const deleteTask = async (taskId) => {
    if (window.confirm('确定要删除此任务吗？')) {
      try {
        await api.delete(`/api/etl/tasks/${taskId}`);
        setSnackbar({
          open: true,
          message: '任务已删除',
          severity: 'success'
        });
        fetchTasks();
        if (editingTask && editingTask.task_id === taskId) {
          setEditingTask(null);
        }
      } catch (error) {
        console.error('Error deleting task:', error);
        setSnackbar({
          open: true,
          message: '删除任务失败: ' + (error.message || '未知错误'),
          severity: 'error'
        });
      }
    }
  };
  */
  
  // 查看任务详情
  const viewTaskDetail = async (taskId) => {
    try {
      // 确保taskId作为字符串处理，避免JavaScript大整数精度问题
      const taskIdStr = String(taskId);
      console.log(`查看任务详情ID: ${taskIdStr}`);
      
      const response = await api.get(`/api/etl/tasks/${taskIdStr}`);
      setSelectedTask(response.data);
      fetchTaskHistory(taskIdStr);
      setOpenTaskDetailDialog(true);
    } catch (error) {
      console.error('Error fetching task details:', error);
      setSnackbar({
        open: true,
        message: '获取任务详情失败: ' + (error.message || '未知错误'),
        severity: 'error'
      });
    }
  };

  // 编辑任务
  const editTask = async (taskId) => {
    try {
      // 确保taskId作为字符串处理，避免JavaScript大整数精度问题
      const taskIdStr = String(taskId);
      console.log(`编辑任务ID: ${taskIdStr}`);
      
      const response = await api.get(`/api/etl/tasks/${taskIdStr}`);
      setEditingTask(response.data);
      setIsCreatingTask(false);
      // 获取任务历史记录
      fetchTaskHistory(taskIdStr);
    } catch (error) {
      console.error('Error fetching task for edit:', error);
      setSnackbar({
        open: true,
        message: '获取任务失败: ' + (error.message || '未知错误'),
        severity: 'error'
      });
    }
  };
  
  // 测试连接
  const testConnection = async (connectionData) => {
    try {
      const response = await api.post('/api/etl/connections/test', connectionData);
      setSnackbar({
        open: true,
        message: response.data.message,
        severity: response.data.success ? 'success' : 'error'
      });
    } catch (error) {
      console.error('Error testing connection:', error);
      setSnackbar({
        open: true,
        message: '测试连接失败: ' + (error.response?.data?.detail || error.message),
        severity: 'error'
      });
    }
  };

  // 测试SQL
  const testSql = async (connectionId, sql) => {
    try {
      // 确保connectionId作为字符串处理，避免JavaScript大整数精度问题
      const connectionIdStr = String(connectionId);
      console.log(`测试SQL，连接ID: ${connectionIdStr}`);
      
      // 这里需要后端提供测试SQL的API
      // 假设API为 POST /api/etl/sql/test
      const response = await api.post('/api/etl/sql/test', {
        connection_id: connectionIdStr,
        sql: sql
      });
      setSqlTestResult(response.data);
      setSnackbar({
        open: true,
        message: 'SQL测试成功',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error testing SQL:', error);
      setSnackbar({
        open: true,
        message: '测试SQL失败: ' + (error.response?.data?.detail || error.message),
        severity: 'error'
      });
    }
  };
  
  // 初始加载
  useEffect(() => {
    fetchTasks();
    fetchConnections();
  }, []);
  
  // 获取连接名称
  const getConnectionName = (connectionId) => {
    const connection = connections.find(conn => conn.connection_id === connectionId);
    return connection ? connection.name : '未知连接';
  };
  
  // 获取任务类型标签
  const getTaskTypeLabel = (type) => {
    const taskType = taskTypes.find(t => t.value === type);
    return taskType ? taskType.label : type;
  };
  
  // 获取状态颜色
  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'default';
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };
  
  // 格式化时间
  const formatDateTime = (dateTime) => {
    if (!dateTime) return '-';
    return new Date(dateTime).toLocaleString();
  };
  
  // 格式化持续时间
  const formatDuration = (startTime, endTime) => {
    if (!startTime || !endTime) return '-';
    const start = new Date(startTime);
    const end = new Date(endTime);
    const durationMs = end - start;
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}小时 ${minutes % 60}分钟`;
    } else if (minutes > 0) {
      return `${minutes}分钟 ${seconds % 60}秒`;
    } else {
      return `${seconds}秒`;
    }
  };

  // 处理任务保存
  const handleTaskSave = (taskData) => {
    if (isCreatingTask) {
      createTask(taskData);
    } else if (editingTask) {
      updateTask(taskData);
    }
  };

  // 处理任务取消
  const handleTaskCancel = () => {
    setEditingTask(null);
    setIsCreatingTask(false);
  };

  // 抽屉宽度
  const drawerWidth = 280;
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      
      {/* 主体内容区 */}
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        {/* 侧边栏 */}
        <Drawer
          variant="persistent"
          anchor="left"
          open={drawerOpen}
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            position: 'relative',
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
              position: 'relative',
              height: '100%',
            },
          }}
        >
        <Box sx={{ display: 'flex', alignItems: 'center', padding: 2, justifyContent: 'space-between' }}>
          <Typography variant="h6">ETL任务管理</Typography>
          <IconButton onClick={() => setDrawerOpen(false)}>
            <MenuIcon />
          </IconButton>
        </Box>
        <Divider />
        <Box sx={{ padding: 2 }}>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            fullWidth 
            onClick={() => {
              setIsCreatingTask(true);
              setEditingTask(null);
            }}
            sx={{ mb: 2 }}
          >
            新建任务
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<StorageIcon />} 
            fullWidth
            onClick={() => setOpenConnectionDialog(true)}
            sx={{ mb: 2 }}
          >
            新建连接
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<CodeIcon />} 
            fullWidth
            onClick={() => setOpenSqlExecutorDialog(true)}
            sx={{ mb: 2 }}
            color="secondary"
          >
            SQL执行器
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            fullWidth
            onClick={fetchTasks}
          >
            刷新
          </Button>
        </Box>
        <Divider />
        <List sx={{ overflow: 'auto', flexGrow: 1 }}>
          {tasks.map((task) => (
            <ListItem 
              key={task.task_id} 
              component="div"
              selected={editingTask && editingTask.task_id === task.task_id}
            >
              <ListItemText 
                primary={task.name} 
                secondary={getTaskTypeLabel(task.task_type)} 
                onClick={() => editTask(task.task_id)}
                sx={{ cursor: 'pointer', flexGrow: 1 }}
              />
              <Chip 
                label={task.status} 
                color={getStatusColor(task.status)} 
                size="small" 
                sx={{ mr: 1 }}
              />
              <Box>
                <IconButton 
                  size="small" 
                  color="info" 
                  onClick={(e) => {
                    e.stopPropagation();
                    viewTaskDetail(task.task_id);
                  }}
                  title="查看详情"
                  sx={{ mr: 0.5 }}
                >
                  <InfoIcon fontSize="small" />
                </IconButton>
                <IconButton 
                  size="small" 
                  color="primary" 
                  onClick={(e) => {
                    e.stopPropagation();
                    runTask(task.task_id);
                    // 执行后获取历史记录，但不弹出对话框
                    setTimeout(() => {
                      fetchTaskHistory(task.task_id);
                      // 如果正在编辑该任务，更新历史记录标签页
                      if (editingTask && editingTask.task_id === task.task_id) {
                        // 延迟一点时间确保历史记录已更新
                        setTimeout(() => {
                          // 提示用户任务已执行
                          setSnackbar({
                            open: true,
                            message: `任务 ${task.name} 已执行，可在历史记录中查看结果`,
                            severity: 'success'
                          });
                        }, 500);
                      }
                    }, 1000);
                  }}
                  title="立即执行"
                >
                  <PlayArrowIcon fontSize="small" />
                </IconButton>
              </Box>
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* 主内容区 */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          padding: 0,
          width: '100%',
          maxWidth: '100%',
          height: '100%',
          overflow: 'auto',
          transition: theme => theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          marginLeft: drawerOpen ? 0 : 0,
        }}
      >

        {/* 任务编辑器或欢迎信息 */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        ) : isCreatingTask || editingTask ? (
          <TaskEditor
            task={editingTask}
            isNew={isCreatingTask}
            connections={connections}
            taskTypes={taskTypes}
            taskHistory={taskHistory}
            onSave={handleTaskSave}
            onCancel={handleTaskCancel}
            onTest={testSql}
            onRunTask={runTask}
            getConnectionName={getConnectionName}
            getTaskTypeLabel={getTaskTypeLabel}
            getStatusColor={getStatusColor}
            formatDateTime={formatDateTime}
            formatDuration={formatDuration}
          />
        ) : (
          <Box sx={{ p: 4, textAlign: 'center', border: '1px solid rgba(0, 0, 0, 0.12)', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Typography variant="h6" gutterBottom>
              选择一个任务进行编辑，或创建新任务
            </Typography>
            <Typography variant="body2" color="textSecondary">
              从左侧任务列表中选择一个任务，或点击"新建任务"按钮创建新任务
            </Typography>
          </Box>
        )}
      </Box>
      </Box>



      {/* 连接管理对话框 */}
      <ConnectionManager
        open={openConnectionDialog}
        onClose={() => setOpenConnectionDialog(false)}
        onSave={createConnection}
        onTest={testConnection}
        connectionTypes={connectionTypes}
      />

      {/* 任务详情对话框 */}
      <TaskDetail
        open={openTaskDetailDialog}
        onClose={() => setOpenTaskDetailDialog(false)}
        task={selectedTask}
        taskHistory={taskHistory}
        onRunTask={runTask}
        getConnectionName={getConnectionName}
        getTaskTypeLabel={getTaskTypeLabel}
        getStatusColor={getStatusColor}
        formatDateTime={formatDateTime}
        formatDuration={formatDuration}
      />
      
      {/* 任务执行结果对话框已移除，改为直接在任务编辑器中显示历史记录 */}
      
      {/* SQL执行器对话框 */}
      <SqlExecutor
        open={openSqlExecutorDialog}
        onClose={() => setOpenSqlExecutorDialog(false)}
      />
      
      {/* 提示消息 */}
      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={6000} 
        onClose={() => setSnackbar({...snackbar, open: false})}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar({...snackbar, open: false})} 
          severity={snackbar.severity} 
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ETLManagement;