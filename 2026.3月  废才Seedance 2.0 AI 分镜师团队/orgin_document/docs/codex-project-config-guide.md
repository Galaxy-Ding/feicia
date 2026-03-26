# Codex 配置提取与 project-config.json 填写指南

这份指南按你当前这台机器的实际情况写。

已确认的信息来源：

- VS Code Codex 扩展目录：`C:\Users\Galaxy\.vscode\extensions\openai.chatgpt-0.4.79-win32-x64`
- Codex 主配置文件：`C:\Users\Galaxy\.codex\config.toml`
- Codex 认证文件：`C:\Users\Galaxy\.codex\auth.json`
- 项目配置文件：`D:\workspace\废材\2026.3月  废才Seedance 2.0 AI 分镜师团队\project-config.json`

你当前机器上已经查到：

- VS Code 里安装的是 OpenAI 官方 Codex 扩展
- Codex 当前模型：`gpt-5.4`
- Codex 当前 provider 类型：`custom`
- Codex 当前接口地址：`http://2000.run:6543/v1`
- Codex 当前接口协议：`responses`
- Codex 当前认证字段：`OPENAI_API_KEY`

## 1. Codex 配置和 Claude 配置的区别

Claude 主要看：

- `C:\Users\Galaxy\.claude\settings.json`

Codex 主要看：

- `C:\Users\Galaxy\.codex\config.toml`
- `C:\Users\Galaxy\.codex\auth.json`

也就是说，Codex 的模型连接信息不在普通 VS Code 的 `settings.json` 里。

## 2. 如何查询 Codex 已配置的信息

### 方法 A：直接看文件

查看 Codex 主配置：

```powershell
Get-Content -LiteralPath 'C:\Users\Galaxy\.codex\config.toml'
```

你当前能看到类似：

```toml
model = 'gpt-5.4'
model_provider = 'custom'
model_reasoning_effort = 'high'
[model_providers.custom]
base_url = 'http://2000.run:6543/v1'
name = 'shiba-cc'
requires_openai_auth = true
wire_api = 'responses'
```

查看认证文件：

```powershell
Get-Content -LiteralPath 'C:\Users\Galaxy\.codex\auth.json' -Raw
```

这里重点看的是：

- `OPENAI_API_KEY`

注意：不要把完整密钥直接贴到文档、聊天窗口或 `project-config.json` 里。

### 方法 B：用项目里的辅助脚本

在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File '.\script\show-codex-config.ps1'
```

这个脚本会输出：

- Codex 配置文件路径
- Codex 认证文件路径
- 当前模型名
- 当前 base URL
- 当前 wire API
- 是否检测到 `OPENAI_API_KEY`
- 推荐填写到 `project-config.json` 的 provider 配置块
- 导入当前会话环境变量的命令

## 3. Codex 信息如何映射到 project-config.json

Codex 当前配置与项目配置的映射关系如下：

| Codex 配置来源 | 当前值 | project-config.json 对应字段 | 怎么填 |
|---|---|---|---|
| `config.toml -> base_url` | `http://2000.run:6543/v1` | `providers.codex.base_url` | 原样填写 |
| `auth.json -> OPENAI_API_KEY` | 已存在 | `providers.codex.api_key_env` | 填 `OPENAI_API_KEY` |
| `config.toml -> wire_api` | `responses` | `providers.codex.wire_api` | 填 `responses` |
| `config.toml -> model` | `gpt-5.4` | `models.*.name` | 按需填到用 Codex 的角色上 |

## 4. 你当前项目里推荐的 Codex provider 块

```json
"codex": {
  "provider": "openai-compatible",
  "base_url": "http://2000.run:6543/v1",
  "api_key_env": "OPENAI_API_KEY",
  "timeout_seconds": 300,
  "max_retries": 3,
  "wire_api": "responses"
}
```

## 5. 如何把 Codex 的 token 导入当前 PowerShell 会话

在你准备运行项目的那个 PowerShell 窗口里执行：

```powershell
$codex = Get-Content -LiteralPath "$env:USERPROFILE\.codex\auth.json" -Raw | ConvertFrom-Json
$env:OPENAI_API_KEY = $codex.OPENAI_API_KEY
```

执行后，这个 PowerShell 会话里就能让项目读取到 Codex 所需 token。

## 6. 现在项目是否支持“Codex + Claude 混用”

支持，已经改成可按模型角色指定 provider。

配置规则是：

1. 顶层 `api`
   仍然保留，作为默认 provider，兼容旧版本配置。

