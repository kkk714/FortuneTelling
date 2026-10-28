# report.py 完整恢复代码

> 历史参考：本文件保存单层菜单调整前的恢复代码，包含旧的签文参数。当前报告已改为 `format_report(birth, chart, reading, language="zh")`，不自动附签文。不要再用下方旧代码覆盖当前文件；当前流程见 [MVP开发指南.md](MVP开发指南.md) 第 16、18 节。

当前错误：报告函数缺失，人物函数重复。下面提供完整的三个双语排版函数。

请打开项目里的 `report.py`，按 Command + A 全选，将整个文件替换为下面代码块内的全部内容。包含顶部导入和三个完整函数；不要复制代码块外围的反引号。保存后再执行末尾的导入检查。

本文件仅供你复制。助手没有修改项目 `report.py`。

```python
from i18n import t


def format_lot(lot, language="zh"):
    lot_label = lot.get(
        "topic_label",
        t("general_topic", language)
    )

    lot_lines = [
        t(
            "lot_heading",
            language,
            topic=lot_label,
            number=lot["id"],
            title=lot["title"]
        ),
        t("lot_text", language) + lot["text"]
    ]

    if "interpretation" in lot:
        lot_lines.append(
            t("lot_interpretation", language)
            + lot["interpretation"]
        )

    if "advice" in lot:
        lot_lines.append(
            t("lot_advice", language) + lot["advice"]
        )

    return "\n".join(lot_lines)


def format_report(birth, chart, reading, lot, language="zh"):
    pillars = chart["pillars"]
    counts = chart["element_counts"]
    separator = t("list_separator", language)

    dominant = separator.join(
        t(element, language)
        for element in reading["dominant_elements"]
    )
    missing = separator.join(
        t(element, language)
        for element in reading["missing_elements"]
    )

    if missing == "":
        missing = t("none", language)

    topic_label = reading.get(
        "topic_label",
        t("basic_reading", language)
    )
    details = reading["text"]

    if "items" in reading:
        sections = []

        for item in reading["items"]:
            lines = [
                item["title"],
                item["basis"],
                item["text"],
                t("reading_advice", language) + item["advice"]
            ]
            sections.append("\n".join(lines))

        details = "\n\n".join(sections)

    count_parts = []

    for element, count in counts.items():
        count_parts.append(
            t(
                "element_count_item",
                language,
                element=t(element, language),
                count=count
            )
        )

    count_text = " ".join(count_parts)
    topic_heading = t("topic_heading", language, topic=topic_label)
    lot_details = format_lot(lot, language)

    return f"""
========== {t("report_title", language)} ==========
{t("local_birth_time", language)}{birth.strftime("%Y-%m-%d %H:%M %z")}
{t("birth_timezone", language)}{birth.tzinfo}
{t("year_pillar", language)}{pillars["year"]}  {t("month_pillar", language)}{pillars["month"]}
{t("day_pillar", language)}{pillars["day"]}  {t("time_pillar", language)}{pillars["time"]}

{t("element_counts", language)}{count_text}
{t("dominant_elements", language)}{dominant}
{t("missing_elements", language)}{missing}

{topic_heading}
{details}

{lot_details}

{t("calculation_note", language)}
{t("report_notice", language)}
==============================
"""


def format_people(matches, language="zh"):
    if not matches:
        return (
            t("people_heading", language)
            + "\n"
            + t("people_none", language)
        )

    sections = [t("people_heading", language)]
    separator = t("list_separator", language)

    for item in matches:
        person = item["person"]
        biography = item["biography"]

        name = person["name"]

        if language == "en":
            name = person["wiki_titles"]["en"]

        dominant = separator.join(
            t(element, language)
            for element in person["dominant_elements"]
        )
        common = separator.join(
            t(element, language)
            for element in item["common_elements"]
        )

        if item["same_dominant"]:
            basis = t("match_exact", language)
        else:
            basis = t("match_partial", language)

        lines = [
            t("person_name", language) + name,
            t("person_dominant", language) + dominant,
            t("common_elements", language) + common,
            t("match_method", language) + basis,
            t("biography_label", language) + biography["summary"],
            t("wiki_source", language) + biography["url"],
            t("birth_source", language) + person["birth_source"]
        ]

        sections.append("\n".join(lines))

    sections.append(t("people_notice", language))

    return "\n\n".join(sections)
```

## 保存后检查

在项目目录运行：

```bash
./.venv/bin/python3 -c "from report import format_report, format_lot, format_people; print('三个排版函数导入成功')"
```

预期输出：

```text
三个排版函数导入成功
```

这份文件只定义三个排版函数，直接运行 `report.py` 不显示报告；完整流程通过 `main.py` 启动。
