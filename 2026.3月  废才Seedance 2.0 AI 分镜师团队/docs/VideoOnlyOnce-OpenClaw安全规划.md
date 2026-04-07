# VideoOnlyOnce OpenClaw 安全规划

## 1. 目的

本文件定义 `VideoOnlyOnce` 项目中使用 `OpenClaw` 的安全边界、部署方式、权限模型和操作规则。

核心目标不是“把 OpenClaw 配到能跑”，而是：

- 让它只做必要的网页自动化
- 不让它接触不必要的账号、数据和系统权限
- 在发生误操作、被诱导、被注入、被劫持时，损失可控且可追溯

## 2. 先给结论

`OpenClaw` 在这个项目里应被视为：

- 高风险浏览器自动化执行器

而不应被视为：

- 项目总控
- 主工作机上的全权限助手
- 可以自由安装技能和访问任意网页的通用代理

最安全的规划是：

- `fenjing_program` 做总控和结构化生产
- `zaomeng` 或受控适配层做任务投递
- `OpenClaw` 只运行在隔离环境中，负责少量、固定、白名单化的网页动作

## 3. 为什么 OpenClaw 在本项目里风险高

结合 OpenClaw 官方文档和你的项目形态，主要风险有 6 类。

## 3.1 Host 权限过大

OpenClaw 官方仓库明确写到，默认情况下主会话工具跑在 host 上，agent 对 host 有完整访问能力。  
这意味着如果把它直接跑在你的日常工作机上，它理论上能接触：

- 项目代码
- 本地下载目录
- 浏览器登录态
- SSH key
- 其他文档
- 其他网站 cookie

对 `VideoOnlyOnce` 而言，这种默认权限过大。

## 3.2 浏览器登录态是高价值目标

OpenClaw 官方浏览器文档明确支持受控浏览器、host browser、profile 选择和手工登录。  
一旦浏览器 profile 暴露，风险不仅是“即梦账号被盗”，还包括：

- 历史站点登录态泄露
- 同机其他网页会话被顺带访问
- agent 被恶意页面诱导去点击、下载、上传

## 3.3 Prompt Injection / 恶意页面诱导

浏览器代理的天然风险是：

- 页面内容本身可能诱导 agent 改变目标
- 页面可出现隐藏文本、伪按钮、虚假确认框
- agent 可能把网页文本误当成系统指令

对你这个项目特别危险的场景包括：

- 下载了恶意文件
- 跳转到了非即梦站点
- 上传了错误素材
- 误点发布、删除、续费、升级、充值类按钮

## 3.4 网关暴露风险

OpenClaw 官方网关文档反复强调：

- `gateway.bind` 应优先保持 `loopback`
- 非 loopback 绑定必须启用 token 或 password

如果错误暴露 Gateway：

- 远程控制面会变成攻击入口
- 风险不是单一浏览器，而是整个 agent 控制面

## 3.5 技能 / 插件 / 第三方代码供应链风险

你项目后续一定会有“再装个 skill 更方便”的诱惑。  
这类供应链风险在 agent 系统里很常见，因为技能往往等价于本地执行权限扩展。

## 3.6 项目数据本身敏感

你的项目包含：

- 原创小说
- 角色设计
- 分镜结构
- 生成素材
- 配音脚本

这些未发布资产本身就属于高价值内容，不应该被浏览器代理随意访问和外发。

## 4. 参考依据

本规划主要参考以下公开资料：

- OpenClaw 官方浏览器文档：浏览器默认在 sandbox 中运行，并建议用 `blocked_domains`、不要把凭据写入配置、生产环境不要忽略 SSL 错误
- OpenClaw 官方浏览器登录文档：推荐手工登录，不要把账号密码给模型；严格站点更建议 host browser 手工登录
- OpenClaw 官方网关安全文档：推荐 `bind: loopback`、token 认证、最小暴露面
- OpenClaw 官方仓库安全模型说明：主会话默认 host 全权限
- OWASP Secrets Management Cheat Sheet：凭据最小范围、短生命周期、可审计、不要明文落盘
- NIST 2026-02-17 发布的 AI Agent Standards Initiative：强调 agent 的安全、身份和可信采用

## 5. 本项目的安全总原则

固定采用以下原则：

- 最小权限
- 默认拒绝
- 白名单访问
- 人工登录
- 账号隔离
- 环境隔离
- 明确审计
- 可熔断
- 可回滚

## 6. 架构边界

## 6.1 角色分工

### 总控层

- `fenjing_program`
- `zaomeng`

职责：

- 读取剧本和知识库
- 生成任务文件
- 做审核和状态控制
- 做资产登记

总控层不能依赖 OpenClaw 决策。

### 执行层

- `OpenClaw`

职责只能包括：

- 打开已批准域名
- 输入指定 prompt
- 上传指定文件
- 触发生成
- 等待完成
- 下载到指定目录

执行层不负责：

- 改 prompt 策略
- 自由浏览互联网
- 决定是否继续流程
- 读整个项目目录
- 访问邮箱、IM、网盘、支付页面

## 6.2 最佳部署形态

推荐使用：

- 独立虚拟机或独立容器宿主机
- 专用系统用户
- 专用浏览器 profile
- 专用即梦账号

不推荐使用：

- 个人主力电脑
- 和日常浏览器共用 profile
- 和代码开发环境共用主目录

## 7. 必须落地的 10 条硬规则

## 7.1 规则 1：OpenClaw 不得运行在你的日常主工作环境

建议专门准备：

- `videoonlyonce-browser-worker`

这个 worker 只负责网页自动化，不存开发 SSH key，不装个人 IM，不登录个人邮箱。

## 7.2 规则 2：OpenClaw 只使用专用浏览器 profile

官方文档本身就建议用独立的 `openclaw` profile。  
在本项目里必须升级为硬规则：

- 禁止复用个人 Chrome profile
- 禁止复用日常办公浏览器 profile
- 禁止同 profile 登录无关站点

## 7.3 规则 3：所有账号必须人工登录，agent 不得知道密码

OpenClaw 官方浏览器登录文档已经明确建议：

- 手工登录是推荐方式
- 不要把凭据给模型

本项目中必须固化为：

- agent 不读取用户名密码
- agent 不读取 MFA 秘钥
- agent 只消费已建立的登录态

## 7.4 规则 4：Gateway 默认只绑定 `loopback`

除非你有强需求，否则：

- `gateway.bind = loopback`

如果必须远程访问：

- 只通过 SSH tunnel 或 Tailscale
- 必须启用 token/password
- 不允许裸暴露到公网

## 7.5 规则 5：默认禁止 host browser control

官方文档说明，sandbox 会话若要访问 host browser，需要显式打开 `allowHostControl`。  
因此项目基线应设为：

- `allowHostControl = false`

只有在“手工登录维护窗口”中，才可临时打开，完成登录后立即关闭。

## 7.6 规则 6：域名白名单 + 敏感域名黑名单

OpenClaw 官方浏览器文档建议使用 `blocked_domains`。  
本项目必须同时做：

- allowlist
- blocklist

### allowlist 建议

- 即梦主站和必要子域
- 你的对象存储或内部素材域
- 必要的 TTS / 视频 API 域

### blocklist 建议

- 邮箱站点
- 网盘站点
- 银行和支付站点
- 社交媒体后台
- Git 托管平台
- 内网域名
- `localhost`
- `127.0.0.1`
- 私网网段映射域

## 7.7 规则 7：OpenClaw 不得拥有整个项目目录读写权

最安全做法是只挂载最小目录：

- 输入：
  - `tasks/incoming/`
- 输出：
  - `tasks/outgoing/`
  - `downloads/`

禁止直接让 OpenClaw 接触：

- 整个仓库根目录
- `~/.ssh`
- 其他项目
- 原始知识库全文
- 秘钥目录

## 7.8 规则 8：禁止安装来源不明的 skill / plugin

生产环境应采用：

- 固定镜像
- 固定版本
- 固定 skill 清单

不允许：

- 在线临时安装插件
- 让 agent 自己搜索并安装 skill
- 让 agent 自己修改安全配置

