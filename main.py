"""先填写出生信息，再按单层菜单执行一项查询。"""

from user import birth_info, choose_action, choose_language
from calculator import bazi
from rules import data_loader, interpretation
from fortune import lots
from report import format_report, format_lot, format_people
from people import PEOPLE, prepare_people, recommend_people
from i18n import t


class MainApp:
    def run(self):
        language = choose_language()
        print(t("welcome", language))

        try:
            rule_data = data_loader(language)
        except (OSError, ValueError) as error:
            print(t("rules_load_failed", language), error)
            return

        print(t("birth_instruction", language))
        birth = birth_info(language)
        chart = bazi(birth)

        # 人物库只在首次查询人物时准备，简介按出生信息与语言缓存。
        people = None
        people_matches = {}

        while True:
            action, topic = choose_action(language)

            if action == "language":
                new_language = choose_language(language)

                try:
                    new_rule_data = data_loader(new_language)
                except (OSError, ValueError) as error:
                    print(t("rules_load_failed", language), error)
                    continue

                language = new_language
                rule_data = new_rule_data
                print(t("language_changed", language))
                continue

            if action == "birth":
                print(t("birth_instruction", language))
                new_birth = birth_info(language)
                new_chart = bazi(new_birth)

                birth, chart = new_birth, new_chart
                people_matches.clear()
                print(t("birth_updated", language))
                continue

            if action == "report":
                reading = interpretation(
                    chart,
                    rule_data,
                    topic=topic,
                    language=language
                )
                print(format_report(birth, chart, reading, language=language))
                continue

            if action == "draw":
                lot = lots(rule_data, topic=topic)
                print(format_lot(lot, language))
                print(t("entertainment_notice", language))
                continue

            if action == "people":
                if language not in people_matches:
                    print(t("people_fetching", language))

                    if people is None:
                        people = prepare_people(PEOPLE)

                    counts = chart["element_counts"]
                    max_count = max(counts.values())
                    dominant = [
                        element for element, count in counts.items()
                        if count == max_count
                    ]
                    people_matches[language] = recommend_people(
                        dominant, people, language=language
                    )

                print(format_people(people_matches[language], language))


if __name__ == "__main__":
    app = MainApp()
    app.run()
