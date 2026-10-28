# Render 后端部署说明

更新日期：2026-10-29。仓库：[kkk714/FortuneTelling](https://github.com/kkk714/FortuneTelling)。

本轮只准备并上传部署配置，没有创建 Render 服务，也没有发布 Lovable 网页。按下面步骤创建服务后才会获得真实公网地址。

## 1. 这次增加的配置

- `render.yaml`：免费 Python Web Service、构建与启动命令、健康检查、关联 `main` 分支。
- `.python-version`：固定 Python `3.12.14`，与本机已验证的 API 环境一致。
- `.gitignore`：排除虚拟环境、缓存、本机环境变量和证书。
- `README.md`：其他人克隆后如何运行、本仓库与网页的关系。

云端使用 Uvicorn 监听 `0.0.0.0:$PORT`，无需修改本机的 `python api.py` 启动方式。业务接口和 JSON 字段保持现有版本，HTTPS 由 Render 处理。

## 2. 在 Render 创建后端

1. 登录 [Render 控制台](https://dashboard.render.com/)，选择 **New → Blueprint**。
2. 连接 GitHub，授权 Render 访问 `kkk714/FortuneTelling`。Codex 已能上传代码，不代表 Render 自动获得了 GitHub 授权。
3. 选择该仓库的 `main` 分支，Blueprint 文件使用根目录的 `render.yaml`。
4. 查看服务 `fortune-telling-api`，确认实例方案显示 **Free**，再创建。名称如有冲突，可另取名称，使用 Render 最终分配的地址。
5. 等待依赖安装与启动完成，服务状态应为 **Live**。如果失败，在日志中查看第一条错误。

如果改用手动创建 **Web Service**，填写：

| 配置项 | 值 |
| --- | --- |
| Repository | `kkk714/FortuneTelling` |
| Branch | `main` |
| Root directory | 留空，使用仓库根目录 |
| Runtime / Language | Python 3 |
| Build command | `python -m pip install -r requirements-api.txt` |
| Start command | `uvicorn api:app --host 0.0.0.0 --port $PORT` |
| Instance type | Free |
| Health check path | `/api/health` |
| Environment | `PYTHON_VERSION=3.12.14`、`PYTHONUNBUFFERED=1` |

不要把启动文件填成 `main.py`：它是需要键盘输入的终端菜单。网页调用的是 `api:app`。

## 3. 确认真实 HTTPS 地址

复制 Render 服务页面显示的完整 HTTPS 地址。不要按服务名称猜域名；地址可能带有额外后缀。

在该地址后分别加上 `/api/health` 和 `/docs` 打开。健康检查应返回：

```json
{"status":"ok","api_version":"1.0.0"}
```

进入 `/docs`，用现有示例测试 `POST /api/report` 与 `POST /api/draw`。接口示例见 [API接口说明](API接口说明.md)。此时只是 API 上线，完整网站还需要前端接入。

## 4. 允许 Lovable 网页访问

在 Render 的 **Environment** 添加变量 `SUANMING_CORS_ORIGINS`，值为真实 Lovable 网页的来源。来源只包含协议、域名和必要端口，不带 `/` 结尾或页面路径。

例如，网页完整地址是 `https://你的实际域名/birth`，变量里只填 `https://你的实际域名`。这里的中文示意内容不是可使用的真实域名，请从 Lovable 页面地址栏复制。

- 生产发布地址与在线预览地址如果不同，分别加入，用英文逗号隔开。
- 不带引号，不填 `*`，不把 Render 自己的地址当成 Lovable 地址。
- 保存后按 Render 提示重新部署，让新环境变量生效。
- 设置此变量会替换本地默认允许列表。如果还需本机前端联调，可同时加入其实际来源，例如 `http://localhost:5173`。

配置没有预填此变量，因为还未拿到真实前端来源。不设置时，健康检查和 `/docs` 可以使用，跨域网页访问仍只允许原来的本地开发来源。CORS 只控制浏览器跨域访问，不是账号权限或 API 密钥。

## 5. 给 Lovable 的内容

把 **Render 实际 HTTPS 基地址**、[Lovable公网接入补充说明](Lovable公网接入补充说明.md) 和原来的五页需求交给 Lovable，让它：

1. 保留已有页面与风格，统一修改 API 基地址；基地址不包含 `/api`。
2. 在线预览和发布环境都调用这个 HTTPS 后端。
3. 保留七个接口及现有字段、中英文、出生时区与同签语言切换约定。
4. 服务休眠唤醒时显示等待，随机抽签请求不自动重试。
5. 实际联调成功后发布网页，提供公众可以打开的网站链接。

用另一台设备测试出生输入、三主题报告、抽签、人物、语言切换与退出，确认无需启动自己的 Mac。

## 6. 之后更新代码

本配置让 Render 跟随 `main` 的提交自动部署。以 Render 最新部署记录与健康检查为准，GitHub 上传成功不代表部署一定成功。

Lovable 前端仍需在 Lovable 发布相应更新。后端重新部署不等于前端网页重新发布。

免费实例闲置 15 分钟会休眠，再次访问唤醒约需一分钟。先用于体验验证；暂不添加数据库或付费服务。

官方资料：[FastAPI 部署](https://render.com/docs/deploy-fastapi)、[Blueprint 配置](https://render.com/docs/blueprint-spec)、[Python 版本](https://render.com/docs/python-version)、[免费实例](https://render.com/docs/free)、[自动部署](https://render.com/docs/deploys)。