## 7.9 规则 9：下载文件必须进入隔离区

OpenClaw 下载的任何文件先进入：

- `downloads/quarantine/`

经过：

- 文件类型检查
- 扩展名与 MIME 检查
- 病毒扫描
- 哈希记录

之后才移动到正式目录。

## 7.10 规则 10：所有“有副作用动作”必须可审计、可人工拦截

尤其是：

- 上传文件
- 提交生成
- 删除素材
- 覆盖旧结果
- 发布或分享

这些动作必须：

- 记录日志
- 记录截图
- 记录任务 ID
- 保留人工中止开关

## 8. 推荐部署拓扑

```text
开发机
  -> 运行 fenjing_program / zaomeng
  -> 输出 task json

隔离执行机
  -> 运行 OpenClaw
  -> 只挂载 tasks/incoming + tasks/outgoing + downloads
  -> 使用专用 browser profile
  -> 只访问 allowlist 域名

审计与存储
  -> logs/
  -> screenshots/
  -> quarantine/
  -> approved/
```

## 9. 配置基线建议

以下是“安全意图”，不是逐字段保证与某一版本配置完全一致的官方样例。实现时仍应以 OpenClaw 当前官方配置文档为准。

```json
{
  "gateway": {
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token"
    }
  },
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "non-main",
        "browser": {
          "allowHostControl": false
        }
      }
    }
  },
  "security": {
    "blocked_domains": [
      "mail.*",
      "drive.*",
      "github.com",
      "gitlab.com",
      "localhost",
      "127.0.0.1"
    ],
    "ignore_ssl_errors": false
  }
}
```

项目内还应额外定义一层业务白名单：

```json
{
  "allowed_domains": [
    "jimeng.jianying.com",
    "your-approved-storage.example.com"
  ],
  "allowed_actions": [
    "open_generation_page",
    "upload_asset",
    "submit_generation",
    "download_result"
  ]
}
```

## 10. 凭据与密钥管理

参考 OWASP Secrets Management Cheat Sheet，本项目必须采用：

- 环境变量或 secrets manager
- 最小作用域
- 定期轮换
- 可追溯调用身份

### 硬性要求

- 禁止把密码写进 `config.yaml` 或仓库
- 禁止把 token 写进 prompt 文件
- 禁止把账号信息写进日志
- 不同环境使用不同账号和不同 token

### 推荐做法

- 浏览器登录态由人工建立
- API 类凭据放入 secrets manager
- 若某服务支持短期 token，则优先使用短期 token

## 11. 数据分级

对 `VideoOnlyOnce` 建议至少分 4 级：

### L1 公开数据

- 官方帮助页
- 平台公开说明

### L2 内部工作数据

- 普通任务文件
- 非核心日志

### L3 核心创作资产

- 原创小说
- 分镜
- 角色设计
- 参考图

### L4 高敏数据

- 登录态
- 账号密钥
- 支付信息
- 内部审计信息

OpenClaw 只允许直接接触：

- L2 的一部分
- L3 的经过筛选子集

默认不得接触：

- L4

## 12. 按项目阶段的安全控制

## 12.1 阶段 0：小说与知识库

不建议使用 OpenClaw。

原因：

- 这一阶段是纯文本理解与结构化抽取
- 没有必要引入浏览器自动化风险

建议：

- 全部在 `fenjing_program` 本地完成

## 12.2 阶段 1：角色锚定与分镜

OpenClaw 只用于“网页出图执行”，不用于“角色决策”。

建议：

- 角色关键词和 schema 在本地生成
- OpenClaw 只读取 `character-image-tasks.json`
- 它不读取完整小说

## 12.3 阶段 2：图片生成

这是 OpenClaw 的主要使用阶段。

控制项：

- 域名白名单
- 固定上传目录
- 固定下载目录
- 每次只处理一个任务批次
- 下载后进入隔离区
- 失败自动退出，不自由重试未知页面

## 12.4 阶段 3：视频生成

风险比图片更高，因为：

- 上传更多素材
- 页面状态更复杂
- 潜在副作用更多

建议：

