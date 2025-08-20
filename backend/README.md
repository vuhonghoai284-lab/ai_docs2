# AI文档测试系统后端 - 重构版

## 架构说明

本项目采用分层架构设计，包含以下层次：

### 目录结构
```
backend/
├── app/
│   ├── core/           # 核心配置和依赖
│   │   ├── config.py   # 配置管理
│   │   └── database.py # 数据库连接
│   ├── models/         # 数据模型（ORM）
│   │   ├── task.py     # 任务模型
│   │   ├── issue.py    # 问题模型
│   │   └── ai_output.py # AI输出模型
│   ├── dto/            # 数据传输对象
│   │   ├── task.py     # 任务DTO
│   │   ├── issue.py    # 问题DTO
│   │   └── ai_output.py # AI输出DTO
│   ├── repositories/   # 数据访问层
│   │   ├── task.py     # 任务仓库
│   │   ├── issue.py    # 问题仓库
│   │   └── ai_output.py # AI输出仓库
│   ├── services/       # 业务逻辑层
│   │   ├── task.py     # 任务服务
│   │   └── task_processor.py # 任务处理器
│   ├── views/          # 视图层（API路由）
│   └── main.py         # 主应用入口
├── tests/              # 测试目录
│   ├── conftest.py     # 测试配置
│   └── test_api.py     # API测试
├── config.yaml         # 配置文件
├── requirements.txt    # 依赖包
├── pytest.ini          # pytest配置
└── run.py             # 启动脚本
```

## 分层架构优势

1. **解耦性**：各层职责分明，降低耦合度
2. **可维护性**：代码组织清晰，易于理解和修改
3. **可测试性**：每层可独立测试
4. **可扩展性**：方便添加新功能和修改现有功能

## 各层职责

### Core层
- 管理应用配置
- 处理数据库连接
- 提供公共依赖

### Models层
- 定义数据库表结构
- 管理表之间的关系

### DTO层
- 定义API请求和响应格式
- 数据验证和序列化

### Repository层
- 封装数据库操作
- 提供数据访问接口
- 处理数据持久化

### Service层
- 实现业务逻辑
- 协调各层之间的调用
- 处理复杂的业务流程

### View层
- 定义API路由
- 处理HTTP请求
- 调用Service层

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置文件
确保 `config.yaml` 文件存在并配置正确

### 3. 启动服务
```bash
python run.py
```

服务将在 http://localhost:8080 启动

### 4. 查看API文档
访问 http://localhost:8080/docs 查看Swagger文档

## 运行测试

```bash
pytest
```

## API端点

- `GET /` - 根路径
- `GET /api/models` - 获取模型列表
- `POST /api/tasks` - 创建任务
- `GET /api/tasks` - 获取任务列表
- `GET /api/tasks/{task_id}` - 获取任务详情
- `DELETE /api/tasks/{task_id}` - 删除任务
- `PUT /api/issues/{issue_id}/feedback` - 提交问题反馈
- `GET /api/tasks/{task_id}/ai-outputs` - 获取AI输出记录
- `GET /api/ai-outputs/{output_id}` - 获取AI输出详情

## 主要改进

1. **分层架构**：代码组织更清晰，易于维护
2. **依赖注入**：使用FastAPI的依赖注入系统
3. **类型提示**：全面使用Python类型提示
4. **测试框架**：集成pytest进行单元测试和集成测试
5. **代码复用**：通过Repository和Service层提高代码复用
6. **错误处理**：统一的错误处理机制
7. **配置管理**：集中式配置管理