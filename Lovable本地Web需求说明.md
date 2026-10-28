# Suanming 本地 Web：交给 Lovable 的需求与接口说明

> 目标更新（2026-10-29）：用户已明确最终目标为公众打开网址即可使用。部署路线改为 Render 运行 Python 后端、Lovable 发布现有前端，详见《Lovable公网接入补充说明.md》。本文件中“只在本机运行／公网部署以后再安排”的范围约定由补充说明覆盖；五页业务、API 契约与双语签文快照继续有效。

版本：1.0；整理日期：2026-10-29。

状态：五个功能页面及以下业务规则已经确认；视觉风格尚未确认；现有 Python HTTP API 已完成。

## 0. 给 Lovable 的工作指令

请先完整阅读本文，复述五页结构、关键状态流转和 API 接入计划，并列出需要用户决定的视觉风格选项。当前先完成需求理解，不要直接决定配色、字体、插画、动效或最终视觉主题。用户确认风格后，再按本文实现前端。

本文中的产品功能与业务约束是已确认的需求；“视觉风格待确认”不能被当作可以自行增加功能或改写流程。先前四页方案已由本文件的五页方案替代。

目标是为已经写好的 Python 后端制作一个可在用户自己电脑运行的 Web 前端。继续复用 Python 的排盘和文案，前端负责输入、导航、状态与展示。不要把后端重写成其他平台的函数，也不需要新建数据库、账号系统、付费接口或 AI 生成人物／解读服务。

本文包含所有必要的产品规则、接口字段与固定签文翻译快照，可以作为一份独立需求输入。另有 `openapi.json` 可作辅助附件，以核对现有接口的完整机器描述。

## 1. 产品范围

这是一个传统文化娱乐用途的八字表层五行体验工具：

- 用户先选择语言，填写出生城市、当地出生日期和时分。
- 出生信息校验成功后，进入单层功能菜单。
- 每次只查询一种内容：一个主题的解读、一支主题签，或相似人物。
- 支持完整中文和英文，主题为财运、学习运、桃花运。
- 解读只依据现有表层五行计数；沿用后端的四柱计算和现有原创文案。
- 每个主题三支签；人物库共 30 位，一次最多推荐三位。
- 人物内容为匹配依据、百科简介和来源，在同一页阅读；没有生平时间线。
- 只保留本次体验的数据，不制作账号、登录、数据库或长期历史记录页面。

首次体验的固定顺序：

```text
选择语言 → 填写出生信息 → 后端验证并排盘
→ 功能菜单 → 所选结果页 → 返回功能菜单或退出
```

即使只想抽签，也先完成出生信息。这是前端流程要求；抽签算法本身不使用生日。

## 2. 页面数量与路由

共五种功能页面。三个主题复用解读页与抽签页，不各自新增页面。修改出生信息复用第一页，语言选择、错误提示和重复钟点选择都不增加独立页面。

| 页面 | 建议路由 | 功能 |
| --- | --- | --- |
| 出生信息页 | `/` | 选择语言、填写或修改出生信息，提交验证 |
| 功能菜单页 | `/menu` | 七个查询入口，以及修改出生信息、切换语言、退出 |
| 主题解读页 | `/report?topic=wealth` | 只展示所选主题的排盘与解读 |
| 抽签结果页 | `/draw?topic=wealth` | 只展示所选主题的一支签，可再抽一次 |
| 相似人物页 | `/people` | 展示最多三位人物、匹配方式、可展开简介与来源 |

`topic` 只能是 `wealth`、`study`、`romance`。结果路由缺少主题或主题无效时返回功能菜单，不把它默认为用户选择了财运。出生信息不能放入 URL。

除出生信息页外，其他页面都需要已验证的出生信息。直接进入受保护页面但没有当前出生信息时，回到出生信息页；这只是业务前置条件，不需要登录系统。

## 3. 每页的内容与行为

### 3.1 出生信息页

内容：

- 简短产品介绍和传统文化娱乐说明。
- 中文／English 语言选择。
- 出生城市下拉选择，数据来自 `/api/cities`，目前五个城市。
- 公历出生日期和 24 小时制出生时间，时间精确到分钟。
- “开始查询”或编辑模式下的“保存出生信息”。
- “退出／结束本次体验”。

