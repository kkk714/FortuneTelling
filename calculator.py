from datetime import datetime, timedelta, timezone
from lunar_python import Solar


def bazi(birth):
    if birth.tzinfo is None or birth.utcoffset() is None:
        raise ValueError("出生时间必须包含时区信息")

    calc_birth = birth.astimezone(timezone(timedelta(hours=8)))

    solar = Solar.fromYmdHms(
        calc_birth.year,
        calc_birth.month,
        calc_birth.day,
        calc_birth.hour,
        calc_birth.minute,
        calc_birth.second
    )

    eight_char = solar.getLunar().getEightChar()
    eight_char.setSect(2)

    # 日柱转化成五行
    wuxing = (
        eight_char.getYearWuXing()
        + eight_char.getMonthWuXing()
        + eight_char.getDayWuXing()
        + eight_char.getTimeWuXing()
    )

    element_counts = {
        "木": 0,
        "火": 0,
        "土": 0,
        "金": 0,
        "水": 0
    }

    for i in wuxing:
        element_counts[i] += 1

    return {
        "pillars": {
            "year": eight_char.getYear(),
            "month": eight_char.getMonth(),
            "day": eight_char.getDay(),
            "time": eight_char.getTime()
        },
        "element_counts": element_counts
    }


if __name__ == "__main__":
    birth = datetime(
        2003, 4, 1, 14, 15,
        tzinfo=timezone(timedelta(hours=8))
    )
    print(bazi(birth))
