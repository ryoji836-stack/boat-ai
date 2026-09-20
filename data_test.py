import json
import urllib.request
from datetime import date, timedelta


BASE_URL = "https://boatraceopenapi.github.io/api/v1"

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 9, 19)

TRAIN_END = date(2026, 6, 30)
TEST_START = date(2026, 7, 1)


# ==========================================
# データ取得
# ==========================================

def get_day_data(target_date):

    ymd = target_date.strftime("%Y%m%d")

    url = f"{BASE_URL}/{target_date.year}/{ymd}.json"

    try:

        with urllib.request.urlopen(
            url,
            timeout=20
        ) as response:

            return json.load(response)

    except Exception as e:

        print(
            f"取得エラー {ymd}: {e}"
        )

        return None


# ==========================================
# レースデータ作成
# ==========================================

def make_races():

    races = []

    current = START_DATE

    success_days = 0
    error_days = 0

    while current <= END_DATE:

        print(
            f"取得中: {current}"
        )

        data = get_day_data(current)

        if data is None:

            error_days += 1

            current += timedelta(days=1)

            continue

        success_days += 1

        try:

            stadiums = (
                data["programs"]["stadiums"]
            )

            for stadium_number, stadium in stadiums.items():

                stadium_races = stadium.get(
                    "races",
                    {}
                )

                for race_number, race in stadium_races.items():

                    racers = race.get(
                        "racers",
                        {}
                    )

                    if len(racers) != 6:
                        continue


                    boats = []

                    for entry_number, boat in racers.items():

                        try:

                            entry = int(
                                entry_number
                            )

                        except:

                            continue


                        boats.append({

                            "entry_number": entry,

                            "national_win_rate":
                                float(
                                    boat.get(
                                        "national_win_rate",
                                        0
                                    ) or 0
                                ),

                            "local_win_rate":
                                float(
                                    boat.get(
                                        "local_win_rate",
                                        0
                                    ) or 0
                                ),

                            "motor_top_2_percent":
                                float(
                                    boat.get(
                                        "motor_top_2_percent",
                                        0
                                    ) or 0
                                ),

                            "average_start_timing":
                                float(
                                    boat.get(
                                        "average_start_timing",
                                        0.20
                                    ) or 0.20
                                ),

                        })


                    if len(boats) != 6:
                        continue


                    # ==================================
                    # 実際の結果
                    # ==================================

                    result = race.get(
                        "result",
                        {}
                    )

                    result_racers = result.get(
                        "racers",
                        {}
                    )

                    if len(result_racers) < 3:
                        continue


                    actual_order = []


                    for entry_number, result_boat in result_racers.items():

                        try:

                            place = int(
                                result_boat.get(
                                    "place_number",
                                    99
                                )
                            )

                        except:

                            place = 99


                        try:

                            entry = int(
                                entry_number
                            )

                        except:

                            continue


                        if place <= 3:

                            actual_order.append(
                                (
                                    place,
                                    entry
                                )
                            )


                    actual_order.sort()


                    if len(actual_order) != 3:
                        continue


                    actual_top3 = tuple(
                        x[1]
                        for x in actual_order
                    )


                    # ==================================
                    # 3連単払戻
                    # ==================================

                    trifecta_payout = 0

                    payouts = result.get(
                        "payouts",
                        {}
                    )

                    trifecta = payouts.get(
                        "trifecta",
                        []
                    )


                    if isinstance(
                        trifecta,
                        list
                    ):

                        for payout in trifecta:

                            combination = str(
                                payout.get(
                                    "combination",
                                    ""
                                )
                            ).replace(
                                "-",
                                ""
                            ).replace(
                                " ",
                                ""
                            )

                            amount = payout.get(
                                "amount",
                                0
                            )

                            try:

                                amount = int(
                                    amount
                                )

                            except:

                                amount = 0


                            predicted_string = "".join(
                                str(x)
                                for x in actual_top3
                            )


                            if combination == predicted_string:

                                trifecta_payout = amount

                                break


                    races.append({

                        "date": current,

                        "stadium_number":
                            stadium_number,

                        "race_number":
                            race_number,

                        "boats":
                            boats,

                        "actual_top3":
                            actual_top3,

                        "trifecta_payout":
                            trifecta_payout,

                    })

        except Exception as e:

            print(
                f"解析エラー {current}: {e}"
            )

        current += timedelta(days=1)


    print()
    print(
        "==================================="
    )
    print(
        "データ取得完了"
    )
    print(
        "==================================="
    )

    print(
        f"成功日数: {success_days}"
    )

    print(
        f"エラー日数: {error_days}"
    )

    print(
        f"レース数: {len(races)}"
    )

    print()

    return races


