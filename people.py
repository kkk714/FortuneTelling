from datetime import datetime
from zoneinfo import ZoneInfo
from calculator import bazi
import json
from urllib.parse import quote
from urllib.request import Request, urlopen
from i18n import t
"""
人物出生资料
    ↓
转换成带出生地时区的 datetime
    ↓
调用 calculator.py 的 bazi()
    ↓
得到五行计数
    ↓
找出全部并列最多项
"""

PEOPLE = [
    {
        "name": "伊丽莎白二世",
        "birth": "1926-04-21 02:40",
        "timezone": "Europe/London",
        "birthplace": "英国伦敦",
        "birth_source": "https://www.royal.uk/the-queens-early-life-and-education?page=7",
        "wiki_titles": {
                "zh": "伊丽莎白二世",
                "en": "Elizabeth II"
        }
    },
    {
        "name": "猫王（埃尔维斯·普雷斯利）",
        "birth": "1935-01-08 04:35",
        "timezone": "America/Chicago",
        "birthplace": "美国密西西比州图珀洛",
        "birth_source": "https://elvispresleymuseum.com/birth-of-elvis",
        "wiki_titles": {
                "zh": "艾維斯·皮禮士利",
                "en": "Elvis Presley"
        }
    },
    {
        "name": "安妮·弗兰克",
        "birth": "1929-06-12 07:30",
        "timezone": "Europe/Berlin",
        "birthplace": "德国美因河畔法兰克福",
        "birth_source": "https://www.annefrank.org/en/about-us/news-and-press/news/2021/6/10/92nd-anniversary-anne-franks-birth/",
        "wiki_titles": {
                "zh": "安妮·弗蘭克",
                "en": "Anne Frank"
        }
    },
    {
        "name": "萨尔瓦多·达利",
        "birth": "1904-05-11 08:45",
        "timezone": "Europe/Madrid",
        "birthplace": "西班牙菲格雷斯",
        "birth_source": "https://collections.glasgowmuseums.com/mwebcgi/mweb?request=record%3Bid%3D2340%3Btype%3D701",
        "wiki_titles": {
                "zh": "萨尔瓦多·达利",
                "en": "Salvador Dalí"
        }
    },
    {
        "name": "吉米·亨德里克斯",
        "birth": "1942-11-27 10:15",
        "timezone": "America/Los_Angeles",
        "birthplace": "美国华盛顿州西雅图，King County Hospital",
        "birth_source": "https://www.jimihendrix.com/biography/",
        "wiki_titles": {
                "zh": "吉米·亨德里克斯",
                "en": "Jimi Hendrix"
        }
    },
    {
        "name": "兰尼埃三世",
        "birth": "1923-05-31 06:00",
        "timezone": "Europe/Monaco",
        "birthplace": "摩纳哥王宫",
        "birth_source": "https://journaldemonaco.gouv.mc/var/jdm/storage/original/application/c5030e55778d903a40d2726cdcebba25.pdf",
        "wiki_titles": {
                "zh": "兰尼埃三世",
                "en": "Rainier III of Monaco"
        }
    },
    {
        "name": "小约翰·肯尼迪",
        "birth": "1960-11-25 00:22",
        "timezone": "America/New_York",
        "birthplace": "美国华盛顿特区，Georgetown University Hospital",
        "birth_source": "https://oregonnews.uoregon.edu/lccn/sn97071090/1960-11-25/ed-1/seq-1/ocr/",
        "wiki_titles": {
                "zh": "小约翰·肯尼迪",
                "en": "John F. Kennedy Jr."
        }
    },
    {
        "name": "玛格丽特公主",
        "birth": "1930-08-21 21:22",
        "timezone": "Europe/London",
        "birthplace": "英国苏格兰格拉米斯城堡",
        "birth_source": "https://www.thegazette.co.uk/London/issue/33636/page/5225/data.pdf",
        "wiki_titles": {
                "zh": "瑪嘉烈公主 (斯諾登伯爵夫人)",
                "en": "Princess Margaret, Countess of Snowdon"
        }
    },
    {
        "name": "戴安娜王妃",
        "birth": "1961-07-01 19:45",
        "timezone": "Europe/London",
        "birthplace": "英国诺福克郡桑德灵厄姆，Park House",
        "birth_source": "https://www.everand.com/book/769154367/Diana-Finally-the-Complete-Story",
        "wiki_titles": {
                "zh": "威爾斯王妃戴安娜",
                "en": "Diana, Princess of Wales"
        }
    },
    {
        "name": "普密蓬·阿杜德",
        "birth": "1927-12-05 08:45",
        "timezone": "America/New_York",
        "birthplace": "美国马萨诸塞州剑桥，Mount Auburn Hospital",
        "birth_source": "https://www.onep.go.th/ebook/ne/ne_2550_special.pdf",
        "wiki_titles": {
                "zh": "普密蓬·阿杜德",
                "en": "Bhumibol Adulyadej"
        }
    },
    {
        "name": "本笃十六世",
        "birth": "1927-04-16 04:15",
        "timezone": "Europe/Berlin",
        "birthplace": "德国巴伐利亚州因河畔马克特尔",
        "birth_source": "https://www.vaticannews.va/de/kirche/news/2025-04/marktl-morgenlob-feier-zum-geburtstag-von-papst-benedikt-xvi.html",
        "wiki_titles": {
                "zh": "本篤十六世",
                "en": "Pope Benedict XVI"
        }
    },
    {
        "name": "李小龙",
        "birth": "1940-11-27 07:12",
        "timezone": "America/Los_Angeles",
        "birthplace": "美国旧金山中华医院",
        "birth_source": "https://chineseexclusionfiles.com/2017/11/27/bruce-lee-anniversary-of-his-birth-27-november-1940/",
        "wiki_titles": {
                "zh": "李小龙",
                "en": "Bruce Lee"
        }
    },
    {
        "name": "玛丽莲·梦露",
        "birth": "1926-06-01 09:30",
        "timezone": "America/Los_Angeles",
        "birthplace": "美国洛杉矶，Los Angeles General Hospital",
        "birth_source": "https://api.pageplace.de/preview/DT0400.9780197636121_A46646150/preview-9780197636121_A46646150.pdf",
        "wiki_titles": {
                "zh": "玛丽莲·梦露",
                "en": "Marilyn Monroe"
        }
    },
    {
        "name": "艾迪特·皮雅芙",
        "birth": "1915-12-19 05:00",
        "timezone": "Europe/Paris",
        "birthplace": "法国巴黎特农医院",
        "birth_source": "https://www.city-editions.com/extrait/extraits-2014/Piaf-vie-vraie-extrait.pdf",
        "wiki_titles": {
                "zh": "艾迪特·皮雅芙",
                "en": "Édith Piaf"
        }
    },
    {
        "name": "塞尔日·甘斯布",
        "birth": "1928-04-02 04:55",
        "timezone": "Europe/Paris",
        "birthplace": "法国巴黎主宫医院",
        "birth_source": "https://static.fnac-static.com/multimedia/editorial/pdf/9782366025453.pdf",
        "wiki_titles": {
                "zh": "塞尔日·甘斯布",
                "en": "Serge Gainsbourg"
        }
    },
    {
        "name": "弗里达·卡罗",
        "birth": "1907-07-06 08:30",
        "timezone": "America/Mexico_City",
        "birthplace": "墨西哥墨西哥城科约阿坎",
        "birth_source": "https://www.penguinlibros.com/co/tematicas/28778-ebook-frida-9788430623198/fragmento",
        "wiki_titles": {
                "zh": "芙烈達·卡蘿",
                "en": "Frida Kahlo"
        }
    },
    {
        "name": "让-保罗·萨特",
        "birth": "1905-06-21 18:45",
        "timezone": "Europe/Paris",
        "birthplace": "法国巴黎第十六区，13 rue Mignard",
        "birth_source": "https://www.shpf.fr/wp-content/uploads/2012/11/CGP-120.pdf",
        "wiki_titles": {
                "zh": "让-保罗·萨特",
                "en": "Jean-Paul Sartre"
        }
    },
    {
        "name": "穆罕默德·阿里",
        "birth": "1942-01-17 18:35",
        "timezone": "America/Kentucky/Louisville",
        "birthplace": "美国肯塔基州路易维尔，Louisville General Hospital",
        "birth_source": "https://www.simonandschuster.com/books/Muhammad-Ali/Thomas-Hauser/9780671779719",
        "wiki_titles": {
                "zh": "穆罕默德·阿里",
                "en": "Muhammad Ali"
        }
    },
    {
        "name": "亚瑟·阿什",
        "birth": "1943-07-10 12:55",
        "timezone": "America/New_York",
        "birthplace": "美国弗吉尼亚州里士满，St. Philip’s Hospital",
        "birth_source": "https://www.newyorker.com/magazine/1969/06/07/arthur-ashe-profile-levels-of-the-game-i",
        "wiki_titles": {
                "zh": "亚瑟·阿什",
                "en": "Arthur Ashe"
        }
    },
    {
        "name": "迭戈·马拉多纳",
        "birth": "1960-10-30 07:05",
        "timezone": "America/Argentina/Buenos_Aires",
        "birthplace": "阿根廷拉努斯埃维塔医院",
        "birth_source": "https://www.lanus.gob.ar/diego-armando-maradona",
        "wiki_titles": {
                "zh": "迭戈·马拉多纳",
                "en": "Diego Maradona"
        }
    },
    {
        "name": "欧内斯特·海明威",
        "birth": "1899-07-21 08:00",
        "timezone": "America/Chicago",
        "birthplace": "美国伊利诺伊州橡树公园",
        "birth_source": "https://www.jfklibrary.org/sites/default/files/2018-07/EHScrapbook1.pdf",
        "wiki_titles": {
                "zh": "欧内斯特·海明威",
                "en": "Ernest Hemingway"
        }
    },
    {
        "name": "西蒙娜·德·波伏娃",
        "birth": "1908-01-09 04:00",
        "timezone": "Europe/Paris",
        "birthplace": "法国巴黎",
        "birth_source": "https://www.mondadorieducation.it/content/uploads/2022/04/9.itineraire_enfance.pdf",
        "wiki_titles": {
                "zh": "西蒙·德·波娃",
                "en": "Simone de Beauvoir"
        }
    },
    {
        "name": "詹姆斯·乔伊斯",
        "birth": "1882-02-02 06:00",
        "timezone": "Europe/Dublin",
        "birthplace": "爱尔兰都柏林拉斯加，41 Brighton Square West",
        "birth_source": "https://us.macmillan.com/books/9780374533823/jamesjoyce/",
        "wiki_titles": {
                "zh": "詹姆斯·乔伊斯",
                "en": "James Joyce"
        }
    },
    {
        "name": "玛丽长公主",
        "birth": "1897-04-25 15:30",
        "timezone": "Europe/London",
        "birthplace": "英国诺福克郡桑德灵厄姆，York Cottage",
        "birth_source": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5254107/",
        "wiki_titles": {
                "zh": "玛丽长公主 (哈伍德伯爵夫人)",
                "en": "Mary, Princess Royal and Countess of Harewood"
        }
    },
    {
        "name": "奥拉夫五世",
        "birth": "1903-07-02 17:50",
        "timezone": "Europe/London",
        "birthplace": "英国诺福克郡桑德灵厄姆，Appleton House",
        "birth_source": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5203360/",
        "wiki_titles": {
                "zh": "奥拉夫五世",
                "en": "Olav V"
        }
    },
    {
        "name": "乔治六世",
        "birth": "1895-12-14 03:00",
        "timezone": "Europe/London",
        "birthplace": "英国诺福克郡桑德灵厄姆，York Cottage",
        "birth_source": "https://www.thegazette.co.uk/London/issue/26689",
        "wiki_titles": {
                "zh": "乔治六世",
                "en": "George VI"
        }
    },
    {
        "name": "肯特公爵乔治王子",
        "birth": "1902-12-20 19:35",
        "timezone": "Europe/London",
        "birthplace": "英国诺福克郡桑德灵厄姆，York Cottage",
        "birth_source": "https://www.thegazette.co.uk/London/issue/27507",
        "wiki_titles": {
                "zh": "肯特公爵喬治王子",
                "en": "Prince George, Duke of Kent"
        }
    },
    {
        "name": "英国的约翰王子",
        "birth": "1905-07-12 03:05",
        "timezone": "Europe/London",
        "birthplace": "英国诺福克郡桑德灵厄姆，York Cottage",
        "birth_source": "https://www.thegazette.co.uk/London/issue/27816",
        "wiki_titles": {
                "zh": "英国的约翰王子",
                "en": "Prince John of the United Kingdom"
        }
    },
    {
        "name": "温斯顿·丘吉尔",
        "birth": "1874-11-30 01:30",
        "timezone": "Europe/London",
        "birthplace": "英国牛津郡伍德斯托克布伦海姆宫",
        "birth_source": "https://winstonchurchill.org/churchill-central/image/extract-from-churchill-the-life-pages-12-13/",
        "wiki_titles": {
                "zh": "温斯顿·丘吉尔",
                "en": "Winston Churchill"
        }
    },
    {
        "name": "艾尔顿·塞纳",
        "birth": "1960-03-21 02:35",
        "timezone": "America/Sao_Paulo",
        "birthplace": "巴西圣保罗，Pro-Matre 产科医院",
        "birth_source": "https://www1.folha.uol.com.br/esporte/2014/04/1447374-de-garoto-trapalhao-a-empresario-de-beco-a-silvastone-conheca-mais-sobre-senna.shtml",
        "wiki_titles": {
                "zh": "艾爾頓·冼拿",
                "en": "Ayrton Senna"
        }
    }
]


