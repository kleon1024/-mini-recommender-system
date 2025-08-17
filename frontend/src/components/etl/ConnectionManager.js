import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  TextField, FormControl, InputLabel, Select, MenuItem, Grid
} from '@mui/material';

/**
 * 数据库连接管理组件
 * 用于创建和测试数据库连接
 */
const ConnectionManager = ({
  open,
  onClose,
  onSave,
  onTest,
  connectionTypes
}) => {
  // 连接表单状态
  const [connectionData, setConnectionData] = useState({
    name: '',
    description: '',
    connection_type: 'mysql',
    host: '',
    port: '',
    username: '',
    password: '',
    database: '',
    config: JSON.stringify({}, null, 2)
  });

  // 处理表单字段变化
  const handleChange = (e) => {
    const { name, value } = e.target;
    setConnectionData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 处理配置变化
  const handleConfigChange = (e) => {
    setConnectionData(prev => ({
      ...prev,
      config: e.target.value
    }));
  };

  // 处理保存
  const handleSave = () => {
    try {
      const formattedData = {
        ...connectionData,
        port: parseInt(connectionData.port),
        config: JSON.parse(connectionData.config)
      };
      onSave(formattedData);
      resetForm();
    } catch (error) {
      console.error('解析配置失败:', error);
      alert('配置格式错误，请检查JSON格式');
    }
  };

  // 处理测试连接
  const handleTest = () => {
    try {
      const formattedData = {
        ...connectionData,
        port: parseInt(connectionData.port),
        config: JSON.parse(connectionData.config)
      };
      onTest(formattedData);
    } catch (error) {
      console.error('解析配置失败:', error);
      alert('配置格式错误，请检查JSON格式');
    }
  };

  // 重置表单
  const resetForm = () => {
    setConnectionData({
      name: '',
      description: '',
      connection_type: 'mysql',
      host: '',
      port: '',
      username: '',
      password: '',
      database: '',
      config: JSON.stringify({}, null, 2)
    });
  };

  // 处理关闭
  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>新建数据库连接</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <TextField
              label="连接名称"
              name="name"
              value={connectionData.name}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth required margin="normal">
              <InputLabel>连接类型</InputLabel>
              <Select
                name="connection_type"
                value={connectionData.connection_type}
                onChange={handleChange}
                label="连接类型"
              >
                {connectionTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="描述"
              name="description"
              value={connectionData.description}
              onChange={handleChange}
              fullWidth
              multiline
              rows={2}
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={8}>
            <TextField
              label="主机"
              name="host"
              value={connectionData.host}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              label="端口"
              name="port"
              value={connectionData.port}
              onChange={handleChange}
              fullWidth
              required
              type="number"
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              label="用户名"
              name="username"
              value={connectionData.username}
              onChange={handleChange}
              fullWidth
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              label="密码"
              name="password"
              type="password"
              value={connectionData.password}
              onChange={handleChange}
              fullWidth
              margin="normal"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="数据库"
              name="database"
              value={connectionData.database}
              onChange={handleChange}
              fullWidth
              margin="normal"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="配置 (JSON)"
              value={connectionData.config}
              onChange={handleConfigChange}
              fullWidth
              multiline
              rows={4}
              margin="normal"
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>取消</Button>
        <Button onClick={handleTest} color="info">测试连接</Button>
        <Button onClick={handleSave} variant="contained" color="primary">创建</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConnectionManager;