import json
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")

START_DATE = datetime(2026, 1, 1, tzinfo=JST)
END_DATE = datetime.now(JST) - timedelta(days=1)


STADIUM_NAMES = {
    "01": "桐生",
    "02": "戸田",
    "03": "江戸川",
    "04": "平和島",
    "05": "多摩川",
    "06": "浜名湖",
    "07": "蒲郡",
    "08": "常滑",
    "09": "津",
    "10": "三国",
    "11": "びわこ",
    "12": "住之江",
    "13": "尼崎",
    "14": "鳴門",
    "15": "丸亀",
    "16": "児島",
    "17": "宮島",
    "18": "徳山",
    "19": "下関",
    "20": "若松",
    "21": "芦屋",
    "22": "福岡",
    "23": "唐津",
    "24": "大村"
}


def calculate_score(boat):

    score = 0

    score += boat.get(
        "national_win_rate", 0
    ) * 10

    score += boat.get(
        "local_win_rate", 0
    ) * 8

    score += boat.get(
        "motor_top_2_percent", 0
    ) * 0.5

    st = boat.get(
        "average_start_timing",
        0.20
    )

    score += (
        0.20 - st
    ) * 100

    if boat.get("entry_number") == 1:
        score += 15

    return score


def empty_stats():

    return {
        "races": 0,
        "main_win": 0,
        "main_top3": 0,
        "top3_hit": 0,
        "trifecta_hit": 0,
        "trifecta_return": 0
    }


def check_race(race):

    racers = race.get(
        "racers",
        {}
    )

    result = race.get(
        "result",
        {}
    )

    result_racers = result.get(
        "racers",
        {}
    )

    if len(racers) != 6:
        return None

    if len(result_racers) != 6:
        return None

    boats = []

    for entry_number, boat in racers.items():

        boat["entry_number"] = int(
            entry_number
        )

        boat["score"] = calculate_score(
            boat
        )

        boats.append(boat)

    ranking = sorted(
        boats,
        key=lambda x: x["score"],
        reverse=True
    )

    ai_main = ranking[0]["entry_number"]

    ai_top3 = [
        boat["entry_number"]
        for boat in ranking[:3]
    ]

    actual_places = {}

    for entry_number, result_boat in result_racers.items():

        entry = int(entry_number)

        place = result_boat.get(
            "place_number"
        )

        if place is not None:

            actual_places[entry] = int(
                place
            )

    if len(actual_places) != 6:
        return None

    actual_ranking = sorted(
        actual_places,
        key=lambda x: actual_places[x]
    )

    actual_top3 = actual_ranking[:3]

    main_win = (
        actual_ranking[0]
        == ai_main
    )

    main_top3 = (
        actual_places.get(
            ai_main,
            99
        ) <= 3
    )

    top3_hit = (
        set(ai_top3)
        == set(actual_top3)
    )

    trifecta_hit = (
        ai_top3
        == actual_top3
    )

    trifecta_return = 0

    payouts = result.get(
        "payouts",
        {}
    )

    trifecta = payouts.get(
        "trifecta",
        []
    )

    expected = (
        f"{ai_top3[0]}-"
        f"{ai_top3[1]}-"
        f"{ai_top3[2]}"
    )

    for payout in trifecta:

        combination = payout.get(
            "combination",
            ""
        )

        if combination == expected:

            trifecta_return += payout.get(
                "amount",
                0
            )

    return {
        "main_win": main_win,
        "main_top3": main_top3,
        "top3_hit": top3_hit,
        "trifecta_hit": trifecta_hit,
        "trifecta_return": trifecta_return
    }


def add_result(stats, result):

    stats["races"] += 1

    if result["main_win"]:
        stats["main_win"] += 1

    if result["main_top3"]:
        stats["main_top3"] += 1

    if result["top3_hit"]:
        stats["top3_hit"] += 1

    if result["trifecta_hit"]:
        stats["trifecta_hit"] += 1

    stats["trifecta_return"] += result[
        "trifecta_return"
    ]


print("================================")
print(" BOAT AI 競艇場別データ分析")
print("================================")

print(
    "開始日:",
    START_DATE.strftime("%Y-%m-%d")
)

print(
    "終了日:",
    END_DATE.strftime("%Y-%m-%d")
)

print()


stadium_stats = {}

for number in STADIUM_NAMES:

    stadium_stats[number] = (
        empty_stats()
    )


current_date = START_DATE

download_count = 0
error_count = 0


while current_date <= END_DATE:

    date_string = current_date.strftime(
        "%Y%m%d"
    )

    year = date_string[:4]

    url = (
        "https://boatraceopenapi.github.io/"
        f"api/v1/{year}/{date_string}.json"
    )

    try:

        with urllib.request.urlopen(
            url,
            timeout=10
        ) as response:

            data = json.load(response)

        download_count += 1

        stadiums = (
            data
            .get("programs", {})
            .get("stadiums", {})
        )

        for stadium_number, stadium in stadiums.items():

            if stadium_number not in stadium_stats:

                stadium_stats[stadium_number] = (
                    empty_stats()
                )

            races = stadium.get(
                "races",
                {}
            )

            for race in races.values():

                result = check_race(race)

                if result is None:
                    continue

                add_result(
                    stadium_stats[
                        stadium_number
                    ],
                    result
                )

    except Exception:

        error_count += 1

    current_date += timedelta(
        days=1
    )


print()
print("================================")
print(" データ取得終了")
print("================================")

print(
    "取得成功日数:",
    download_count
)

print(
    "取得エラー日数:",
    error_count
)


print()
print("================================")
print(" 競艇場別結果")
print("================================")


for stadium_number in sorted(
    stadium_stats.keys()
):

    stats = stadium_stats[
        stadium_number
    ]

    races = stats["races"]

    if races == 0:
        continue

    name = STADIUM_NAMES.get(
        stadium_number.zfill(2),
        f"競艇場{stadium_number}"
    )

    main_win_rate = (
        stats["main_win"]
        / races
        * 100
    )

    main_top3_rate = (
        stats["main_top3"]
        / races
        * 100
    )

    trifecta_hit_rate = (
        stats["trifecta_hit"]
        / races
        * 100
    )

    investment = races * 100

    return_rate = (
        stats["trifecta_return"]
        / investment
        * 100
    )

    print()
    print(
        f"【{stadium_number} {name}】"
    )

    print(
        "検証レース数:",
        races
    )

    print(
        f"本命1着率: "
        f"{main_win_rate:.1f}%"
    )

    print(
        f"本命3着以内率: "
        f"{main_top3_rate:.1f}%"
    )

    print(
        f"3連単的中率: "
        f"{trifecta_hit_rate:.1f}%"
    )

    print(
        f"3連単回収率: "
        f"{return_rate:.1f}%"
    )


print()
print("================================")
print(" 分析完了！")
print("================================")