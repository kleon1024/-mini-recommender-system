# 迷你推荐系统

## 项目概述

迷你推荐系统是一个简化版的推荐引擎实现，包含前端展示、后端API、数据采集、推荐算法等核心功能。系统支持基于标签和协同过滤的推荐算法，并提供完整的用户行为埋点和数据分析功能。

## 系统架构

系统由以下主要组件构成：

- **前端**：React + Redux + Ant Design实现的用户界面
- **后端**：FastAPI实现的API服务
- **数据库**：MySQL存储用户、内容、行为和特征数据
- **推荐引擎**：基于标签和协同过滤的推荐算法

## 快速开始

### 方式一：直接启动（推荐）

#### 启动后端

```bash
# 添加执行权限
chmod +x start_backend.sh

# 启动后端服务
./start_backend.sh
```

后端服务将在 http://localhost:8000 启动

#### 启动前端

```bash
# 添加执行权限
chmod +x start_frontend.sh

# 启动前端服务
./start_frontend.sh
```

前端服务将在 http://localhost:3000 启动

### 方式二：Docker部署

如果您已安装Docker和Docker Compose，可以使用以下命令一键启动整个系统：

```bash
# 添加执行权限
chmod +x run_system.sh

# 运行系统脚本
./run_system.sh
```

然后选择"1. 启动系统"选项。

## 功能验证

1. 打开浏览器访问 http://localhost:3000
2. 首页将显示推荐内容列表
3. 点击内容卡片可查看详情和相关推荐
4. 可以进行点赞、收藏等交互操作

## 测试

系统提供了单元测试和集成测试：

```bash
# 运行后端单元测试
python -m unittest discover -s tests/backend

# 运行集成测试（需要先启动系统）
python -m unittest discover -s tests/integration
```

## 项目结构

```
├── backend/           # 后端代码
│   ├── models/        # 数据模型
│   ├── routers/       # API路由
│   ├── schemas/       # 数据校验模型
│   ├── services/      # 业务逻辑服务
│   └── utils/         # 工具函数
├── frontend/          # 前端代码
│   ├── public/        # 静态资源
│   └── src/           # 源代码
│       ├── pages/     # 页面组件
│       ├── store/     # Redux状态管理
│       └── utils/     # 工具函数
├── database/          # 数据库脚本
├── docker/            # Docker配置
└── tests/             # 测试代码
    ├── backend/       # 后端单元测试
    └── integration/   # 集成测试
```

## 文档

- [技术需求文档](TRD.md)
- [开发任务清单](TODO.md)