输入字段使用明确标签。日期、时间与城市均需填写；不知道生时不能自动用午夜代替。`00:00` 是合法的明确时间输入。

按出生地钟面原样提交日期、时间和 IANA 时区。不要用浏览器所在时区把用户输入预先转换成另一日期或时间，也不要自行换算固定 UTC+8；这些由后端完成。

提交行为：

1. 调用 `POST /api/chart`。
2. 加载期间防止重复提交。
3. `200` 成功后保存本次出生输入、解析后的出生信息和排盘，再进入 `/menu`。
4. 输入错误时在当前表单内提示，保留已填内容。
5. 收到 `time_ambiguous` 时，在表单内列出后端返回的两次钟点及偏移，让用户选择；使用对应的 `fold` 重新提交。
6. 修改城市、日期或时间后，清掉先前重复钟点的选择，避免把旧 `fold` 用于新的输入。

修改模式预填当前出生信息。使用独立草稿，新的校验与排盘成功后才替换已保存的信息，并清空旧解读、签文和人物结果。编辑过程中返回菜单可以保留原来的已验证信息；点击“退出”仍结束整次体验。

### 3.2 功能菜单页

展示当前出生信息的简短摘要，以及以下七个平级查询入口：

| 对应原终端编号 | 中文入口 | 英文入口 | 触发 |
| --- | --- | --- | --- |
| 1 | 财运解读 | Wealth Reading | `POST /api/report`，`topic=wealth` |
| 2 | 学习运解读 | Study Reading | `POST /api/report`，`topic=study` |
| 3 | 桃花运解读 | Romance Reading | `POST /api/report`，`topic=romance` |
| 4 | 财运抽签 | Wealth Fortune Draw | `POST /api/draw`，`topic=wealth` |
| 5 | 学习运抽签 | Study Fortune Draw | `POST /api/draw`，`topic=study` |
| 6 | 桃花运抽签 | Romance Fortune Draw | `POST /api/draw`，`topic=romance` |
| 7 | 相似人物 | Similar People | `POST /api/people` |

网页使用可点击入口，不要求输入数字。可以保留编号帮助理解，但不要在选择功能后再弹出一个主题选择层。

另有“修改出生信息”“切换语言”“退出”操作，它们不算新查询页面。

打开菜单时不自动请求解读、抽签或人物。用户选择哪个功能，就只执行对应操作。

### 3.3 主题解读页

展示：

- 本次主题名称。
- 出生地当地时间、出生时区。
- 年柱、月柱、日柱、时柱。
- 木、火、土、金、水五项计数。
- 全部并列最多项，以及表层计数未出现项；没有未出现项时显示“无／None”。
- `reading.items` 中各项标题、匹配依据、正文和行动提示。
- 后端的排盘口径说明与娱乐说明。

`reading.items` 已包含详细内容，按顺序展示一次，不要同时再把 `reading.text` 作为另一段重复展示。

当前选择一个主题时，只显示该主题，不附加签文或人物，也不要偷偷预取它们。最多项并列时可以显示多项解读，这是正常业务结果。

操作：返回功能菜单、修改出生信息、切换语言、退出。

显示出生当地时间时使用响应中的当地时间／指定出生时区，不能让 JavaScript 默认转换为当前电脑时区。

### 3.4 抽签结果页

展示当前主题、签号、签名、签诗、解签、行动提示和娱乐说明。不要附加八字报告或人物。

操作：再抽一次、返回功能菜单、切换语言、退出。

抽签规则：

- 从功能菜单主动选择某个抽签入口时，调用一次 `/api/draw` 并进入结果页。
- 点击“再抽一次”才再次调用；随机重复同一签属于正常结果。
- 加载时禁用重复点击。
- 页面渲染、组件重新挂载、返回／前进、刷新、语言切换，均不得自动产生新的一次抽签。
- 不要把抽签调用放进会重复执行的页面挂载副作用，也不要对它做自动重试。
- 返回菜单后再次主动点击抽签入口，属于用户发起的新抽签，可以更新结果。
- 直接打开抽签路由而没有当前结果时，显示主题及“开始抽签”按钮，由用户主动触发；不凭路由进入事件自动抽签。

一支签的身份是 `(topic, id)`，因为不同主题都会使用签号 1、2、3。切换语言必须保留相同主题和相同签号，处理办法见第 6 节。

### 3.5 相似人物页

展示最多三位人物，每位包括：

- 当前语言的姓名。
- 人物最多项、共同最多项。
- 匹配方式，区分“最多项集合相同”和“部分最多项相同”。
- 百科简介，同页展开／收起，不进入另一个详情页。
- 百科原文链接与出生资料来源链接。

保持后端返回的排序，使用 `person.id` 识别同一个人物。人物资料、简介和来源均以 API 为准；接口没有照片、完整传记或时间线，不自行补造这些内容。

页面内处理：加载中、没有匹配、简介获取失败、整次请求失败。来源链接应可以正常打开。

`200` 且 `biography.available=false` 是有效的降级结果：继续显示人物与匹配依据，使用后端给出的备用说明和原文链接，不把整个页面当作失败。

人物请求可能包含最多三次百科访问，每次设置 8 秒网络超时；前端不应把整次人物查询的总等待时间直接设成 8 秒。加载时有清楚提示，允许用户返回或退出。

操作：返回功能菜单、修改出生信息、切换语言、退出。

## 4. 公共状态与交互规则

### 4.1 当前体验的数据

区分出生输入与后端解析结果：

- `birthInput`：`date/time/timezone/fold`，用于后续请求。
- `resolvedBirth`：后端的带偏移当地时间、UTC 时间和排盘时间，用于展示。
- `chart`：四柱与五行。
- `language`：`zh/en`。
- 解读缓存：按出生输入、主题、语言区分。
- 人物缓存：按出生输入、语言区分。
- 当前签：保存主题、签号和已取得的各语言显示内容；这只是当前结果，不做历史记录列表。

前端可以用内存状态与 `sessionStorage` 保留本标签页的当前体验，支持刷新后恢复当前结果。语言偏好可以单独放 `localStorage`。不把出生信息或查询结果存入 `localStorage`，不把它们写入 URL。

### 4.2 返回菜单

保留出生信息、排盘和已取得的结果。返回动作不请求新签、不重新获取人物简介；再次选择已有主题解读或人物时可复用当前语言的缓存。

### 4.3 修改出生信息

新输入校验成功后替换当前出生信息，并清空所有语言下的旧解读、签文与人物结果。之后使用新的出生信息查询，不能显示前一个生日的旧结果。

### 4.4 切换语言

- 不改变出生信息、四柱、五行计数、当前主题或已抽中的签号。
- 界面标签、按钮、表单提示、加载及错误提示均切换。
- 在解读页：用相同出生信息、相同主题获取另一语言解读，或复用相应缓存。
- 在人物页：用相同出生信息获取另一语言简介，或复用相应缓存；同一人物由稳定 `person.id` 对应。
- 在抽签页：按第 6 节直接读取同一支签的另一语言文案，绝不再次随机抽签。
- 正文翻译尚在加载或获取失败时给出相应语言提示，不能把旧语言正文标记成已翻译完成。

五行原始键始终为中文，英文显示名使用 `element_labels`。四柱干支仍显示癸未、甲辰等原始符号，栏目名称翻译即可。IANA 时区标识不翻译。

### 4.5 退出

所有五个页面都能结束本次体验：

1. 取消或废弃本次未完成的业务请求。
2. 清除出生信息、排盘、所有查询缓存与当前签。
3. 清除本标签页保存的本次体验数据。
4. 保留语言偏好，回到空的出生信息页。

这是网页的“结束本次体验”，不请求不存在的 logout 接口，也不停止 Python API 服务。

### 4.6 异步结果与失败

切换语言、修改出生信息、退出或离开结果页后，旧请求不能覆盖新状态。使用取消请求或状态版本／请求标识来判断响应是否仍属于当前出生信息与语言。

API 不可连接时，在当前页显示“服务暂时无法连接，请重试”等易懂提示，不显示 Python 堆栈。调试地址和原始错误留在开发日志或 README，不作为面向用户的主体内容。

## 5. 已实现的 API 契约

### 5.1 地址与通用约定

本机开发地址：`http://127.0.0.1:8000`。

前端使用可配置的 API 基地址；如果使用 Vite，可用：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

基地址不包含 `/api`，调用路径包含 `/api/...`，避免拼成 `/api/api/...`。当前 API 不需要 API Key、登录 Cookie 或鉴权 Token。

