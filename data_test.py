import json
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")

START_DATE = datetime(2026, 1, 1, tzinfo=JST)
END_DATE = datetime.now(JST) - timedelta(days=1)


def calculate_score(boat):
    score = 0

    # 全国勝率
    score += boat.get("national_win_rate", 0) * 10

    # 当地勝率
    score += boat.get("local_win_rate", 0) * 8

    # モーター2連対率
    score += boat.get("motor_top_2_percent", 0) * 0.5

    # 平均スタート
    st = boat.get("average_start_timing", 0.20)
    score += (0.20 - st) * 100

    # 1号艇補正
    if boat.get("entry_number") == 1:
        score += 15

    return score


def check_race(race):
    racers = race.get("racers", {})
    result = race.get("result", {})
    result_racers = result.get("racers", {})

    if len(racers) != 6:
        return None

    if len(result_racers) != 6:
        return None

    boats = []

    for entry_number, boat in racers.items():

        boat["entry_number"] = int(entry_number)
        boat["score"] = calculate_score(boat)

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

        place = result_boat.get("place_number")

        if place is not None:
            actual_places[entry] = int(place)

    if len(actual_places) != 6:
        return None

    actual_ranking = sorted(
        actual_places,
        key=lambda x: actual_places[x]
    )

    actual_top3 = actual_ranking[:3]

    main_win = (
        actual_ranking[0] == ai_main
    )

    main_top3 = (
        actual_places.get(ai_main, 99) <= 3
    )

    top3_hit = (
        set(ai_top3) == set(actual_top3)
    )

    trifecta_hit = (
        ai_top3 == actual_top3
    )

    trifecta_return = 0

    payouts = result.get("payouts", {})
    trifecta = payouts.get("trifecta", [])

    for payout in trifecta:

        combination = payout.get(
            "combination", ""
        )

        expected = (
            f"{ai_top3[0]}-"
            f"{ai_top3[1]}-"
            f"{ai_top3[2]}"
        )

        if combination == expected:

            trifecta_return += payout.get(
                "amount", 0
            )

    return {
        "main_win": main_win,
        "main_top3": main_top3,
        "top3_hit": top3_hit,
        "trifecta_hit": trifecta_hit,
        "trifecta_return": trifecta_return,
    }


def empty_stats():
    return {
        "races": 0,
        "main_win": 0,
        "main_top3": 0,
        "top3_hit": 0,
        "trifecta_hit": 0,
        "trifecta_return": 0,
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


def print_stats(name, stats):

    races = stats["races"]

    print()
    print("================================")
    print(name)
    print("================================")

    if races == 0:
        print("検証レースなし")
        return

    main_win_rate = (
        stats["main_win"] / races * 100
    )

    main_top3_rate = (
        stats["main_top3"] / races * 100
    )

    top3_hit_rate = (
        stats["top3_hit"] / races * 100
    )

    trifecta_hit_rate = (
        stats["trifecta_hit"] / races * 100
    )

    investment = races * 100

    return_rate = (
        stats["trifecta_return"]
        / investment
        * 100
    )

    print("検証レース数:", races)

    print(
        f"本命1着率: "
        f"{main_win_rate:.1f}%"
    )

    print(
        f"本命3着以内率: "
        f"{main_top3_rate:.1f}%"
    )

    print(
        f"AI上位3艇一致率: "
        f"{top3_hit_rate:.1f}%"
    )

    print(
        f"3連単そのまま的中率: "
        f"{trifecta_hit_rate:.1f}%"
    )

    print(
        f"3連単投資額: "
        f"{investment:,}円"
    )

    print(
        f"3連単払戻合計: "
        f"{stats['trifecta_return']:,}円"
    )

    print(
        f"3連単回収率: "
        f"{return_rate:.1f}%"
    )


print("================================")
print(" BOAT AI 全期間データ検証")
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


all_stats = empty_stats()
first_half_stats = empty_stats()
second_half_stats = empty_stats()

current_date = START_DATE
download_count = 0
error_count = 0


while current_date <= END_DATE:

    date_string = current_date.strftime("%Y%m%d")
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

        day_races = 0

        for stadium in stadiums.values():

            races = stadium.get("races", {})

            for race in races.values():

                result = check_race(race)

                if result is None:
                    continue

                add_result(
                    all_stats,
                    result
                )

                # 2026年1月〜6月
                if current_date.month <= 6:

                    add_result(
                        first_half_stats,
                        result
                    )

                # 2026年7月以降
                else:

                    add_result(
                        second_half_stats,
                        result
                    )

                day_races += 1

        print(
            f"{date_string}: "
            f"{day_races}レース検証"
        )

    except Exception as e:

        error_count += 1

        print(
            f"{date_string}: "
            f"取得スキップ"
        )

    current_date += timedelta(days=1)


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


print_stats(
    "2026年1月〜6月",
    first_half_stats
)

print_stats(
    "2026年7月〜現在",
    second_half_stats
)

print_stats(
    "2026年全期間",
    all_stats
)


print()
print("================================")
print(" 全期間検証完了！")
print("================================")