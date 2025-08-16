# 迷你推荐系统技术需求文档 (TRD)

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 文档版本 | V1.0 |
| 创建日期 | 2023-11-02 |
| 最后更新 | 2023-11-02 |
| 状态 | 初稿 |
| 关联文档 | [PRD.md](/Users/bytedance/projects/aieng/mini-recommender-system/PRD.md) |

## 1. 概述

### 1.1 背景

基于产品需求文档(PRD)中的要求，我们需要构建一个迷你推荐系统，用于教学目的。本文档将PRD拆解为具体的技术需求，并明确MVP版本的技术选型和实现方案。

### 1.2 MVP目标

MVP（最小可行产品）版本的目标是实现推荐系统的核心功能，包括：

1. 基础的前端展示和交互
2. 用户行为数据采集
3. 简单的数据处理流程
4. 基础推荐算法实现
5. 简易的数据分析功能

### 1.3 系统规模（MVP阶段）

1. **用户规模**：支持1万级别用户数量（PRD中最终目标为10万级别）
2. **内容规模**：支持1-5万级别的内容数量（PRD中最终目标为数十万级别）
3. **数据量**：能够处理与上述规模相匹配的用户行为数据

注：MVP阶段采用较小规模以加速开发和测试，后续版本将逐步扩展至PRD中规定的完整规模。

## 2. 系统架构

### 2.1 MVP架构概览

为了快速实现MVP，我们将简化系统架构，保留核心组件：

```
+----------------+    +----------------+    +----------------+
|                |    |                |    |                |
|  Web前端       |    |  后端API服务   |    |  埋点服务      |
|                |    |                |    |                |
+-------+--------+    +-------+--------+    +-------+--------+
        |                     |                     |
        v                     v                     v
+-------+---------------------+---------------------+--------+
|                                                            |
|                       数据存储层                           |
|                     (MySQL + MinIO)                        |
+-------+---------------------+------------------------------+
        |                     |                     
        v                     v                     
+-------+--------+    +-------+--------+    
|                |    |                |    
|  数据处理服务  |    |  推荐算法服务  |    
|                |    |                |    
+----------------+    +----------------+    
```

### 2.2 组件说明

1. **Web前端**：提供用户界面，展示内容和推荐结果
2. **后端API服务**：处理前端请求，提供业务逻辑
3. **埋点服务**：收集用户行为数据
4. **数据存储层**：存储用户、内容、行为数据
5. **数据处理服务**：处理原始数据，生成特征和样本
6. **推荐算法服务**：实现基础推荐算法

## 3. 技术选型

### 3.1 前端技术栈

| 技术/框架 | 版本 | 用途 |
| --- | --- | --- |
| React | 18.x | 前端框架 |
| Ant Design | 5.x | UI组件库 |
| Redux Toolkit | 1.9.x | 状态管理 |
| Axios | 1.4.x | HTTP客户端 |
| React Router | 6.x | 路由管理 |
| ECharts | 5.4.x | 数据可视化 |

### 3.2 后端技术栈

| 技术/框架 | 版本 | 用途 |
| --- | --- | --- |
| FastAPI | 0.95.x | API服务框架 |
| SQLAlchemy | 2.0.x | ORM框架 |
| Pydantic | 1.10.x | 数据验证 |
| Pandas | 2.0.x | 数据处理 |
| NumPy | 1.24.x | 科学计算 |
| Scikit-learn | 1.2.x | 机器学习库 |
| PyTorch (轻量级) | 2.0.x | 深度学习库 |

### 3.3 存储技术栈

| 技术/框架 | 版本 | 用途 |
| --- | --- | --- |
| MySQL | 8.0 | 关系型数据库 |
| MinIO | 最新版 | 对象存储(模拟HDFS) |
| Redis | 7.0 | 缓存(可选) |

### 3.4 部署技术栈

| 技术/框架 | 版本 | 用途 |
| --- | --- | --- |
| Docker | 最新稳定版 | 容器化 |
| Docker Compose | 最新稳定版 | 容器编排 |

## 4. 数据模型设计

### 4.1 数据库表设计