# ==========================================
# AIスコア
# ==========================================

def calculate_score(
    boat,
    weights
):

    national_weight = weights[0]
    local_weight = weights[1]
    motor_weight = weights[2]
    st_weight = weights[3]
    lane_bonus = weights[4]


    score = 0


    score += (
        boat["national_win_rate"]
        * national_weight
    )


    score += (
        boat["local_win_rate"]
        * local_weight
    )


    score += (
        boat["motor_top_2_percent"]
        * motor_weight
    )


    score += (
        (
            0.20
            - boat["average_start_timing"]
        )
        * st_weight
    )


    if boat["entry_number"] == 1:

        score += lane_bonus


    return score


# ==========================================
# レース予想
# ==========================================

def predict_race(
    race,
    weights
):

    ranking = sorted(

        race["boats"],

        key=lambda boat:
            calculate_score(
                boat,
                weights
            ),

        reverse=True

    )


    return tuple(

        boat["entry_number"]

        for boat in ranking

    )


# ==========================================
# 回収率評価
# ==========================================

def evaluate_return(
    races,
    weights
):

    total_races = 0

    win_count = 0

    place3_count = 0

    exact_count = 0

    investment = 0

    payout = 0


    for race in races:

        predicted = predict_race(
            race,
            weights
        )


        predicted_top1 = predicted[0]

        predicted_top3 = predicted[:3]

        actual_top3 = race["actual_top3"]


        # 本命1着
        if predicted_top1 == actual_top3[0]:

            win_count += 1


        # 本命3着以内
        if predicted_top1 in actual_top3:

            place3_count += 1


        # 3連単完全一致
        if predicted_top3 == actual_top3:

            exact_count += 1


        # 1レース100円
        investment += 100


        # 完全一致なら払戻
        if predicted_top3 == actual_top3:

            payout += race[
                "trifecta_payout"
            ]


        total_races += 1


    if total_races == 0:

        return {

            "races": 0,

            "win_rate": 0,

            "place3_rate": 0,

            "trifecta_rate": 0,

            "investment": 0,

            "payout": 0,

            "return_rate": 0,

            "profit": 0,

        }


    return {

        "races":
            total_races,

        "win_rate":
            win_count
            / total_races
            * 100,

        "place3_rate":
            place3_count
            / total_races
            * 100,

        "trifecta_rate":
            exact_count
            / total_races
            * 100,

        "investment":
            investment,

        "payout":
            payout,

        "return_rate":
            payout
            / investment
            * 100,

        "profit":
            payout
            - investment,

    }


# ==========================================
# メイン
# ==========================================

print()
print(
    "==================================="
)
print(
    "BOAT AI 回収率検証"
)
print(
    "==================================="
)
print()


# データ取得

all_races = make_races()


# ==========================================
# 学習期間 / テスト期間
# ==========================================

train_races = [

    race

    for race in all_races

    if race["date"] <= TRAIN_END

]


test_races = [

    race

    for race in all_races

    if race["date"] >= TEST_START

]


print(
    "==================================="
)
print(
    "期間"
)
print(
    "==================================="
)

print(
    f"学習期間: "
    f"{START_DATE} ～ {TRAIN_END}"
)