请求使用 JSON，`Content-Type: application/json`。请求模型拒绝多余字段；不要把解析后的整份出生响应当作出生输入发送，也不要给抽签或人物接口附加它们不接受的字段。

语言：`zh | en`。主题：`wealth | study | romance`。

| 方法 | 路径 | 返回用途 |
| --- | --- | --- |
| GET | `/api/health` | 服务状态 |
| GET | `/api/topics?language=zh` | 三主题的 id、label、description |
| GET | `/api/cities?language=zh` | 五城市的 id、label、timezone |
| POST | `/api/chart` | 校验出生信息并排盘 |
| POST | `/api/report` | 排盘与所选主题解读 |
| POST | `/api/draw` | 随机一支主题签 |
| POST | `/api/people` | 最多三位人物及简介来源 |

这七个接口已存在；没有固定签文查询、用户、登录、历史记录或人物详情接口。不要虚构接口地址。

### 5.2 请求示例

`POST /api/chart`：

```json
{
  "language": "zh",
  "birth": {
    "date": "2003-04-01",
    "time": "14:15",
    "timezone": "Asia/Shanghai"
  }
}
```

`POST /api/report`：

```json
{
  "language": "en",
  "topic": "study",
  "birth": {
    "date": "2003-04-01",
    "time": "14:15",
    "timezone": "Asia/Shanghai"
  }
}
```

`POST /api/draw`：

```json
{
  "language": "zh",
  "topic": "wealth"
}
```

`POST /api/people`：

```json
{
  "language": "en",
  "limit": 3,
  "birth": {
    "date": "2003-04-01",
    "time": "14:15",
    "timezone": "Asia/Shanghai"
  }
}
```

`limit` 为整数 1～3，默认 3。主题默认为 `wealth`，语言默认为 `zh`；前端仍应明确传入用户所选值。

### 5.3 响应结构

下列 TypeScript 类型描述当前数据契约，可用于建立前端类型；准确的完整结构也可从 `/openapi.json` 或同名附件读取。

```typescript
type Language = 'zh' | 'en';
type Topic = 'wealth' | 'study' | 'romance';
type Element = '木' | '火' | '土' | '金' | '水';

interface BirthInput {
  date: string;
  time: string;
  timezone: string;
  fold?: 0 | 1;
}

interface ResolvedBirth {
  local_datetime: string;
  timezone: string;
  utc_datetime: string;
  calculation_datetime: string;
  fold: 0 | 1;
}

interface Chart {
  pillars: { year: string; month: string; day: string; time: string };
  element_counts: Record<Element, number>;
}

interface ChartResponse {
  language: Language;
  birth: ResolvedBirth;
  chart: Chart;
  element_labels: Record<Element, string>;
  calculation_note: string;
  notice: string;
}

interface ReadingItem {
  element: Element;
  title: string;
  basis: string;
  text: string;
  advice: string;
}

interface ReportResponse extends ChartResponse {
  reading: {
    topic: Topic;
    topic_label: string;
    dominant_elements: Element[];
    missing_elements: Element[];
    text: string;
    items: ReadingItem[];
  };
}

interface Lot {
  id: number;
  topic: Topic;
  topic_label: string;
  title: string;
  text: string;
  interpretation: string;
  advice: string;
}

interface DrawResponse {
  language: Language;
  lot: Lot;
  notice: string;
}

interface PersonMatch {
  person: {
    id: string;
    name: string;
    birth: string;
    timezone: string;
    birth_source: string;
    dominant_elements: Element[];
    element_counts: Record<Element, number>;
  };
  common_elements: Element[];
  same_dominant: boolean;
  match_label: string;
  biography: { summary: string; url: string; available: boolean };
}

interface PeopleResponse {
  language: Language;
  birth: ResolvedBirth;
  dominant_elements: Element[];
  element_labels: Record<Element, string>;
  people: PersonMatch[];
  notice: string;
}

interface APIErrorResponse {
  error: { code: string; message: string; details: unknown };
}
```

例如英文计数显示：用 `element_labels['木']` 显示 `Wood`，数字仍读取 `chart.element_counts['木']`。不要把原始对象键改成英文后再传回 API。

### 5.4 日期错误与重复钟点

