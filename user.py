"""
终端输入：先填写出生信息，再通过单层菜单选择一个查询。
每个输入位置都支持输入 0 退出整个程序。
"""

from datetime import datetime, timezone
from birth_time import resolve_local_time
from i18n import t


def input_or_exit(prompt, language="zh"):
    """读取终端输入；0、Ctrl+C 或输入结束时正常退出。"""
    try:
        value = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        value = "0"

    if value == "0":
        print(t("goodbye", language))
        raise SystemExit(0)

    return value


def choose_language(language="zh"):
    choices = {
        "1": "zh",
        "2": "en"
    }

    print("\n请选择语言 / Choose a language:")
    print("1. 中文")
    print("2. English")
    print("0. 退出 / Exit")

    while True:
        choice = input_or_exit(
            "请输入编号 / Enter a number (1/2, 0 退出 / to exit): ",
            language
        )

        if choice in choices:
            return choices[choice]

        print(
            "输入无效，请输入1或2，输入0退出。 / "
            "Invalid input. Enter 1 or 2, or 0 to exit."
        )


def birth_info(language="zh"):
    zone_name = choose_timezone(language)

    while True:
        birthday = input_or_exit(t("birth_date_prompt", language), language)
        time = input_or_exit(t("birth_time_prompt", language), language)

        try:
            local_birth = datetime.strptime(
                birthday + " " + time,
                "%Y-%m-%d %H:%M"
            )
            candidates = resolve_local_time(local_birth, zone_name)
        except ValueError:
            print(t("invalid_birth", language))
            continue
        except OverflowError:
            print(t("birth_out_of_range", language))
            continue

        if len(candidates) == 0:
            print(t("time_nonexistent", language))
            continue

        if len(candidates) == 1:
            birth = candidates[0]
        else:
            print(t("time_ambiguous", language))

            for number, candidate in enumerate(candidates, start=1):
                print(
                    f"{number}. "
                    f"{candidate.strftime('%Y-%m-%d %H:%M %z')}"
                )

            while True:
                choice = input_or_exit(
                    t("time_occurrence_prompt", language), language
                )

                if choice in ("1", "2"):
                    birth = candidates[int(choice) - 1]
                    break

                print(t("invalid_occurrence", language))

        if birth.astimezone(timezone.utc) > datetime.now(timezone.utc):
            print(t("birth_in_future", language))
            continue

        return birth


def choose_topic(rules, language="zh"):
    """保留供单独练习使用；主程序已将主题合并到单层菜单。"""
    choices = {
        "1": "wealth",
        "2": "study",
        "3": "romance"
    }

    print("\n" + t("topic_title", language))

    for number, topic in choices.items():
        label = rules["topics"][topic]["label"]
        print(f"{number}. {label}")

    while True:
        choice = input_or_exit(t("topic_prompt", language), language)

        if choice in choices:
            return choices[choice]

        print(t("invalid_topic", language))


def choose_action(language="zh"):
    """返回 (功能, 主题)；没有主题的功能返回 None。"""
    choices = {
        "1": ("report", "wealth", "menu_wealth_report"),
        "2": ("report", "study", "menu_study_report"),
        "3": ("report", "romance", "menu_romance_report"),
        "4": ("draw", "wealth", "menu_wealth_draw"),
        "5": ("draw", "study", "menu_study_draw"),
        "6": ("draw", "romance", "menu_romance_draw"),
        "7": ("people", None, "menu_people"),
        "8": ("birth", None, "menu_birth"),
        "9": ("language", None, "menu_language")
    }

    print("\n==========", t("menu_title", language), "==========")

    for number, (_, _, label) in choices.items():
        print(f"{number}. {t(label, language)}")

    print("0. " + t("menu_exit", language))

    while True:
        choice = input_or_exit(t("action_prompt", language), language)

        if choice in choices:
            action, topic, _ = choices[choice]
            return action, topic

        print(t("invalid_action", language))


def choose_timezone(language="zh"):
    choices = {
        "1": {"label": t("city_shanghai", language), "zone": "Asia/Shanghai"},
        "2": {"label": t("city_sydney", language), "zone": "Australia/Sydney"},
        "3": {"label": t("city_london", language), "zone": "Europe/London"},
        "4": {"label": t("city_new_york", language), "zone": "America/New_York"},
        "5": {"label": t("city_tokyo", language), "zone": "Asia/Tokyo"}
    }

    print("\n" + t("city_title", language))

    for number, city in choices.items():
        print(f"{number}. {city['label']}")

    while True:
        choice = input_or_exit(t("city_prompt", language), language)

        if choice in choices:
            return choices[choice]["zone"]

        print(t("invalid_city", language))


if __name__ == "__main__":
    print(birth_info())
