# FortuneTelling · 八字与主题抽签

一个 Python 终端程序和 FastAPI 后端，支持中文与英文：

- 输入出生地时区、日期与时间，处理冬夏令时并计算四柱、表层五行计数。
- 按财运、学习运、桃花运查询主题解读，或单独抽取主题签文。
- 从 30 位有出生资料来源的人物中匹配五行最多项相似的人物，获取百科简介。

解读与人物匹配供传统文化娱乐和阅读参考。程序目前不连接数据库，不提供账号、登录或长期历史记录；人物简介需要联网，无法获取时仍保留人物与来源链接。

## 项目状态

本仓库包含后端、终端程序、规则数据与接入文档。Lovable 发布的网页不在本仓库中。

**当前状态：后端 HTTPS 已部署并验证，Lovable 网站已发布；整站流程待手动验收。** Render 服务为 Live、Free，区域 Oregon；通过公开仓库 URL 部署。

- API 基地址：[https://fortune-telling-api-rlt2.onrender.com](https://fortune-telling-api-rlt2.onrender.com)
- 已验证入口：[健康检查](https://fortune-telling-api-rlt2.onrender.com/api/health)、[交互文档](https://fortune-telling-api-rlt2.onrender.com/docs)、[OpenAPI](https://fortune-telling-api-rlt2.onrender.com/openapi.json)。
- 公开网站：[Suanming 五行体验](https://doc-to-dreamsite.lovable.app)。

线上已检查中英文主题与报告、出生时间错误、抽签、人物匹配和四个具体 Lovable 来源的 CORS。百科部分简介不可用时会返回备用说明和原文链接，未宣称全部简介获取成功。

本次网站检查已确认首页 `200`、动态城市列表、中英文首页切换及发布来源的 API `GET`／`OPTIONS`。自动化未能完成日期控件填写，提交生日→菜单→报告／抽签／人物→返回／退出的整站流程仍待用户手动确认。

```text
用户浏览器 → Lovable 发布的网页 → Render 上的 FastAPI 后端
```

## 在自己电脑运行

安装 Python 3.12。以下命令适用于 macOS / Linux，在终端逐行运行：

```bash
git clone https://github.com/kkk714/FortuneTelling.git
cd FortuneTelling
python3.12 -m venv .venv-api
./.venv-api/bin/python3 -m pip install -r requirements-api.txt
./.venv-api/bin/python3 api.py
```

保持终端运行，打开 [API 交互文档](http://127.0.0.1:8000/docs) 或 [健康检查](http://127.0.0.1:8000/api/health)。按 `Ctrl+C` 停止服务。

体验终端菜单时，在同一目录运行：

```bash
./.venv-api/bin/python3 main.py
```

这台 Mac 已有的 `.venv` 和 `.venv-api` 可以继续使用。虚拟环境不会上传；其他人克隆后按上述命令安装依赖。

## 部署到 Render

仓库根目录的 `render.yaml` 定义免费 Python Web Service：

| 配置 | 值 |
| --- | --- |
| Python | `3.12.14` |
| 构建命令 | `python -m pip install -r requirements-api.txt` |
| 启动命令 | `uvicorn api:app --host 0.0.0.0 --port $PORT` |
| 健康检查 | `/api/health` |
| 部署分支 | `main` |
| 自动部署 | 关闭，`autoDeployTrigger: off` |
| 后续代码更新 | Render 中手动选择 `Deploy latest commit` |

当前通过公开仓库 URL 创建 [Render 服务](https://dashboard.render.com/web/srv-dbh8gko473hc7397mgrg)，未安装 GitHub 仓库集成。推送到 `main` 后仍需手动部署，不能据此认为线上已更新。服务记录、网页跨域配置与 Lovable 接入顺序见 [Render部署说明](Render部署说明.md)。

免费服务闲置后会休眠，首次唤醒需要等待。Render 提供 HTTPS，不需要在自己电脑安装证书。网页上线后，访问者也无需启动 Python。

## API 与文档

| 方法 | 路径 | 功能 |
| --- | --- | --- |
| GET | `/api/health` | 服务状态 |
| GET | `/api/topics` | 主题列表 |
| GET | `/api/cities` | 常用城市与时区 |
| POST | `/api/chart` | 验证出生信息并排盘 |
| POST | `/api/report` | 只查询指定主题解读 |
| POST | `/api/draw` | 只抽取一支指定主题签 |
| POST | `/api/people` | 只查询最多三位相似人物 |

语言使用 `zh` / `en`，主题使用 `wealth` / `study` / `romance`。接口独立返回 JSON，随机抽签不能自动重试。完整请求、响应和错误说明见 [API接口说明](API接口说明.md) 与 [openapi.json](openapi.json)。

- [Lovable公网接入补充说明](Lovable公网接入补充说明.md)：当前部署方案与前端需要修改的配置。
- [Lovable本地Web需求说明](Lovable本地Web需求说明.md)：五页业务、交互和接口约定，部署部分以公网补充说明为准。
- [MVP开发指南](MVP开发指南.md)：业务模块关系与学习记录。
- [手动测试清单](手动测试清单.md)：终端和 API 验收步骤。
- [人物资料清单](人物资料清单.md)：人物出生资料来源。

## 运行自动检查

```bash
./.venv-api/bin/python3 -m pip install -r requirements-dev.txt
./.venv-api/bin/python3 -B -m unittest discover -s tests -v
```

测试使用模拟百科响应，不需要连接外部百科服务。

部署配置依据：[Render FastAPI 部署文档](https://render.com/docs/deploy-fastapi)、[Blueprint 配置说明](https://render.com/docs/blueprint-spec)、[Python 版本配置](https://render.com/docs/python-version)。