参数和出生时间错误通常返回 `422`，本地资料暂时不可用返回 `503`。错误体是 `error` 对象，不是 FastAPI 默认示例中的 `detail`。

```json
{
  "error": {
    "code": "birth_in_future",
    "message": "出生时间不能晚于当前时间。",
    "details": null
  }
}
```

需处理的常见 `code`：`invalid_request`、`invalid_birth`、`invalid_timezone`、`time_nonexistent`、`time_ambiguous`、`invalid_fold`、`birth_in_future`、`birth_out_of_range`、`calculation_unavailable`、`rules_unavailable`、`people_unavailable`、`internal_error`。

`time_ambiguous` 的 `error.details.candidates` 是一个数组，每项包含 `fold/local_datetime/utc_datetime`。展示两种候选并提交其 `fold`：0 为第一次，1 为第二次；不能把终端的选项编号 1／2 原样发给 API。

例如悉尼 `2024-04-07 02:30`：第一次偏移为 `+11:00`，第二次为 `+10:00`。悉尼 `2024-10-06 02:30` 不存在。普通钟点省略 `fold`，不要总是发送 `fold: 1`。

## 6. 同一支签的中英文切换：本次确定的接入办法

当前后端只有随机 `POST /api/draw`，没有按签号获取固定签文的接口。本次文档不新增 Python 接口，而是提供第 10 节的真实双语签文快照，供前端做显示语言切换。

请将快照保存为前端项目的数据文件，例如 `src/data/lot-catalog.json`。数据来自现有 `rules.json` 与 `rules_en.json`；每个主题的 1～3 签均有中英文对应。

工作方式：

1. 用户主动抽签时，仍调用真实 `/api/draw`；随机结果以后端为准。
2. 保存响应中的 `(topic, id)` 和这次收到的完整签文。
3. 切换语言时，用相同的 `topic/id` 到快照的对应语言签池中取文案，并使用对应主题名称与娱乐提示。
4. 原来已经取得的语言内容可复用，不改变当前签的身份。
5. 只有用户主动再抽一次时，才重新调用 `/api/draw`。

快照仅用于显示已有随机结果的另一语言，不用于前端自行随机、不用于假装后端已连接，也不用 AI 重新编写或翻译当前签文。

如果后端规则日后更新，需从两份规则文件同步更新快照。若缺少当前 `(topic,id)` 的对应翻译，保留原签并明确说明翻译暂不可用，不重新抽签来掩盖缺失。

以后可以改为真实的固定签文查询接口，但那属于后端另一次改动；当前不能生成一个不存在的地址并当成已经可用。

## 7. 本地运行、预览和后续部署

当前已验证的联调方式是：前端与 Python API 都在用户自己的电脑运行。

后端启动：

```bash
cd /Users/liuliu/Desktop/suanming
./.venv-api/bin/python3 api.py
```

测试页为 `http://127.0.0.1:8000/docs`。API 服务需要保持运行；打开一个网址不会自动启动 Python。

前端交付时必须附自己的 README、安装命令、启动命令和 `.env.example`。建议使用 `localhost:5173` 作为本地前端地址；若选择其他端口，请与后端 CORS 配置一致。

当前后端默认允许以下网页来源：

```text
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
http://localhost:8080
http://127.0.0.1:8080
```

使用不同来源时，可在启动后端前显式配置，例如：

```bash
SUANMING_CORS_ORIGINS='http://localhost:5173,http://localhost:4173' ./.venv-api/bin/python3 api.py
```

环境变量会替换默认来源列表。

Lovable 云端构建或服务端进程中的 `127.0.0.1` 不指向用户这台 Mac。云端 HTTPS 预览访问本机 HTTP 还受浏览器与网络环境限制，不应当作已经验证成功的联调方式。默认交付可取回并本地运行的前端；云端无法调用 API 时如实说明连接尚不可用，不用演示数据冒充成功。

未来上线时，由用户另行安排可公开访问的 HTTPS 后端及前端来源配置。当前没有公网 API 域名，没有配置本地可信 HTTPS，也不要求 Lovable 在这一版自动发布后端或开通云数据库。

## 8. 验收标准

