# FortuneTelling · 八字与主题抽签

一个 Python 终端程序和 FastAPI 后端，支持中文与英文：

- 输入出生地时区、日期与时间，处理冬夏令时并计算四柱、表层五行计数。
- 按财运、学习运、桃花运查询主题解读，或单独抽取主题签文。
- 从 30 位有出生资料来源的人物中匹配五行最多项相似的人物，获取百科简介。

解读与人物匹配供传统文化娱乐和阅读参考。程序目前不连接数据库，不提供账号、登录或长期历史记录；人物简介需要联网，无法获取时仍保留人物与来源链接。

## 项目状态

本仓库包含后端、终端程序、规则数据与接入文档。Lovable 正在制作的网页不在本仓库中。

已加入 Render 部署配置。**上传到 GitHub 不等于已经上线**；还需要在 Render 创建后端服务，然后把真实 HTTPS API 地址配置给 Lovable 并发布网页。当前没有可供公众体验的网站链接。

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
| 自动部署分支 | `main` |

在 Render 连接本仓库，通过 **New → Blueprint** 读取配置；创建前确认实例为 **Free**。完整步骤、网页跨域配置与 Lovable 接入顺序见 [Render部署说明](Render部署说明.md)。

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
