import json
import urllib.request

URL = "https://boatraceopenapi.github.io/api/v1/today.json"


def get_data():

    with urllib.request.urlopen(URL, timeout=10) as response:

        return json.load(response)


def calculate_score(boat):

    score = 0

    # ==========================================
    # 最適化済みAIスコア
    # 2026年1月〜6月のデータで重みを探索
    # 2026年7月〜9月の未知データで検証済み
    # ==========================================

    # 全国勝率
    score += (
        boat.get("national_win_rate", 0)
        * 8.804
    )

    # 当地勝率
    score += (
        boat.get("local_win_rate", 0)
        * 4.059
    )

    # モーター2連対率
    score += (
        boat.get("motor_top_2_percent", 0)
        * 0.417
    )

    # 平均スタートタイミング
    # 速いほど高得点
    st = boat.get(
        "average_start_timing",
        0.2
    )

    score += (
        (0.20 - st)
        * 117.952
    )

    # 1号艇ボーナス
    if boat.get("entry_number") == 1:

        score += 25.603

    return score


# ==========================================
# データ取得
# ==========================================

data = get_data()

stadiums = data["programs"]["stadiums"]


print()
print("===================================")
print("      BOAT AI 今日の予想")
print("===================================")
print()

print(
    f"競艇場数: {len(stadiums)}"
)


# ==========================================
# 競艇場ごとの処理
# ==========================================

for stadium_number, stadium in stadiums.items():

    races = stadium.get(
        "races",
        {}
    )

    for race_number, race in races.items():

        racers = race.get(
            "racers",
            {}
        )

        boats = []


        # ==================================
        # 6艇のスコア計算
        # ==================================

        for entry_number, boat in racers.items():

            try:

                boat["entry_number"] = int(
                    entry_number
                )

            except:

                continue


            boat["score"] = calculate_score(
                boat
            )

            boats.append(
                boat
            )


        # 6艇揃っていないレースはスキップ
        if len(boats) != 6:

            continue


        # ==================================
        # AI順位
        # ==================================

        ranking = sorted(
            boats,
            key=lambda x: x["score"],
            reverse=True
        )


        print()

        print(
            "-----------------------------------"
        )

        print(
            f"競艇場 {stadium_number} "
            f"第{race_number}R"
        )

        print(
            "-----------------------------------"
        )


        # ==================================
        # AI順位
        # ==================================

        print(
            "AI順位:",
            " → ".join(
                str(
                    boat["entry_number"]
                )
                for boat in ranking
            )
        )


        # ==================================
        # AI上位3艇
        # ==================================

        top3 = [

            boat["entry_number"]

            for boat in ranking[:3]

        ]


        print(
            "AI上位3艇:",
            " → ".join(
                str(x)
                for x in top3
            )
        )


        # ==================================
        # 本命
        # ==================================

        print(
            "本命:",
            ranking[0]["entry_number"],
            "号艇"
        )


        # ==================================
        # AIスコア
        # ==================================

        print(
            "AIスコア:"
        )


        for rank, boat in enumerate(
            ranking,
            start=1
        ):

            print(
                f"{rank}位 "
                f"{boat['entry_number']}号艇 "
                f"{boat['score']:.2f}"
            )


print()
print("===================================")
print("      BOAT AI 予想終了")
print("===================================")