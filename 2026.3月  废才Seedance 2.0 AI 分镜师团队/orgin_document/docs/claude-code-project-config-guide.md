# Claude Code 配置提取与 project-config.json 填写指南

这份指南按你当前这台机器的实际情况写。

已确认的信息来源：

- VS Code 用户设置文件：`C:\Users\Galaxy\AppData\Roaming\Code\User\settings.json`
- Claude Code 主配置文件：`C:\Users\Galaxy\.claude\settings.json`
- 项目配置文件：`D:\workspace\废材\2026.3月  废才Seedance 2.0 AI 分镜师团队\project-config.json`

你当前机器上已经查到：

- Claude Code 扩展已安装
- Claude Code 的基础地址已配置：`http://2000.run:6543`
- Claude Code 的认证令牌已存在于 `C:\Users\Galaxy\.claude\settings.json`
- 当前项目走的是 `openai-compatible` 协议，不是 Claude 原生协议

## 1. 先理解这三种“配置”

你现在手里其实有三套不同层面的配置：

1. VS Code 扩展显示设置
   这类配置在 `settings.json` 里，比如 `claudeCode.preferredLocation`。

2. Claude Code 自己的连接配置
   这类配置在 `C:\Users\Galaxy\.claude\settings.json` 里，重点是：
   - `ANTHROPIC_BASE_URL`
   - `ANTHROPIC_AUTH_TOKEN`

3. 你这个项目自己的运行配置
   这类配置在 `project-config.json` 里。现在项目已经支持：
   - 顶层 `api` 作为默认 provider
   - 顶层 `providers` 定义多个 provider
   - `models.<role>.provider` 指定每个角色走哪个 provider

重点：项目代码不会自动读取 `C:\Users\Galaxy\.claude\settings.json`。  
它只会读取 `project-config.json` 里的“环境变量名”，然后去当前终端进程里找这个环境变量。

所以正确流程不是“把密钥直接写进 JSON”，而是：

1. 从 Claude 配置里查出地址和密钥来源
2. 把地址和“环境变量名”填进 `project-config.json` 的 Claude provider
3. 在运行项目前，把密钥导入当前 PowerShell 会话

## 2. 如何查询 Claude Code 已配置的信息

### 方法 A：直接看配置文件

打开：

```powershell
Get-Content -LiteralPath 'C:\Users\Galaxy\.claude\settings.json' -Raw
```

你会看到类似：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "...",
    "ANTHROPIC_BASE_URL": "http://2000.run:6543"
  }
}
```

这里最重要的是两项：

- `ANTHROPIC_BASE_URL`
- `ANTHROPIC_AUTH_TOKEN`

### 方法 B：用我给你加好的辅助脚本

在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File '.\script\show-claude-config.ps1'
```

这个脚本会帮你输出：

- Claude 配置文件路径
- 已检测到的基础地址
- 已检测到的令牌是否存在（只显示掩码，不显示完整密钥）
- 推荐填写到 `project-config.json` 的 Claude provider 配置块
- 当前 PowerShell 会话导入密钥的命令

## 3. 这些信息如何映射到 project-config.json

你当前项目的协议是 `openai-compatible`，项目代码实际会去请求：

- `.../responses`
或
- `.../chat/completions`

所以从 Claude 配置映射到项目配置时，要这样转换：

| Claude 配置来源 | 当前值 | project-config.json 对应字段 | 怎么填 |
|---|---|---|---|
| `ANTHROPIC_BASE_URL` | `http://2000.run:6543` | `providers.claude.base_url` | 改成 `http://2000.run:6543/v1` |
| `ANTHROPIC_AUTH_TOKEN` | 已存在 | `providers.claude.api_key_env` | 填 `ANTHROPIC_AUTH_TOKEN` |
| 无需从 Claude 提取 | - | `providers.claude.provider` | 保持 `openai-compatible` |
| 无需从 Claude 提取 | - | `providers.claude.wire_api` | 保持 `responses` |

注意：

- `base_url` 不是照抄 Claude 的值，而是要补上 `/v1`
- `api_key_env` 填的是“变量名”，不是密钥内容
- 不要把真实 token 直接写进 `project-config.json`

## 4. 你这个项目现在应该怎么填

你当前项目里推荐把 Claude 部分写成下面这段：