2. 顶层 `providers`
   用来声明多个 provider，例如：
   - `codex`
   - `claude`

3. `models.<role>.provider`
   用来指定某个角色到底走哪个 provider。

## 7. 你要的混用写法

你提的需求是：

- `orchestrator` 用 Codex
- `director_generate` 用 Codex
- `director_review` 用 Codex
- `art_designer` 用 Claude
- `storyboard_artist` 用 Claude
- `compliance_review` 用 Claude

当前项目已经按这个方式配置好了，核心结构如下：

```json
{
  "api": {
    "provider": "openai-compatible",
    "base_url": "http://2000.run:6543/v1",
    "api_key_env": "OPENAI_API_KEY",
    "timeout_seconds": 300,
    "max_retries": 3,
    "wire_api": "responses"
  },
  "providers": {
    "codex": {
      "provider": "openai-compatible",
      "base_url": "http://2000.run:6543/v1",
      "api_key_env": "OPENAI_API_KEY",
      "timeout_seconds": 300,
      "max_retries": 3,
      "wire_api": "responses"
    },
    "claude": {
      "provider": "openai-compatible",
      "base_url": "http://2000.run:6543/v1",
      "api_key_env": "ANTHROPIC_AUTH_TOKEN",
      "timeout_seconds": 300,
      "max_retries": 3,
      "wire_api": "responses"
    }
  },
  "models": {
    "orchestrator": { "name": "gpt-5.4", "provider": "codex" },
    "director_generate": { "name": "gpt-5.4", "provider": "codex" },
    "director_review": { "name": "gpt-5.4", "provider": "codex" },
    "art_designer": { "name": "gpt-5.4", "provider": "claude" },
    "storyboard_artist": { "name": "gpt-5.4", "provider": "claude" },
    "compliance_review": { "name": "gpt-5.4", "provider": "claude" }
  }
}
```

## 8. 运行混合配置前，必须同时导入两类 token

如果项目中同时存在 Codex provider 和 Claude provider，那么运行前必须把两种环境变量都导入到同一个 PowerShell 会话里：

```powershell
$codex = Get-Content -LiteralPath "$env:USERPROFILE\.codex\auth.json" -Raw | ConvertFrom-Json
$env:OPENAI_API_KEY = $codex.OPENAI_API_KEY

$claude = Get-Content -LiteralPath "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json
$env:ANTHROPIC_AUTH_TOKEN = $claude.env.ANTHROPIC_AUTH_TOKEN
```

如果只导入其中一个，那么走另一个 provider 的角色在运行时会报缺少环境变量。

## 9. 手把手操作顺序

1. 进入项目目录

```powershell
Set-Location 'D:\workspace\废材\2026.3月  废才Seedance 2.0 AI 分镜师团队'
```

2. 查看 Codex 当前配置

```powershell
powershell -ExecutionPolicy Bypass -File '.\script\show-codex-config.ps1'
```

3. 查看 Claude 当前配置

```powershell
powershell -ExecutionPolicy Bypass -File '.\script\show-claude-config.ps1'
```

4. 导入 Codex 和 Claude 两种 token

```powershell
$codex = Get-Content -LiteralPath "$env:USERPROFILE\.codex\auth.json" -Raw | ConvertFrom-Json
$env:OPENAI_API_KEY = $codex.OPENAI_API_KEY

$claude = Get-Content -LiteralPath "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json
$env:ANTHROPIC_AUTH_TOKEN = $claude.env.ANTHROPIC_AUTH_TOKEN
```

5. 验证两种变量都已存在

```powershell
if ($env:OPENAI_API_KEY) { 'OPENAI_API_KEY loaded' } else { 'OPENAI_API_KEY missing' }
if ($env:ANTHROPIC_AUTH_TOKEN) { 'ANTHROPIC_AUTH_TOKEN loaded' } else { 'ANTHROPIC_AUTH_TOKEN missing' }
```

6. 再运行项目

```powershell
python -m feicai_seedance.cli status
python -m feicai_seedance.cli start ep01
```

## 10. 结论

你问的这件事现在可以明确回答：

可以。  
而且项目现在已经支持把不同模型角色绑定到不同 provider / 不同 token 类型。

你当前这台机器上最适合的混用方式就是：

- 导演链路和编排链路走 Codex：`OPENAI_API_KEY`
- 服化道、分镜、合规链路走 Claude：`ANTHROPIC_AUTH_TOKEN`