#### 4.1.1 用户表 (users)

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| user_id | VARCHAR(64) | 主键，用户ID |
| username | VARCHAR(64) | 用户名 |
| create_time | TIMESTAMP | 创建时间 |
| tags | JSON | 用户标签 |
| preferences | JSON | 用户偏好 |

#### 4.1.2 内容表 (posts)

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| post_id | VARCHAR(64) | 主键，内容ID |
| title | VARCHAR(128) | 标题 |
| content | TEXT | 内容 |
| author_id | VARCHAR(64) | 作者ID，外键关联users表 |
| create_time | TIMESTAMP | 创建时间 |
| tags | JSON | 内容标签 |
| view_count | INT | 浏览次数 |
| like_count | INT | 点赞次数 |
| favorite_count | INT | 收藏次数 |

#### 4.1.3 行为表 (events)

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| event_id | VARCHAR(64) | 主键，事件ID |
| user_id | VARCHAR(64) | 用户ID，外键关联users表 |
| post_id | VARCHAR(64) | 内容ID，外键关联posts表 |
| event_type | VARCHAR(32) | 事件类型(view, click, like, favorite, play, stay) |
| timestamp | TIMESTAMP | 事件时间 |
| source | VARCHAR(64) | 事件来源 |
| device_info | JSON | 设备信息 |
| extra | JSON | 额外信息 |

#### 4.1.4 特征表 (features)

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| feature_id | VARCHAR(64) | 主键，特征ID |
| entity_type | VARCHAR(32) | 实体类型(user, post) |
| entity_id | VARCHAR(64) | 实体ID |
| feature_type | VARCHAR(32) | 特征类型 |
| feature_value | JSON | 特征值 |
| update_time | TIMESTAMP | 更新时间 |

### 4.2 对象存储设计

#### 4.2.1 模型存储

```
models/
  ├── tag_based/
  │   └── {version}/model.pkl
  ├── collaborative_filtering/
  │   └── {version}/model.pkl
  ├── swing/
  │   └── {version}/model.pkl
  └── vector/
      └── {version}/model.pkl
```

#### 4.2.2 样本存储

```
samples/
  ├── daily/
  │   └── {date}/samples.parquet
  ├── positive/
  │   └── {date}/samples.parquet
  └── negative/
      └── {date}/samples.parquet
```

## 5. 接口设计

### 5.1 前端API

#### 5.1.1 获取推荐内容

```
GET /api/recommendations
Params:
  - user_id: string
  - count: integer (default: 20)
  - page: integer (default: 1)
Response:
  - posts: array of post objects
  - has_more: boolean
```

#### 5.1.2 获取帖子详情

```
GET /api/posts/{post_id}
Response:
  - post: post object
  - related_posts: array of related post objects
```

#### 5.1.3 用户行为上报

```
POST /api/events
Body:
  - user_id: string
  - post_id: string
  - event_type: string (view, click, like, favorite, play, stay)
  - timestamp: timestamp
  - source: string
  - device_info: object
  - extra: object (optional)
Response:
  - success: boolean
```

### 5.2 数据处理API

#### 5.2.1 触发数据处理任务

```
POST /api/data/process
Body:
  - task_type: string (daily, feature, sample)
  - params: object
Response:
  - task_id: string
  - status: string
```

### 5.3 模型API

#### 5.3.1 触发模型训练

```
POST /api/models/train
Body:
  - model_type: string (tag, cf)
  - params: object
Response:
  - model_id: string
  - status: string
```

## 6. 算法实现

### 6.1 MVP阶段算法

#### 6.1.1 基于标签的推荐

**算法描述**：根据用户历史行为提取兴趣标签，与内容标签进行匹配，计算相似度得分。

**实现步骤**：
1. 从用户历史行为中提取感兴趣的标签及权重
2. 计算用户标签向量与内容标签向量的余弦相似度
3. 根据相似度得分排序，返回Top-N结果

**技术实现**：使用Python + Scikit-learn实现，采用TF-IDF或CountVectorizer处理标签

#### 6.1.2 协同过滤

**算法描述**：基于用户-物品交互矩阵，计算物品间相似度，推荐相似物品。

**实现步骤**：
1. 构建用户-物品交互矩阵
2. 计算物品间相似度（余弦相似度或Jaccard相似度）
3. 对于目标用户交互过的物品，找出相似物品并排序

