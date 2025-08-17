import React, { useState } from 'react';
import {
  Box, Paper, Typography, Button, IconButton, Divider, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import {
  Code as CodeIcon,
  OpenInNew as OpenInNewIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { CodeEditor } from './index';

/**
 * SQL执行器组件
 * 提供SQL编辑和执行功能，支持内嵌Adminer
 */
const SqlExecutor = ({ open, onClose }) => {
  const [sql, setSql] = useState('SELECT * FROM users LIMIT 10;');
  const [showAdminer, setShowAdminer] = useState(false);

  // 处理SQL变化
  const handleSqlChange = (value) => {
    setSql(value);
  };

  // 切换Adminer显示
  const toggleAdminer = () => {
    setShowAdminer(!showAdminer);
  };

  // 构建Adminer URL
  const getAdminerUrl = () => {
    return `http://localhost:8080/?pgsql=postgres&username=postgres&db=datawarehouse&ns=dw&sql=${encodeURIComponent(sql)}`;
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '90vh', display: 'flex', flexDirection: 'column' }
      }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center">
            <CodeIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">SQL执行器</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <Divider />
      <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>
        {!showAdminer ? (
          <Box p={2} display="flex" flexDirection="column" height="100%">
            <Typography variant="caption" color="textSecondary" paragraph>
              在此编辑SQL语句，点击「执行SQL」按钮在Adminer中执行
            </Typography>
            <Box flexGrow={1} mb={2}>
              <CodeEditor
                value={sql}
                onChange={handleSqlChange}
                language="sql"
                theme="light"
                height="100%"
              />
            </Box>
            <Box display="flex" justifyContent="space-between">
              <Box>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<CodeIcon />}
                  onClick={toggleAdminer}
                  sx={{ mr: 1 }}
                >
                  执行SQL
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={() => {
                    // 简单的SQL格式化逻辑
                    try {
                      // 移除多余空格，规范化关键字大写
                      const formattedSql = sql
                        .replace(/\s+/g, ' ')
                        .replace(/\s*([,;])\s*/g, '$1 ')
                        .replace(/\s*=\s*/g, ' = ')
                        .replace(/\bselect\b/gi, 'SELECT')
                        .replace(/\bfrom\b/gi, 'FROM')
                        .replace(/\bwhere\b/gi, 'WHERE')
                        .replace(/\band\b/gi, 'AND')
                        .replace(/\bor\b/gi, 'OR')
                        .replace(/\bgroup by\b/gi, 'GROUP BY')
                        .replace(/\border by\b/gi, 'ORDER BY')
                        .replace(/\blimit\b/gi, 'LIMIT')
                        .replace(/\bjoin\b/gi, 'JOIN')
                        .replace(/\bon\b/gi, 'ON')
                        .replace(/\bhaving\b/gi, 'HAVING');
                      setSql(formattedSql);
                    } catch (error) {
                      console.error('格式化SQL失败:', error);
                    }
                  }}
                >
                  格式化
                </Button>
              </Box>
              <Button
                variant="outlined"
                color="secondary"
                endIcon={<OpenInNewIcon />}
                onClick={() => {
                  // 在新窗口打开，但不跳转当前页面
                  window.open(getAdminerUrl(), '_blank', 'noopener,noreferrer');
                }}
              >
                在新窗口中打开
              </Button>
            </Box>
          </Box>
        ) : (
          <Box display="flex" flexDirection="column" height="100%">
            <Box p={1} bgcolor="#f5f5f5">
              <Button
                variant="outlined"
                size="small"
                onClick={toggleAdminer}
                startIcon={<CodeIcon />}
              >
                返回编辑器
              </Button>
            </Box>
            <Box flexGrow={1} sx={{ height: 'calc(100% - 48px)' }}>
              <iframe
                src={getAdminerUrl()}
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="Adminer SQL执行"
              />
            </Box>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default SqlExecutor;