1. 首次访问先填写出生信息，验证成功后才进入功能菜单。
2. 五页结构成立；三个主题共用模板，人物简介在同页展开。
3. 选择主题后没有第二层主题菜单，每次只展示所选功能的结果。
4. 财运、学习运、桃花运解读均只请求报告接口，不触发抽签或人物请求。
5. 三种主题抽签均来自正确签池；仅用户主动操作产生新抽签。
6. 返回、刷新、前进／后退、组件重新渲染与切换语言均不重抽。
7. 抽签页切换中英文，主题与签号保持不变，文案来自本文真实快照。
8. 相似人物无需先查报告；最多三位，顺序、共同项、匹配方式和来源与后端一致。
9. 人物简介失败仍能展示人物与原文链接；没有匹配时有空状态。
10. 中英文覆盖表单、菜单、结果标签、按钮、加载、错误与娱乐说明；四柱和原始五行键按约定保留。
11. 出生城市、日期、时间修改成功后清除旧结果，旧网络响应不能把旧结果写回来。
12. 退出清空本次信息和结果，保留语言，返回空的出生信息页。
13. 无效日期、未来时间、冬夏令时空缺与重复钟点均可正确提示和重试。
14. 服务停止时显示连接失败提示，不生成替代的“真实”八字、签文或人物数据。
15. 桌面和手机宽度均可操作，长英文、长简介与来源链接不会破坏页面。
16. 前端可以按 README 在本机运行并调用真实 API，业务数据不依赖 Lovable 云端数据库。

人工对照样例：上海 `2003-04-01 14:15`，四柱癸未／乙卯／甲辰／辛未，五行木3、火0、土3、金1、水1，最多项木与土，未出现项火。相似人物应为猫王、本笃十六世、塞尔日·甘斯布；英文姓名分别为 Elvis Presley、Pope Benedict XVI、Serge Gainsbourg。报告内容与人物姓名以 API 当前语言实际响应为准。

补充时区样例：悉尼 `2024-04-07 02:30` 要求选择第一次或第二次；选第二次后偏移为 `+10:00`。`2024-10-06 02:30` 要求重新填写。

## 9. 视觉风格待确认

本节暂未填写，也没有默认选择。

用户之后会单独确认：整体视觉方向、配色、字体、图形与图标、页面布局偏好、动效强度、参考网站或截图。

Lovable 当前先给出对需求的理解与风格讨论选项，等用户确认再生成最终视觉。不要仅凭“算命／五行”自行决定玄幻、古风、宇宙星空、卡通等风格。

风格确认后只补充本节，不改变前面的五页结构与业务规则；若视觉设计确实需要改变业务，应先明确提出并等待用户确认。

## 10. 双语固定签文快照

下方 JSON 从当前项目规则文件逐项导出，不是示例签文。请完整保留主题键、数字签号和正文。`topic_labels` 用于主题显示，`notices` 用于相应语言的娱乐提示，`lots` 用于按语言、主题和签号查找已有签的显示内容。