**技术实现**：使用Python + Scikit-learn + Pandas实现，采用稀疏矩阵存储交互数据

## 7. 部署方案

### 7.1 Docker容器配置

#### 7.1.1 前端容器

```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

#### 7.1.2 后端容器

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Docker Compose配置

```yaml
version: '3'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis
      - minio
    environment:
      - DATABASE_URL=mysql://user:password@mysql:3306/recommender
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin

  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=root
      - MYSQL_DATABASE=recommender
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7.0
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  mysql_data:
  minio_data:
```

## 8. 实现路径与执行计划

### 8.1 MVP阶段实现计划

| 阶段 | 任务 | 预计工时(人天) |
| --- | --- | --- |
| 1 | 环境搭建与基础架构 | 3 |
| 1.1 | Docker环境配置 | 1 |
| 1.2 | 数据库设计与初始化 | 1 |
| 1.3 | 项目结构搭建 | 1 |
| 2 | 前端开发 | 5 |
| 2.1 | 页面框架与路由 | 1 |
| 2.2 | 首页与推荐列表 | 1 |
| 2.3 | 帖子详情页 | 1 |
| 2.4 | 用户中心 | 1 |
| 2.5 | 埋点实现 | 1 |
| 3 | 后端开发 | 7 |
| 3.1 | API服务框架 | 1 |
| 3.2 | 数据模型与ORM | 1 |
| 3.3 | 埋点接口 | 1 |
| 3.4 | 推荐接口 | 2 |
| 3.5 | 数据处理服务 | 2 |
| 4 | 算法实现 | 5 |
| 4.1 | 基于标签的推荐 | 2 |
| 4.2 | 协同过滤 | 3 |
| 5 | 测试与部署 | 3 |
| 5.1 | 单元测试 | 1 |
| 5.2 | 集成测试 | 1 |
| 5.3 | 容器化部署 | 1 |

**总计**：23人天

### 8.2 开发里程碑

| 里程碑 | 交付内容 | 预计完成时间 |
| --- | --- | --- |
| M1: 环境准备 | Docker环境、项目结构、数据库设计 | 第1周末 |
| M2: 前端框架 | 基础页面、路由、组件 | 第2周中 |
| M3: 后端基础 | API服务、数据模型、基础接口 | 第2周末 |
| M4: 埋点系统 | 前端埋点、埋点接口、数据存储 | 第3周中 |
| M5: 基础推荐 | 标签推荐算法、推荐接口 | 第3周末 |
| M6: 协同过滤 | 协同过滤算法、相似内容推荐 | 第4周中 |
| M7: MVP完成 | 系统集成、测试、部署 | 第4周末 |

### 8.3 交付物清单

1. **代码仓库**
   - 前端代码（React应用）
   - 后端代码（FastAPI服务）
   - 算法代码（Python模块）
   - Docker配置文件

2. **文档**
   - 系统设计文档
   - API文档
   - 部署指南
   - 用户手册

3. **数据库**
   - 数据库初始化脚本
   - 示例数据集

4. **模型**
   - 基础推荐模型
   - 协同过滤模型

## 9. 技术评审与验收标准

### 9.1 技术评审点

| 评审项 | 评审内容 | 评审标准 |
| --- | --- | --- |
| 架构设计 | 系统架构的合理性和可扩展性 | 组件职责清晰，接口定义合理，支持后续扩展 |
| 技术选型 | 技术栈的适用性和兼容性 | 技术成熟度高，学习成本适中，各组件间兼容性好 |
| 数据模型 | 数据库设计的规范性和效率 | 符合数据库设计范式，索引设计合理，支持高效查询 |
| 接口设计 | API接口的一致性和可用性 | 接口命名规范，参数定义清晰，错误处理完善 |
| 算法实现 | 推荐算法的正确性和效率 | 算法逻辑正确，计算效率高，结果可解释 |
| 部署方案 | 容器化配置的完整性和可靠性 | 容器配置合理，服务编排正确，环境隔离良好 |

### 9.2 MVP验收标准

#### 9.2.1 功能验收

| 功能点 | 验收标准 | 验收方法 |
| --- | --- | --- |
| 用户浏览 | 用户可以浏览首页推荐内容和帖子详情 | 功能测试 |
| 用户交互 | 用户可以点击、点赞、收藏帖子 | 功能测试 |
| 埋点收集 | 系统能够收集并存储用户行为数据 | 数据验证 |
| 数据处理 | 系统能够处理原始数据并生成特征 | 数据验证 |
| 推荐算法 | 基于标签和协同过滤的推荐结果合理 | 算法评估 |
| 容器部署 | 系统可以通过Docker Compose一键部署 | 部署测试 |

#### 9.2.2 性能验收

| 性能指标 | 目标值 | 验收方法 |
| --- | --- | --- |
| 页面加载时间 | < 2秒 | 性能测试 |
| API响应时间 | < 500ms | 性能测试 |
| 推荐生成时间 | < 1秒 | 性能测试 |
| 数据处理效率 | 每小时处理>10万条记录 | 性能测试 |
| 系统资源占用 | CPU < 50%, 内存 < 2GB | 监控验证 |

## 10. 风险与应对

| 风险 | 影响 | 应对措施 |
| --- | --- | --- |
| 数据量不足 | 算法效果不佳 | 设计合理的数据生成脚本，模拟真实用户行为 |
| 性能瓶颈 | 系统响应慢 | 实现缓存机制，优化数据库查询，必要时增加索引 |
| 算法复杂度 | 开发周期延长 | 优先实现简单算法，确保基础功能可用，再逐步优化 |
| 容器化部署问题 | 系统无法正常运行 | 提前进行小规模测试，确保各组件间通信正常 |

## 11. 后续扩展

MVP完成后，可以考虑以下扩展：

1. **高级算法实现**：
   - Swing算法
   - 向量召回算法
   - 轻量级精排模型

2. **数据中台升级**：
   - 引入Hive/HDFS
   - 实现更复杂的数据处理流程

3. **算法中台升级**：
   - 模型训练与部署流程优化
   - A/B测试框架

4. **实时处理能力**：
   - 引入Kafka
   - 实现Flink任务
   - 在线学习框架

## 12. 需求追踪矩阵

下表展示了TRD中的技术实现与PRD中功能需求的对应关系，确保MVP阶段的技术实现能够满足产品需求：

| PRD功能需求 | TRD技术实现 | 优先级 | MVP阶段状态 |
| --- | --- | --- | --- |
| 前端展示层-用户界面 | React + Ant Design实现的Web前端 | 高 | 包含 |
| 前端展示层-交互功能 | 前端埋点系统 | 高 | 包含 |
| 数据采集层-埋点系统 | 埋点服务 + 事件API | 高 | 包含 |
| 数据处理层-数据清洗与转换 | 数据处理服务 | 高 | 简化版包含 |
| 数据处理层-样本生成 | 数据处理服务 | 中 | 简化版包含 |
| 算法层-基于标签的召回 | 基于标签的推荐算法 | 高 | 包含 |
| 算法层-协同过滤 | 协同过滤算法 | 高 | 包含 |
| 算法层-Swing算法 | - | 低 | MVP后实现 |
| 算法层-向量召回 | - | 低 | MVP后实现 |
| 算法层-轻量级精排模型 | - | 低 | MVP后实现 |
| 存储层-数据存储 | MySQL数据库 | 高 | 包含 |
| 存储层-模型存储 | MinIO对象存储 | 高 | 包含 |
| 分析层-数据分析 | 简易数据分析功能 | 中 | 简化版包含 |
| 分析层-可视化界面 | ECharts实现的数据可视化 | 中 | 简化版包含 |
| 容器化部署 | Docker + Docker Compose | 高 | 包含 |

## 13. 附录

### 13.1 技术栈版本兼容性

| 组件 | 依赖关系 |
| --- | --- |
| FastAPI | Python 3.7+ |
| SQLAlchemy | Python 3.7+ |
| React | Node.js 14+ |
| Docker | 需要支持Compose V3 |

### 13.2 参考资料

1. FastAPI官方文档: https://fastapi.tiangolo.com/
2. React官方文档: https://reactjs.org/docs/getting-started.html
3. Docker Compose文档: https://docs.docker.com/compose/
4. 推荐系统相关论文和技术博客
5. Scikit-learn文档: https://scikit-learn.org/stable/