# 迷你推荐系统 - 数据分析平台

## 系统架构

本数据分析平台基于PostgreSQL构建，用于对迷你推荐系统的数据进行分析和处理，支持用户行为漏斗分析、用户标签提取、内容相似度计算、协同过滤推荐等功能。

### 组件说明

- **PostgreSQL**: 核心数据仓库，存储分析数据和结果
- **Adminer**: 数据库管理工具，用于查看和管理MySQL和PostgreSQL数据库
- **Metabase**: 数据可视化工具，用于构建数据分析大盘
- **pgAdmin**: PostgreSQL管理工具，用于高级数据库管理和查询

### 数据流

1. MySQL中的业务数据通过定时任务同步到PostgreSQL的raw schema
2. ETL流程处理raw数据，生成维度表、事实表和数据集市表
3. 基于处理后的数据，生成用户标签、内容标签、用户相似度矩阵、内容相似度矩阵等
4. 基于用户标签和相似度矩阵，生成用户推荐池并写入Redis
5. 推荐系统从Redis中获取推荐池，进行推荐

## 功能特性

### 1. 用户行为漏斗分析

- 跟踪用户从浏览到点赞到收藏的转化过程
- 分析不同来源、不同设备的转化率
- 计算各环节的转化时间和转化率

### 2. 用户标签提取

- 基于用户明确设置的兴趣提取显式标签
- 基于用户行为（浏览、点赞、收藏）提取隐式标签
- 计算标签权重，构建用户画像

### 3. 内容标签提取

- 基于内容元数据提取显式标签
- 计算标签权重，构建内容特征

### 4. 用户分群

- 基于活跃度将用户分为高度活跃、活跃、常规、偶尔和不活跃五类
- 支持自定义分群规则

### 5. 推荐算法

- 协同过滤：基于用户相似度的推荐
- 基于内容的推荐：基于内容相似度的推荐
- 基于标签的推荐：基于用户标签和内容标签的匹配推荐
- 流行度推荐：基于内容流行度的推荐

### 6. 数据可视化

- 用户活跃度趋势分析
- 内容表现趋势分析
- 推荐效果趋势分析
- 用户行为漏斗分析

## 使用方法

### 启动服务

```bash
cd docker
docker-compose up -d
```

### 访问服务

- **Adminer**: http://localhost:8080
  - 服务器: mysql 或 postgres
  - 用户名/密码: 
    - MySQL: user/password
    - PostgreSQL: postgres/postgres

- **Metabase**: http://localhost:3030
  - 初次访问需要设置管理员账号

- **pgAdmin**: http://localhost:5050
  - 邮箱: admin@example.com
  - 密码: admin

### 手动执行数据同步

```bash
# 进入容器
docker exec -it postgres bash

# 执行增量同步
python /scripts/mysql_to_postgres.py

# 执行全量同步
python /scripts/mysql_to_postgres.py --full

# 仅执行ETL流程
python /scripts/mysql_to_postgres.py --etl-only

# 仅执行数据同步
python /scripts/mysql_to_postgres.py --sync-only
```

## 数据模型

### 原始数据 (raw schema)

- `raw.users`: 用户原始数据
- `raw.posts`: 内容原始数据
- `raw.events`: 事件原始数据
- `raw.features`: 特征原始数据
- `raw.likes`: 点赞原始数据
- `raw.favorites`: 收藏原始数据

### 数据仓库 (dw schema)

- `dw.dim_users`: 用户维度表
- `dw.dim_posts`: 内容维度表
- `dw.fact_events`: 事件事实表（分区表）
- `dw.fact_user_funnels`: 用户行为漏斗事实表
- `dw.fact_user_tags`: 用户标签事实表
- `dw.fact_post_tags`: 内容标签事实表

### 数据集市 (mart schema)

- `mart.user_activity_analysis`: 用户活跃度分析
- `mart.content_performance_analysis`: 内容表现分析
- `mart.recommendation_performance_analysis`: 推荐效果分析
- `mart.user_similarity_matrix`: 用户相似度矩阵
- `mart.post_similarity_matrix`: 内容相似度矩阵
- `mart.user_recommendation_pool`: 用户推荐池

### 视图 (mart schema)

- `mart.vw_user_funnel_analysis`: 用户行为漏斗分析视图
- `mart.vw_user_activity_trend`: 用户活跃度趋势视图
- `mart.vw_content_performance_trend`: 内容表现趋势视图
- `mart.vw_recommendation_performance_trend`: 推荐效果趋势视图

## 定时任务

系统配置了以下定时任务：

- 每小时执行一次增量同步
- 每天凌晨2点执行一次ETL流程
- 每周日凌晨3点执行一次全量同步
- 每5分钟执行一次用户推荐池更新

## 注意事项

1. 首次启动时，需要等待PostgreSQL初始化完成后，手动执行一次全量同步
2. Metabase首次访问需要设置管理员账号和连接PostgreSQL数据库
3. 推荐池生成后会自动写入Redis，推荐系统可直接从Redis获取