```json
{
  "snapshot_date": "2026-10-29",
  "source_files": {
    "zh": "rules.json",
    "en": "rules_en.json"
  },
  "topic_labels": {
    "zh": {
      "wealth": "财运",
      "study": "学习运",
      "romance": "桃花运"
    },
    "en": {
      "wealth": "Wealth",
      "study": "Study",
      "romance": "Romance"
    }
  },
  "notices": {
    "zh": "传统文化娱乐参考。",
    "en": "For cultural interest and entertainment."
  },
  "lots": {
    "zh": {
      "wealth": [
        {
          "id": 1,
          "title": "细水长流",
          "text": "细水绕青石，缓步识来路。",
          "interpretation": "这支签的主题是日常积累。先看清反复发生的收支，再安排自己的步调。照顾好能够持续的小习惯，让近期计划与生活节奏相互配合，留意那些容易被忽略的细小调整。",
          "advice": "整理一次固定支出清单，标出必需、可调整和已不再需要的项目。"
        },
        {
          "id": 2,
          "title": "灯下看清",
          "text": "灯下辨来路，心定再移步。",
          "interpretation": "这支签把注意力放在决定前的核对。面对折扣、邀约或新鲜想法，给自己一点时间，弄清实际用途、投入与相关条件。清楚的理由能帮助安排下一步，也让选择贴近眼前真正重视的事。",
          "advice": "遇到一项计划外消费时，先写下实际用途，再决定是否购买。"
        },
        {
          "id": 3,
          "title": "旧物生光",
          "text": "拂尘见旧物，留白纳新风。",
          "interpretation": "这支签邀请你重新看看手边已有的物品、时间和技能。先盘点能够继续使用的资源，再考虑添置物品或接下新安排。让计划贴近眼下的条件，也为新的想法留出适当空间。",
          "advice": "整理一个常用的角落，找出一件能够继续使用或修好的物品。"
        }
      ],
      "study": [
        {
          "id": 1,
          "title": "一步一页",
          "text": "一页添新字，一步过小桥。",
          "interpretation": "这支签的主题是从小处开始。面对一整章内容，先选一个概念或一道题，给自己留下实际动手的机会。把练习中遇到的困难记具体，下一次就有了清楚的起点。",
          "advice": "选一道难度适中的题，专心做十五分钟，并记下卡住的具体步骤。"
        },
        {
          "id": 2,
          "title": "旧页新知",
          "text": "灯下翻旧页，重读见新知。",
          "interpretation": "这支签把注意力放在回看与修正。暂时忘记的知识、曾经做错的题，都可以成为复习线索。分清概念模糊、条件遗漏和步骤失误，再安排一次有针对性的练习。",
          "advice": "挑一道旧错题，遮住答案重做，再对照解析写下一条纠错笔记。"
        },
        {
          "id": 3,
          "title": "清声问答",
          "text": "清声穿书页，一问接新枝。",
          "interpretation": "这支签的主题是表达与提问。把知识讲出来，能让理解清楚和仍然含糊的地方逐渐显现。遇到说不清的部分，回到资料中核对，也可以请别人指出没有听懂的地方。",
          "advice": "选一个刚学过的概念，录一段一分钟讲解，再回听并记下一处需要核对的地方。"
        }
      ],
      "romance": [
        {
          "id": 1,
          "title": "春风小径",
          "text": "花边留小径，问候似清风。",
          "interpretation": "这支签的主题是轻松相识。从共同话题开始，观察彼此是否愿意继续交流。把注意力放在当下的回应与相处感受上，让关系按照双方都舒适的节奏发展。",
          "advice": "在双方愿意交流时，分享一个共同话题，并给对方自然结束聊天的空间。"
        },
        {
          "id": 2,
          "title": "静听心声",
          "text": "清泉映疏影，静处听真声。",
          "interpretation": "这支签把注意力放在倾听与确认。分清对方说过的话和自己的推想，表达真实感受，也给对方澄清的机会。通过具体的交流，慢慢了解彼此重视的事。",
          "advice": "下次交流时，先用一句话复述对方的意思，确认理解后再表达自己的感受。"
        },
        {
          "id": 3,
          "title": "留隙生风",
          "text": "并枝留寸隙，各叶纳清风。",
          "interpretation": "这支签的主题是亲近中的空间。照顾自己的生活节奏，也尊重对方的安排。把需要沟通的事平和地说清楚，让相处与独处都能找到合适的位置。",
          "advice": "今天给自己安排一段独处时间，把注意力放回一件喜欢做的小事。"
        }
      ]
    },
    "en": {
      "wealth": [
        {
          "id": 1,
          "title": "A Steady Stream",
          "text": "A slender stream winds round blue-grey stone;\nSlow steps reveal the path that brought you here.",
          "interpretation": "This lot focuses on everyday accumulation. First understand your recurring income and expenses, then set your own pace. Nurture small habits you can sustain, let your near-term plans work with the rhythm of your life, and notice small adjustments that are easy to overlook.",
          "advice": "Make a list of your recurring expenses and mark those that are essential, those you could adjust, and those you no longer need."
        },
        {
          "id": 2,
          "title": "Clarity by Lamplight",
          "text": "By lamplight, trace the path;\nLet the heart settle before you step.",
          "interpretation": "This lot draws attention to checking the details before deciding. When considering a discount, an invitation, or a fresh idea, give yourself a little time to understand its practical use, the resources it requires, and any conditions involved. Clear reasons can help you plan the next step and keep your choices close to what truly matters to you now.",
          "advice": "When considering an unplanned expense, write down its practical use before deciding whether to buy."
        },
        {
          "id": 3,
          "title": "Old Things Shine Again",
          "text": "Brush away the dust, and old things reappear;\nLeave an open space to welcome a fresh breeze.",
          "interpretation": "This lot invites you to take another look at the possessions, time, and skills you already have. Take stock of resources you can continue using before buying more or taking on new commitments. Keep your plans grounded in your present circumstances while leaving suitable room for new ideas.",
          "advice": "Tidy a corner you use often and find one item you can keep using or repair."
        }
      ],
      "study": [
        {
          "id": 1,
          "title": "One Step, One Page",
          "text": "New words upon a page, small steps across a bridge.",
          "interpretation": "This lot is about starting small. When a whole chapter feels like a lot to take on, choose one concept or one question and give yourself a chance to work through it. Record the specific difficulty you encounter during practice so you have a clear starting point next time.",
          "advice": "Choose a question of moderate difficulty, work on it for fifteen focused minutes, and note the exact step where you get stuck."
        },
        {
          "id": 2,
          "title": "Old Pages, New Insights",
          "text": "By lamplight, old pages turn; rereading brings new insights.",
          "interpretation": "This lot draws your attention to review and correction. Knowledge you have temporarily forgotten and questions you once answered incorrectly can both guide your revision. Distinguish an unclear concept from an overlooked condition or a mistaken step, then plan a practice exercise that addresses it.",
          "advice": "Choose a past question you answered incorrectly, cover the answer and solve it again, then compare your work with the explanation and write one correction note."
        },
        {
          "id": 3,
          "title": "A Clear Voice, a Question",
          "text": "One clear voice among the pages, one question sprouting a new branch.",
          "interpretation": "This lot is about explaining and asking questions. Putting knowledge into words can reveal both what you understand clearly and what remains uncertain. When you cannot explain a part, return to your materials to check it. You can also ask someone to point out anything in your explanation they did not understand.",
          "advice": "Choose a concept you have just learned, record a one-minute explanation, then listen back and note one point you need to check."
        }
      ],
      "romance": [
        {
          "id": 1,
          "title": "A Path in the Spring Breeze",
          "text": "Leave a narrow path beside the flowers; let a greeting pass like a gentle breeze.",
          "interpretation": "This lot is about getting to know someone with ease. Start with a shared topic and notice whether you both want to keep talking. Focus on the responses and feelings you experience together in the moment, letting the relationship develop at a pace that feels comfortable for both of you.",
          "advice": "When you both feel like talking, share a topic you have in common and give the other person room to end the conversation naturally."
        },
        {
          "id": 2,
          "title": "Listen Quietly to the Heart",
          "text": "Clear spring water mirrors scattered shadows; in stillness, hear a true voice.",
          "interpretation": "This lot focuses on listening and checking your understanding. Distinguish what the other person has said from your own assumptions. Express your true feelings and give them a chance to clarify. Through specific conversations, gradually learn what matters to each of you.",
          "advice": "In your next conversation, first sum up the other person's meaning in one sentence. Check that you have understood before sharing your own feelings."
        },
        {
          "id": 3,
          "title": "Room for the Breeze",
          "text": "Between branches side by side, leave a little space; let every leaf welcome the breeze.",
          "interpretation": "This lot is about making room within closeness. Take care of your own daily rhythm and respect the other person's plans. Calmly explain anything that needs to be discussed, making room for both time together and time alone.",
          "advice": "Set aside some time alone today and turn your attention to one small thing you enjoy doing."
        }
      ]
    }
  }
}
```

## 11. 交给 Lovable 时可附的开场消息

> 请把附件《Lovable本地Web需求说明.md》作为本项目的产品需求和 API 交接说明。五页功能及业务规则已确认，Python 后端继续复用现有 API。本轮先复述你的理解与接入计划，随后和我确认视觉风格；暂不直接生成最终网页。特别注意本机 API 的联调边界、抽签切语言保留同一签，以及本文第 10 节的真实双语签文快照。不要重新设计已确认的功能范围。

可同时提供 `openapi.json` 作为辅助接口描述；不必上传 `.venv` 或 `.venv-api`。本文已经包含签文切换需要的数据，其他真实解读与人物内容从 API 获取。

参考资料（查阅日期 2026-10-29）：[Lovable 外部 API 接入](https://docs.lovable.dev/integrations/any-api)、[Lovable 项目 Instructions](https://docs.lovable.dev/features/knowledge)。本文不要求自动创建或发布 Lovable 项目，上传与后续生成由用户发起。