- 视频阶段独立 worker
- 严格限制并发
- 提交生成前截图和二次确认

## 12.5 阶段 4：TTS 与后期

不建议使用 OpenClaw。

原因：

- 这部分更适合 API 或本地工具
- 浏览器不是必要依赖

## 13. 人工介入点

以下动作必须人工：

- 首次登录
- MFA
- 主角角色定稿
- 高价值任务首次运行
- 改平台 UI 后的恢复确认
- 关键视频片段最终放行
- 生产环境安全配置变更

以下动作可半自动：

- 打开生成页
- 输入 prompt
- 上传指定图片
- 等待生成
- 下载结果

## 14. 日志与审计

每次 OpenClaw 运行至少记录：

- `run_id`
- `task_id`
- `episode_id`
- 访问域名
- 上传文件路径
- 下载文件路径
- 截图路径
- 开始时间
- 结束时间
- 最终状态
- 失败原因

日志至少分三类：

- 操作日志
- 错误日志
- 审计日志

关键动作应配截图：

- 登录成功后
- 上传前
- 提交前
- 下载后

## 15. 熔断与应急

必须有以下熔断条件：

- 访问到白名单外域名
- 页面出现未知登录页
- 页面出现充值、支付、授权、分享按钮
- 下载到未知文件类型
- 单任务超时
- 单批次失败率超过阈值

触发后应执行：

1. 立即停止当前 agent
2. 冻结浏览器 profile
3. 保存截图和日志
4. 通知人工检查
5. 需要时重建 profile 和 token

## 16. 禁止事项

以下行为应明确禁止：

- 在个人主力机长期运行 OpenClaw 生产任务
- 使用个人浏览器 profile
- 让 agent 自动搜索并安装第三方 skill
- 让 agent 保存账号密码
- 让 agent 访问 GitHub、邮箱、网盘等无关站点
- 将原创全量资料直接暴露给网页执行器
- 把 OpenClaw 当作项目总控来调度所有步骤

## 17. 建议的项目落地策略

### 第一阶段

- 不引入 OpenClaw
- 先把 `fenjing_program + zaomeng + 本地审核` 跑通

### 第二阶段

- 只在图片阶段引入 OpenClaw
- 严格限制为专机、专号、专 profile、专域名

### 第三阶段

- 再扩展到视频阶段
- 继续保持独立 worker 和高审计

### 第四阶段

- 若平台提供正式 API，优先改为 API

原则很简单：

- 能不用浏览器，就不用浏览器
- 能用官方 API，就不用 agent 点网页

## 18. 最终建议

对 `VideoOnlyOnce` 而言，OpenClaw 的正确位置是：

- 受限网页执行器

不是：

- 创作中枢

最安全、最专业的设定是：

- 把创作逻辑和资产管理留在本地可控程序里
- 把 OpenClaw 限制在隔离环境、专用账号、专用 profile、白名单域名、固定动作、可审计日志这几个边界内
- 在登录、定稿、关键提交、最终放行处保留人工

只有这样，OpenClaw 带来的效率收益，才不会被安全和运营风险抵消。

## 19. 参考来源

- OpenClaw 浏览器自动化文档：https://openclawdoc.com/docs/agents/browser-automation/
- OpenClaw Browser 工具文档：https://docs.openclaw.ai/tools/browser
- OpenClaw Browser Login 文档：https://docs.openclaw.ai/tools/browser-login
- OpenClaw Gateway 安全文档：https://docs.openclaw.ai/gateway/security
- OpenClaw Gateway Network Model：https://docs.openclaw.ai/gateway/network-model
- OpenClaw Gateway CLI：https://docs.openclaw.ai/cli/gateway
- OpenClaw Sandboxing 文档：https://docs.openclaw.ai/gateway/sandboxing
- OpenClaw 官方仓库：https://github.com/openclaw/openclaw
- OWASP Secrets Management Cheat Sheet：https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- NIST AI Agent Standards Initiative：https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure
- OWASP Agent Security Initiative：https://owasp.org/www-project-top-10-for-large-language-model-applications/initiatives/agent_security_initiative/
