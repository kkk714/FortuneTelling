# Render 后端部署说明

更新日期：2026-10-29。仓库：[kkk714/FortuneTelling](https://github.com/kkk714/FortuneTelling)。

**当前状态：后端 HTTPS 已部署并验证，Lovable 网站已发布；整站流程待手动验收。** Render 服务为 Live、Free，区域 Oregon。真实 HTTPS 业务与跨域检查已通过。

| 项目 | 实际地址 |
| --- | --- |
| API 基地址 | [https://fortune-telling-api-rlt2.onrender.com](https://fortune-telling-api-rlt2.onrender.com) |
| 公开网站 | [Suanming 五行体验](https://doc-to-dreamsite.lovable.app) |
| 服务控制台 | [Render Web Service](https://dashboard.render.com/web/srv-dbh8gko473hc7397mgrg) |
| Blueprint | [Render Blueprint](https://dashboard.render.com/blueprint/exs-dbh8gbe1egvs73eqokpg) |

控制台和 Blueprint 链接用于账号内管理，不是给访问者使用的网站链接。

## 1. 这次增加的配置

- `render.yaml`：免费 Python Web Service、构建与启动命令、健康检查、关联 `main` 分支。
- `.python-version`：固定 Python `3.12.14`，与本机已验证的 API 环境一致。
- `.gitignore`：排除虚拟环境、缓存、本机环境变量和证书。
- `README.md`：其他人克隆后如何运行、本仓库与网页的关系。

云端使用 Uvicorn 监听 `0.0.0.0:$PORT`，无需修改本机的 `python api.py` 启动方式。业务接口和 JSON 字段保持现有版本，HTTPS 由 Render 处理。

## 2. 已采用的创建方式

账号注册和邮箱验证已完成。当前使用公开仓库 URL `https://github.com/kkk714/FortuneTelling` 创建 Blueprint 和免费 Python 服务，读取 `main` 分支根目录的 `render.yaml`。服务已经创建，不需要重复新建。

本次没有安装 GitHub 仓库集成。配置中的 `autoDeployTrigger: off` 已关闭自动部署，后续代码更新按第 6 节手动发布。

以下参数供核对服务配置或以后重建时参考：

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

实际基地址为 `https://fortune-telling-api-rlt2.onrender.com`，不是按服务名称推测的占位地址。前端基地址不要加 `/api`。

已实际验证 [健康接口](https://fortune-telling-api-rlt2.onrender.com/api/health)、[交互文档](https://fortune-telling-api-rlt2.onrender.com/docs) 和 [OpenAPI](https://fortune-telling-api-rlt2.onrender.com/openapi.json)。Swagger 浏览器界面完整显示七个接口，健康检查返回 `200`：

```json
{"status":"ok","api_version":"1.0.0"}
```

线上还已验证中英文主题／城市、三主题中英文报告、非法日期、悉尼 DST 空缺／重复及 `fold=1`、一次英文桃花抽签、中英文各三位人物。接口示例见 [API接口说明](API接口说明.md)。网站已发布，整站业务流程仍待手动验收。

百科实际结果并非全部成功：中文三位均为 `available=false`；英文 Elvis Presley 可用，Pope Benedict XVI 和 Serge Gainsbourg 不可用。人物匹配、备用说明与原文链接均正常返回。

## 4. 允许 Lovable 网页访问

`render.yaml` 的 `SUANMING_CORS_ORIGINS` 已加入以下四个具体来源，线上预检均返回 `200` 和精确匹配的允许来源：

| 来源 | 当前用途 |
| --- | --- |
| `https://doc-to-dreamsite.lovable.app` | 已发布的公开网站 |
| `https://preview--doc-to-dreamsite.lovable.app` | 已观察到的当前预览来源 |
| `https://id-preview--20989e88-1876-429e-accf-5a000bbdbaa3.lovable.app` | 已观察到的另一预览来源 |
| `https://20989e88-1876-429e-accf-5a000bbdbaa3.lovableproject.com` | 已观察到的项目来源 |

正常报告 `200` 与日期错误 `422` 响应均已检查 CORS；未允许来源的预检返回 `400`，不带允许来源头。来源只包含协议、域名和必要端口，不带 `/` 结尾或页面路径。本次另已确认实际发布来源的 API `GET`／`OPTIONS`；整站验收范围见下节。

- 生产发布地址与在线预览地址如果不同，分别加入，用英文逗号隔开。
- 不带引号，不填 `*`，不把 Render 自己的地址当成 Lovable 地址。
- 保存后按 Render 提示重新部署，让新环境变量生效。
- 设置此变量会替换本地默认允许列表。如果还需本机前端联调，可同时加入其实际来源，例如 `http://localhost:5173`。

CORS 只控制浏览器跨域访问，不是账号权限或 API 密钥。以后前端来源改变时更新此配置并重新部署，再验证浏览器实际请求。

## 5. 给 Lovable 的内容

后端验收已通过，网站已发布于 [https://doc-to-dreamsite.lovable.app](https://doc-to-dreamsite.lovable.app)。后续继续按[Lovable公网接入补充说明](Lovable公网接入补充说明.md)和原来的五页需求核对：

1. 保留已有页面与风格，统一使用实际 API 基地址；基地址不包含 `/api`。
2. 核对在线预览和发布环境都调用这个 HTTPS 后端。
3. 保留七个接口及现有字段、中英文、出生时区与同签语言切换约定。
4. 服务休眠唤醒时显示等待，随机抽签请求不自动重试。
5. 从已发布网址完成整站流程的手动验收；后续前端修改仍需重新发布。

本次已确认公开首页 `200`（标题为“出生信息 · Suanming 五行体验”）、动态城市列表和中英文首页切换。自动化未能完成浏览器日期控件填写，提交生日→菜单→报告／抽签／人物→返回／退出尚未完成整站 E2E，留给用户手动确认；可用另一台设备继续测试。

## 6. 之后更新代码

当前没有 GitHub 仓库集成，自动部署已关闭。更新代码后先推送到公开仓库 `main`，再在服务控制台手动选择 **Deploy latest commit**；以最新部署记录与健康检查为准。GitHub 上传成功不代表线上版本已更新。

Lovable 前端仍需在 Lovable 发布相应更新。后端重新部署不等于前端网页重新发布。

免费实例闲置后可能休眠，首次唤醒需要等待。先用于体验验证；暂不添加数据库或付费服务，抽签请求不得因等待而自动重试。

官方资料：[FastAPI 部署](https://render.com/docs/deploy-fastapi)、[Blueprint 配置](https://render.com/docs/blueprint-spec)、[Python 版本](https://render.com/docs/python-version)、[免费实例](https://render.com/docs/free)、[自动部署](https://render.com/docs/deploys)。
