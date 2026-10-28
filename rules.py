import json
from pathlib import Path
from i18n import t


def data_loader(language="zh"):
    filenames = {
        "zh": "rules.json",
        "en": "rules_en.json"
    }

    rules_path = Path(__file__).resolve().parent / filenames[language]

    with open(rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    return rules


def interpretation(chart, rules, topic=None, language="zh"):
    label = t("basic_reading", language)

    if topic is not None:
        if topic not in rules["topics"]:
            raise ValueError(
                t("unknown_topic", language, topic=topic)
            )

        if topic not in rules["topic_readings"]:
            raise ValueError(t("reading_unavailable", language))

        label = rules["topics"][topic]["label"]

    counts = chart["element_counts"]
    max_count = max(counts.values())

    dominant = []
    missing = []
    readings = []
    items = []

    for i, j in counts.items():
        if j == max_count:
            dominant.append(i)

            if topic is None:
                readings.append(rules["element_readings"][i])
            else:
                content = rules["topic_readings"][topic][i]
                readings.append(content["text"])

                items.append({
                    "element": i,
                    "title": content["title"],
                    "basis": t(
                        "element_basis",
                        language,
                        element=t(i, language),
                        count=j
                    ),
                    "text": content["text"],
                    "advice": content["advice"]
                })

        if j == 0:
            missing.append(i)

    result = {
        "dominant_elements": dominant,
        "missing_elements": missing,
        "text": "\n".join(readings)
    }

    if topic is not None:
        result["topic"] = topic
        result["topic_label"] = label
        result["items"] = items

    return result


if __name__ == "__main__":
    rules = data_loader()

    chart = {
        "element_counts": {
            "木": 3,
            "火": 0,
            "土": 3,
            "金": 1,
            "水": 1
        }
    }

    reading = interpretation(chart, rules, topic="wealth")

    print("数量最多：", reading["dominant_elements"])
    print("表层计数未出现：", reading["missing_elements"])
    print("主题：", reading["topic_label"])

    for item in reading["items"]:
        print(item["title"])
        print(item["basis"])
        print(item["text"])
        print("行动提示：", item["advice"])
        print()