def prepare_people(people):
    prepared = []

    for person in people:
        birth = datetime.strptime(
            person["birth"],
            "%Y-%m-%d %H:%M"
        )
        birth = birth.replace(
            tzinfo=ZoneInfo(person["timezone"])
        )

        chart = bazi(birth)
        counts = chart["element_counts"]
        max_count = max(counts.values())

        dominant = []

        for element, count in counts.items():
            if count == max_count:
                dominant.append(element)

        item = person.copy()
        item["element_counts"] = counts
        item["dominant_elements"] = dominant

        prepared.append(item)

    return prepared


def match_people(dominant_elements, people, limit=3):
    user_top = set(dominant_elements)
    matches = []

    for person in people:
        person_top = set(person["dominant_elements"])
        common = []

        for element in dominant_elements:
            if element in person_top:
                common.append(element)

        if len(common) == 0:
            continue

        matches.append({
            "person": person,
            "common_elements": common,
            "same_dominant": user_top == person_top
        })

    matches.sort(key=lambda item: (
        not item["same_dominant"],
        -len(item["common_elements"])
    ))

    return matches[:limit]


def fetch_biography(person, language="zh"):
    title = person["wiki_titles"][language]
    encoded_title = quote(title, safe="")

    api_url = (
        f"https://{language}.wikipedia.org/"
        f"api/rest_v1/page/summary/{encoded_title}"
    )
    page_url = (
        f"https://{language}.wikipedia.org/wiki/{encoded_title}"
    )

    result = {
        "summary": t("bio_unavailable", language),
        "url": page_url,
        "available": False,
        "error": ""
    }

    request = Request(
        api_url,
        headers={
            "User-Agent": (
                "SuanmingLearning/0.1 "
                "(local terminal; biography lookup)"
            ),
            "Accept": "application/json"
        }
    )

    try:
        with urlopen(request, timeout=8) as response:
            data = json.load(response)

        summary = data.get("extract", "")

        if not summary:
            raise ValueError(t("bio_empty", language))

        result["summary"] = summary
        result["url"] = (
            data.get("content_urls", {})
            .get("desktop", {})
            .get("page", page_url)
        )
        result["available"] = True

    except (OSError, ValueError) as error:
        result["error"] = str(error)

    return result


"""
用户的五行最多项
    ↓
match_people()：选出最多三位人物
    ↓
fetch_biography()：获取入选人物的简介
    ↓
返回包含匹配依据和简介的列表
"""


def recommend_people(dominant_elements, people, language="zh", limit=3):
    matches = match_people(
        dominant_elements,
        people,
        limit=limit
    )

    for item in matches:
        item["biography"] = fetch_biography(
            item["person"],
            language=language
        )

    return matches


if __name__ == "__main__":
    people = prepare_people(PEOPLE)
    matches = recommend_people(["木", "土"], people)

    print("匹配人数：", len(matches))

    for item in matches:
        person = item["person"]
        biography = item["biography"]

        print("人物：", person["name"])
        print("共同最多项：", item["common_elements"])
        print("最多项完全相同：", item["same_dominant"])
        print("简介：", biography["summary"])
        print("原文：", biography["url"])

        if biography["error"]:
            print("失败原因：", biography["error"])
