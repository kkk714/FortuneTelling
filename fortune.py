import random


def lots(rules, topic=None):
    if topic is None:
        pool = rules["lots"]
    else:
        if topic not in rules["topics"]:
            raise ValueError(f"未知主题：{topic}")

        if topic not in rules["topic_lots"]:
            raise ValueError("这个主题的签文尚未准备好")

        pool = rules["topic_lots"][topic]

    if len(pool) == 0:
        raise ValueError("签池不能为空")

    lot = random.choice(pool).copy()

    if topic is not None:
        lot["topic"] = topic
        lot["topic_label"] = rules["topics"][topic]["label"]

    return lot


if __name__ == "__main__":
    from rules import data_loader

    rules = data_loader()
    lot = lots(rules, topic="wealth")

    print("主题：", lot["topic_label"])
    print(f"第{lot['id']}签：{lot['title']}")
    print("签诗：", lot["text"])
    print("解签：", lot["interpretation"])
    print("行动提示：", lot["advice"])