```json
"claude": {
  "provider": "openai-compatible",
  "base_url": "http://2000.run:6543/v1",
  "api_key_env": "ANTHROPIC_AUTH_TOKEN",
  "timeout_seconds": 300,
  "max_retries": 3,
  "wire_api": "responses"
}
```

现在这个项目已经支持 Codex 和 Claude 混用，所以 Claude 不再一定写在顶层 `api`。  
更稳妥的写法是把 Claude 放到 `providers.claude`，再由具体模型角色通过 `provider: "claude"` 去引用。

## 5. 最关键一步：把 Claude 的 token 导入当前 PowerShell 会话

只改 `project-config.json` 还不够。  
因为项目运行时只会读当前终端里的环境变量。

在你准备运行项目的那个 PowerShell 窗口里，执行：

```powershell
$claude = Get-Content -LiteralPath "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json
$env:ANTHROPIC_AUTH_TOKEN = $claude.env.ANTHROPIC_AUTH_TOKEN
```

执行完以后，这个 PowerShell 会话里就有可用密钥了。

## 6. 如果项目是 Codex + Claude 混用

如果项目同时使用两个 provider，那么运行前需要把两种凭据都导入到同一个 PowerShell 会话：

```powershell
$codex = Get-Content -LiteralPath "$env:USERPROFILE\.codex\auth.json" -Raw | ConvertFrom-Json
$env:OPENAI_API_KEY = $codex.OPENAI_API_KEY

$claude = Get-Content -LiteralPath "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json
$env:ANTHROPIC_AUTH_TOKEN = $claude.env.ANTHROPIC_AUTH_TOKEN
```

这样不同角色走不同 provider 时，运行时都能找到对应 token。

## 7. 手把手操作顺序

按下面顺序做就行：

1. 打开项目目录

```powershell
Set-Location 'D:\workspace\废材\2026.3月  废才Seedance 2.0 AI 分镜师团队'
```

2. 查看 Claude 当前配置

```powershell
powershell -ExecutionPolicy Bypass -File '.\script\show-claude-config.ps1'
```

3. 确认 `project-config.json` 里 Claude provider 这两项正确

```json
"base_url": "http://2000.run:6543/v1",
"api_key_env": "ANTHROPIC_AUTH_TOKEN"
```

4. 导入当前会话环境变量

```powershell
$claude = Get-Content -LiteralPath "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json
$env:ANTHROPIC_AUTH_TOKEN = $claude.env.ANTHROPIC_AUTH_TOKEN
```

5. 验证当前会话里是否已经有值

```powershell
if ($env:ANTHROPIC_AUTH_TOKEN) { 'token loaded' } else { 'token missing' }
```

6. 再运行你的项目命令

例如：

```powershell
python -m feicai_seedance.cli status
```

如果某个模型角色绑定到 `claude` provider，它就会按：

- `providers.claude.base_url`
- 当前会话中的 `ANTHROPIC_AUTH_TOKEN`

来调用接口。

## 8. 你现在这台机器上，哪些值已经明确，哪些还不能直接提取

已经明确的：

- Claude 基础地址：`http://2000.run:6543`
- Claude token 已存在
- Claude provider 应使用的兼容地址：`http://2000.run:6543/v1`
- Claude provider 应使用的环境变量名：`ANTHROPIC_AUTH_TOKEN`

不能直接从当前 Claude 配置里确定的：

- 你项目里各角色模型名是否一定要继续用 `gpt-5.4`
- 是否要把所有 `models.*.name` 改成别的模型

原因是当前 VS Code / Claude 配置里没有显式写出一个可直接复用到此项目的模型名配置。  
所以 `models` 这部分先保持你项目现状最稳妥。

## 9. 最容易犯错的地方

- 把真实 token 直接写进 `project-config.json`
- 直接把 `ANTHROPIC_BASE_URL` 原样填成 `api.base_url`，漏掉 `/v1`
- 只改了 JSON，没有把环境变量导入当前终端
- 在一个 PowerShell 窗口导入变量，却去另一个新开的窗口运行项目

## 10. 一句话结论

你现在最推荐的做法就是：

1. 在 `project-config.json` 里为 Claude 写一个 `providers.claude`
2. 每次运行项目前，在当前 PowerShell 窗口执行：

```powershell
$claude = Get-Content -LiteralPath "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json
$env:ANTHROPIC_AUTH_TOKEN = $claude.env.ANTHROPIC_AUTH_TOKEN
```

如果项目还混用了 Codex，再额外导入 `OPENAI_API_KEY` 即可。
