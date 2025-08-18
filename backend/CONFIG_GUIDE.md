# AI服务配置指南

## 配置文件结构

AI服务现在完全通过 `config.yaml` 进行配置，支持多种AI提供商和灵活的环境变量配置。

## 基本配置

```yaml
ai_service:
  # 主要提供商：openai, anthropic, azure, custom
  provider: "openai"
  
  # OpenAI配置
  openai:
    api_key: "${OPENAI_API_KEY}"  # 从环境变量获取
    base_url: "https://api.openai.com/v1"  # 可自定义API端点
    model: "gpt-4o-mini"
    temperature: 0.3
    max_tokens: 4096
    timeout: 30
    max_retries: 3
```

## 环境变量支持

配置支持环境变量替换，格式为 `${ENV_VAR_NAME}`：

```yaml
openai:
  api_key: "${OPENAI_API_KEY}"    # 使用环境变量
  base_url: "${OPENAI_BASE_URL}"  # 可选的自定义端点
```

## 多提供商配置

```yaml
ai_service:
  provider: "openai"  # 主提供商
  
  # OpenAI配置
  openai:
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"
    model: "gpt-4o-mini"
    temperature: 0.3
    max_tokens: 4096
    
  # Anthropic配置（备选）
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "${ANTHROPIC_BASE_URL}"
    model: "claude-3-haiku-20240307"
    temperature: 0.3
    max_tokens: 4096
    
  # 通用默认配置
  default:
    temperature: 0.3
    max_tokens: 4096
    timeout: 30
    max_retries: 3
    
  # 降级策略
  fallback:
    enabled: true
    provider: "anthropic"  # 主提供商失败时切换到此提供商
```

## 配置参数说明

### 基本参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| provider | string | "openai" | AI提供商 |
| api_key | string | - | API密钥 |
| base_url | string | - | API端点URL |
| model | string | "gpt-4o-mini" | 使用的模型 |
| temperature | float | 0.3 | 温度参数(0-1) |
| max_tokens | int | 4096 | 最大token数 |
| timeout | int | 30 | 请求超时时间(秒) |
| max_retries | int | 3 | 最大重试次数 |

### 降级策略

当主提供商失败时，系统可以自动切换到备选提供商：

```yaml
fallback:
  enabled: true           # 启用降级
  provider: "anthropic"   # 备选提供商
```

## 使用方式

### 1. 设置环境变量

```bash
export OPENAI_API_KEY="your-openai-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export ANTHROPIC_API_KEY="your-anthropic-key"       # 备选
```

### 2. 直接配置密钥（不推荐用于生产环境）

```yaml
openai:
  api_key: "sk-your-direct-key-here"  # 直接填写
```

### 3. 自定义端点

```yaml
openai:
  base_url: "https://your-custom-endpoint.com/v1"
  model: "your-custom-model"
```

## 配置优先级

1. **提供商特定配置** > **通用默认配置** > **硬编码默认值**
2. **环境变量** > **配置文件中的直接值**

## 示例配置

### OpenAI官方API

```yaml
ai_service:
  provider: "openai"
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o-mini"
    temperature: 0.3
```

### 自建OpenAI兼容服务

```yaml
ai_service:
  provider: "openai"
  openai:
    api_key: "${CUSTOM_API_KEY}"
    base_url: "http://localhost:8000/v1"
    model: "custom-model"
```

### 双重保障配置

```yaml
ai_service:
  provider: "openai"
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o-mini"
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-haiku-20240307"
  fallback:
    enabled: true
    provider: "anthropic"
```

## 故障排除

1. **检查环境变量**：确保必要的环境变量已设置
2. **验证API密钥**：确认密钥有效且有足够权限
3. **网络连通性**：确保能访问配置的API端点
4. **查看日志**：启动时会显示加载的配置信息

## 配置热重载

系统支持配置热重载，修改配置文件后重启服务即可生效。