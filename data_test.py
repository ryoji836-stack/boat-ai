import json
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")


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

    # 1号艇を加点
    if boat.get("entry_number") == 1:
        score += 15

    return score


# 昨日のデータ
date = (
    datetime.now(JST) - timedelta(days=1)
).strftime("%Y%m%d")

year = date[:4]

url = (
    f"https://boatraceopenapi.github.io/"
    f"api/v1/{year}/{date}.json"
)


print("================================")
print(" BOAT AI 過去データ検証")
print("================================")
print("検証日:", date)
print()


try:

    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.load(response)

    stadiums = data["programs"]["stadiums"]

    total = 0
    main_win = 0
    main_top3 = 0
    top3_hit = 0
    trifecta_hit = 0

    trifecta_bet_count = 0
    trifecta_return = 0

    for stadium_number, stadium in stadiums.items():

        races = stadium.get("races", {})

        for race_number, race in races.items():

            racers = race.get("racers", {})
            result = race.get("result", {})
            result_racers = result.get("racers", {})

            # 6艇揃っていないレースは除外
            if len(racers) != 6:
                continue

            if len(result_racers) != 6:
                continue

            boats = []

            # AIスコア計算
            for entry_number, boat in racers.items():

                boat["entry_number"] = int(entry_number)
                boat["score"] = calculate_score(boat)

                boats.append(boat)

            # AI順位
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

            # 実際の着順
            actual_places = {}

            for entry_number, result_boat in result_racers.items():

                entry = int(entry_number)

                place = result_boat.get("place_number")

                if place is not None:
                    actual_places[entry] = int(place)

            if len(actual_places) != 6:
                continue

            actual_ranking = sorted(
                actual_places,
                key=lambda x: actual_places[x]
            )

            actual_top3 = actual_ranking[:3]

            total += 1

            # 本命1着
            if actual_ranking[0] == ai_main:
                main_win += 1

            # 本命3着以内
            if actual_places.get(ai_main, 99) <= 3:
                main_top3 += 1

            # AI上位3艇が実際の3着以内に全部入った
            if set(ai_top3) == set(actual_top3):
                top3_hit += 1

            # AI順位そのままの3連単
            if ai_top3 == actual_top3:
                trifecta_hit += 1

                payouts = result.get("payouts", {})
                trifecta = payouts.get("trifecta", [])

                for payout in trifecta:

                    combination = payout.get(
                        "combination", ""
                    )

                    if combination == (
                        f"{ai_top3[0]}-"
                        f"{ai_top3[1]}-"
                        f"{ai_top3[2]}"
                    ):

                        trifecta_return += payout.get(
                            "amount", 0
                        )

            trifecta_bet_count += 1


    print("検証レース数:", total)
    print()

    if total > 0:

        main_win_rate = (
            main_win / total * 100
        )

        main_top3_rate = (
            main_top3 / total * 100
        )

        top3_hit_rate = (
            top3_hit / total * 100
        )

        trifecta_hit_rate = (
            trifecta_hit / total * 100
        )

        investment = trifecta_bet_count * 100

        if investment > 0:
            return_rate = (
                trifecta_return / investment * 100
            )
        else:
            return_rate = 0

        print("========== 結果 ==========")
        print()

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

        print()

        print(
            f"3連単投資額: "
            f"{investment:,}円"
        )

        print(
            f"3連単払戻合計: "
            f"{trifecta_return:,}円"
        )

        print(
            f"3連単回収率: "
            f"{return_rate:.1f}%"
        )

        print()
        print("==========================")
        print("検証完了！")


except Exception as e:

    print("エラーが発生しました:")
    print(e)