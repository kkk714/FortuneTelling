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


def format_report(birth, chart, reading, language="zh"):
    """展示四柱、表层五行和所选主题解读。"""
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
