import React from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  Chip, IconButton, CircularProgress
} from '@mui/material';
import {
  PlayArrow as PlayIcon, Cancel as CancelIcon, Delete as DeleteIcon,
  Edit as EditIcon, Info as InfoIcon
} from '@mui/icons-material';
import { theme, combinedStyles } from '../../styles/theme';

/**
 * ETL任务列表组件
 * 显示所有ETL任务并提供基本操作功能
 */
const TaskList = ({
  tasks,
  loading,
  onViewTask,
  onEditTask,
  onRunTask,
  onCancelTask,
  onDeleteTask,
  getConnectionName,
  getTaskTypeLabel,
  formatDateTime
}) => {
  // 获取状态样式
  const getStatusClass = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'running': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'cancelled': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default: return 'bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-200';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <CircularProgress />
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="text-center p-8">
        <p className={theme.text.body}>暂无任务</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
        <thead className="bg-neutral-50 dark:bg-neutral-800">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">名称</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">类型</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">源连接</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">目标连接</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">状态</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">上次运行</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">操作</th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-neutral-900 divide-y divide-neutral-200 dark:divide-neutral-800">
          {tasks.map((task) => (
            <tr key={task.task_id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">
              <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900 dark:text-neutral-100">{task.name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900 dark:text-neutral-100">{getTaskTypeLabel(task.task_type)}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900 dark:text-neutral-100">{getConnectionName(task.source_connection_id)}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900 dark:text-neutral-100">{task.target_connection_id ? getConnectionName(task.target_connection_id) : '-'}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(task.status)}`}>
                  {task.status}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900 dark:text-neutral-100">{formatDateTime(task.end_time)}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button 
                  className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 mr-2"
                  onClick={() => onViewTask(task.task_id)}
                  title="查看详情"
                >
                  <InfoIcon fontSize="small" />
                </button>
                <button 
                  className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-2"
                  onClick={() => onEditTask(task.task_id)}
                  title="编辑任务"
                >
                  <EditIcon fontSize="small" />
                </button>
                {task.status !== 'running' && (
                  <button 
                    className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300 mr-2"
                    onClick={() => onRunTask(task.task_id)}
                    title="运行任务"
                  >
                    <PlayIcon fontSize="small" />
                  </button>
                )}
                {task.status === 'running' && (
                  <button 
                    className="text-yellow-600 hover:text-yellow-900 dark:text-yellow-400 dark:hover:text-yellow-300 mr-2"
                    onClick={() => onCancelTask(task.task_id)}
                    title="取消任务"
                  >
                    <CancelIcon fontSize="small" />
                  </button>
                )}
                <button 
                  className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                  onClick={() => onDeleteTask(task.task_id)}
                  title="删除任务"
                >
                  <DeleteIcon fontSize="small" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TaskList;