print(
    f"テスト期間: "
    f"{TEST_START} ～ {END_DATE}"
)

print()

print(
    f"学習レース数: "
    f"{len(train_races)}"
)

print(
    f"テストレース数: "
    f"{len(test_races)}"
)

print()


# ==========================================
# 最適化前
# ==========================================

baseline_weights = (

    10.0,   # 全国勝率

    8.0,    # 当地勝率

    0.5,    # モーター

    100.0,  # ST

    15.0,   # 1号艇

)


# ==========================================
# 最適化後
# ==========================================

optimized_weights = (

    8.804,   # 全国勝率

    4.059,   # 当地勝率

    0.417,   # モーター

    117.952, # ST

    25.603,  # 1号艇

)


# ==========================================
# 最適化前のテスト
# ==========================================

baseline_result = evaluate_return(

    test_races,

    baseline_weights

)


# ==========================================
# 最適化後のテスト
# ==========================================

optimized_result = evaluate_return(

    test_races,

    optimized_weights

)


# ==========================================
# 結果表示
# ==========================================

print()
print(
    "==================================="
)
print(
    "テスト期間：最適化前"
)
print(
    "==================================="
)

print(
    f"レース数: "
    f"{baseline_result['races']}"
)

print(
    f"本命1着率: "
    f"{baseline_result['win_rate']:.2f}%"
)

print(
    f"本命3着内率: "
    f"{baseline_result['place3_rate']:.2f}%"
)

print(
    f"3連単完全一致率: "
    f"{baseline_result['trifecta_rate']:.2f}%"
)

print(
    f"投資額: "
    f"{baseline_result['investment']:,}円"
)

print(
    f"払戻: "
    f"{baseline_result['payout']:,}円"
)

print(
    f"回収率: "
    f"{baseline_result['return_rate']:.2f}%"
)

print(
    f"収支: "
    f"{baseline_result['profit']:,}円"
)


print()
print(
    "==================================="
)
print(
    "テスト期間：最適化後"
)
print(
    "==================================="
)

print(
    f"レース数: "
    f"{optimized_result['races']}"
)

print(
    f"本命1着率: "
    f"{optimized_result['win_rate']:.2f}%"
)

print(
    f"本命3着内率: "
    f"{optimized_result['place3_rate']:.2f}%"
)

print(
    f"3連単完全一致率: "
    f"{optimized_result['trifecta_rate']:.2f}%"
)

print(
    f"投資額: "
    f"{optimized_result['investment']:,}円"
)

print(
    f"払戻: "
    f"{optimized_result['payout']:,}円"
)

print(
    f"回収率: "
    f"{optimized_result['return_rate']:.2f}%"
)

print(
    f"収支: "
    f"{optimized_result['profit']:,}円"
)


# ==========================================
# 比較
# ==========================================

print()
print(
    "==================================="
)
print(
    "最適化前 → 最適化後"
)
print(
    "==================================="
)

print(
    f"本命1着率: "
    f"{baseline_result['win_rate']:.2f}%"
    f" → "
    f"{optimized_result['win_rate']:.2f}%"
)

print(
    f"本命3着内率: "
    f"{baseline_result['place3_rate']:.2f}%"
    f" → "
    f"{optimized_result['place3_rate']:.2f}%"
)

print(
    f"3連単完全一致率: "
    f"{baseline_result['trifecta_rate']:.2f}%"
    f" → "
    f"{optimized_result['trifecta_rate']:.2f}%"
)

print(
    f"回収率: "
    f"{baseline_result['return_rate']:.2f}%"
    f" → "
    f"{optimized_result['return_rate']:.2f}%"
)

print(
    f"収支: "
    f"{baseline_result['profit']:,}円"
    f" → "
    f"{optimized_result['profit']:,}円"
)


print()
print(
    "==================================="
)
print(
    "回収率検証終了"
)
print(
    "==================================="
)