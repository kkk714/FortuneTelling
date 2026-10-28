# Suanming 公网接入补充说明：给正在制作前端的 Lovable

日期：2026-10-29。

## 1. 本次目标变更与优先级

用户最终目标已明确为：**任何人打开网站网址即可使用，不必下载代码、安装 Python 或在自己电脑启动服务。**

采用以下最小改动路线：

- Python FastAPI 后端：部署到 Render 的 Python Web Service。
- 已有 Lovable 前端：保留当前项目和页面，继续在 Lovable 发布。
- GitHub：保存和同步源代码；当前 Render 使用公开仓库 URL，后续更新需手动部署。

本文补充并覆盖《Lovable本地Web需求说明.md》中“仅在用户本机运行”“公网部署留到以后”等部署范围约定。原文的五页结构、业务逻辑、数据字段、中英文规则、状态管理、同签语言切换与双语签文快照继续有效。

请继续当前已经制作的页面，保留已有视觉成果。本次不要求重新设计页面或重新讨论已确认的风格，不新增页面、数据库、登录、历史记录，也不重写 Python 业务逻辑。

**当前状态：后端 HTTPS 已部署并验证，前端未接入／未发布。** Render 服务为 Live、Free，区域 Oregon。实际 API 基地址是 [https://fortune-telling-api-rlt2.onrender.com](https://fortune-telling-api-rlt2.onrender.com)。健康、七个接口及四个具体 Lovable 来源的 CORS 均已完成线上检查。

Lovable 前端尚未发布，尚未确认与此后端连接成功。Publish 界面计划域名是 `https://doc-to-dreamsite.lovable.app`，当前预览来源是 `https://preview--doc-to-dreamsite.lovable.app`；二者不能混写成已验收的公众网站。

服务记录与 CORS 来源见[Render部署说明](Render部署说明.md)。[服务控制台](https://dashboard.render.com/web/srv-dbh8gko473hc7397mgrg) 和 [Blueprint](https://dashboard.render.com/blueprint/exs-dbh8gbe1egvs73eqokpg) 是账号管理入口，不是面向访问者的网站。

## 2. 用人话理解这三个地方

| 地方 | 在本项目里的作用 |
| --- | --- |
| GitHub | 存放代码，保留修改记录 |
| Render | 让现有 Python 程序在网上运行，提供 HTTPS API 地址 |
| Lovable | 制作和发布用户打开后看到的网页，提供网站地址 |

用户只打开 Lovable 发布的网站。网页把出生信息或抽签请求发送给 Render，Render 使用现有 Python 代码处理并返回结果，网页负责展示。

```text
用户浏览器 → Lovable 发布的网页 → Render 上的 Python API
```

完成后端验收、前端接入与网站发布后，用户的 Mac 不需要保持开机。平台提供的网站地址可用于公开体验，不必先准备自有域名。

## 3. 后端部署约定：由后端维护方完成

Render 使用原生 Python Web Service，不要求前端改写后端，也不需要把前端迁入 Python 服务。

仓库中的部署配置：

| 配置项 | 值 |
| --- | --- |
| Python | 固定为已经验证的 `3.12.14` |
| Build command | `python -m pip install -r requirements-api.txt` |
| Start command | `uvicorn api:app --host 0.0.0.0 --port $PORT` |
| Health check | `/api/health` |
| 业务数据 | 使用同一仓库中的两份规则 JSON 及既有人物资料 |

服务已通过公开仓库 URL 创建，业务与跨域验收通过。线上通过上面的 Uvicorn 命令监听平台端口，本机原启动方式可继续保留。

真实地址为 `https://fortune-telling-api-rlt2.onrender.com`。[健康检查](https://fortune-telling-api-rlt2.onrender.com/api/health) 已返回 `200`、`ok`、版本 `1.0.0`；[交互文档](https://fortune-telling-api-rlt2.onrender.com/docs) 与 [OpenAPI](https://fortune-telling-api-rlt2.onrender.com/openapi.json) 完整提供七个接口。HTTPS 由平台处理，不要求先为用户的 Mac 配置本地可信证书。

`render.yaml` 已将以下四个具体来源加入 `SUANMING_CORS_ORIGINS`，四项线上预检均已通过：

```text
https://doc-to-dreamsite.lovable.app
https://preview--doc-to-dreamsite.lovable.app
https://id-preview--20989e88-1876-429e-accf-5a000bbdbaa3.lovable.app
https://20989e88-1876-429e-accf-5a000bbdbaa3.lovableproject.com
```

第一项是计划发布来源，其余是已经观察到的预览／项目来源；CORS 通过不等于网页已发布或联调成功。正常报告和参数错误的跨域响应也已验证，未允许来源的预检被拒绝。来源不包含页面路径。

线上报告、日期及 DST 校验、英文桃花抽签与中英文人物匹配均已检查。百科部分简介不可用：中文三位均返回备用说明；英文仅 Elvis Presley 本次获取成功，另外两位使用备用说明。匹配与原文链接正常，前端应继续遵守 `biography.available=false` 的降级约定。

先使用免费实例进行体验验证。免费实例闲置后可能休眠，首次唤醒需要等待。是否以后升级常驻规格，由用户根据使用体验另行决定。

## 4. Lovable 需要调整的内容

### 4.1 统一使用实际公网 API 地址

所有 API 请求都经过一个集中配置的基地址：健康检查、城市、主题、出生验证、报告、抽签、人物查询都一样。

- 生产环境和 Lovable 在线预览：使用 `https://fortune-telling-api-rlt2.onrender.com`；后端已验收，前端联调仍待完成。
- 开发者在自己电脑本地联调：可以显式配置 `http://127.0.0.1:8000`。
- 基地址不包含 `/api`，请求路径继续使用 `/api/chart` 等。
- 不要简单使用“开发模式就连接 localhost”的判断；Lovable 在线预览也可能是开发模式。
- 检查是否存在写死的本机地址、只在本地有效的代理配置，或调用到了前端自身的同名路径。

根据当前前端实际框架选配置方式。如果是 Vite，可以继续使用 `VITE_API_BASE_URL`；如果是其他框架，使用该框架的公开配置约定，不为套用变量名而迁移整个项目。

如果使用 Vite，可将公开配置设为：

```dotenv
VITE_API_BASE_URL=https://fortune-telling-api-rlt2.onrender.com
```

基地址已提供，但是否真正联通仍以浏览器请求结果为准；失败时如实显示连接状态，不用模拟结果冒充成功。

### 4.2 页面和 API 契约继续保留

仍是以下七个接口，方法、请求字段和响应字段不变：

```text
GET  /api/health
GET  /api/topics?language=zh
GET  /api/cities?language=zh
POST /api/chart
POST /api/report
POST /api/draw
POST /api/people
```

仍保留五个页面：出生信息、功能菜单、主题解读、抽签结果、相似人物。页面的现有代码无需因为后端上线而整体重做。

出生信息输入仍是 `birth.date/time/timezone/fold`。网站先验证出生信息，再进入菜单；选择哪项就显示哪项。后端仍不存用户会话，前端继续保存当前体验的数据。

抽签切换语言仍按原文第 6、10 节，用同一 `(topic,id)` 和真实双语快照取另一语言文案；不能改成重新调用随机抽签接口。

### 4.3 调整等待、失败与重试提示

公开网站使用面向普通用户的提示，例如“服务正在准备，请稍候”或“暂时无法连接，请重试”。不要让访问者执行 Python 命令或启动本机后端。

考虑免费后端休眠后的较长启动时间：

- 可以用安全的 `GET /api/health` 检测服务是否准备好，并显示加载状态。
- 不要因为很短的前端超时就立即认定服务永久不可用；等待应可取消，失败时允许用户主动重试。
- `POST /api/draw` 不做自动重试，也不能因为服务唤醒、页面挂载或切换语言重复发起抽签。
- 人物查询还可能等待外部百科，继续保留单独的加载提示和已有的降级显示。

### 4.4 公开发布与代码同步

前端后续仍由 Lovable 发布，发布时确认网站允许公众访问并测试实际网址。目前尚未发布；`https://doc-to-dreamsite.lovable.app` 只是 Publish 界面的计划域名。

GitHub 同步用于保存代码和同步编辑器，不能把“同步成功”当成“已发布网站已更新”。在 Lovable 修改前端后，仍需发布相应更新。当前 Render 未安装 GitHub 仓库集成，`autoDeployTrigger: off`；代码推送到 `main` 后要手动选择 **Deploy latest commit**。前后端发布状态分别确认。

## 5. 联调顺序

1. 已完成：后端代码与部署配置放入 GitHub，使用公开仓库 URL 创建 Render Blueprint 和免费服务。
2. 已完成：真实 HTTPS 健康、接口业务与四个具体来源的跨域检查。
3. 待完成：Lovable 使用上述真实基地址，在当前预览中验证请求。
4. 待完成：验证出生信息、解读、抽签、同签语言切换、人物与退出，修正联调问题。
5. 待完成：由用户确认并发布前端，再从真实发布网址验收和分享。

本次后端部署已由用户授权执行；后端 HTTPS 已部署并验证，不表示前端已经连接或发布。

## 6. 公网验收标准

- 使用另一台电脑或手机，直接打开网站即可使用，不需要连接用户的 Mac。
- 在线前端请求的是 Render 的真实 HTTPS API，不是 `127.0.0.1`。
- 线上五页、中文与英文、输入错误、冬夏令时与退出行为均按原需求运行。
- 修改出生信息后旧结果失效；离开页面或退出后的旧响应不能覆盖状态。
- 抽签只在主动选择抽签或再抽一次时发生；语言切换保持主题和签号。
- 百科不可用时仍显示匹配人物、备用说明和原文链接。
- 休眠唤醒时有明确等待提示，抽签不会因为重试产生额外调用。
- 页面刷新、直接进入结果路由与浏览器前进／后退正常。
- 前后端发布状态分别核对，不能只依据 GitHub 同步成功判断网站已经更新。

## 7. 可以直接发给 Lovable 的补充消息

> 请保留当前五个页面、交互和视觉成果，继续现有项目。后端 HTTPS 已部署并验证，实际 API 基地址是 https://fortune-telling-api-rlt2.onrender.com ，基地址不含 /api；沿用原来的七个接口和 JSON 契约。四个具体 Lovable 来源的 CORS 已通过，下一步请在当前前端实际接入和联调；不要提前宣称已连接或发布。Publish 界面计划域名是 doc-to-dreamsite.lovable.app，当前预览为 preview--doc-to-dreamsite.lovable.app。人物接口的 available=false 是正常降级，请保留备用说明和原文链接。继续处理免费后端唤醒等待；随机抽签不自动重试，切换语言保留同一签。联调通过后，再由用户确认前端发布。

官方资料（核对日期 2026-10-29）：[Render 部署 FastAPI](https://render.com/docs/deploy-fastapi)、[Render Python 版本配置](https://render.com/docs/python-version)、[Render 免费实例限制](https://render.com/docs/free)、[Render 自动部署](https://render.com/docs/deploys)、[Lovable 网站发布](https://docs.lovable.dev/features/publish)。
