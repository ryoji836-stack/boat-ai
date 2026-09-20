import json
import urllib.request
from datetime import date, timedelta


BASE_URL = "https://boatraceopenapi.github.io/api/v1"

START_DATE = date(2026, 7, 1)
END_DATE = date(2026, 9, 19)


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
# AIスコア
# ==========================================

def calculate_score(boat):

    score = 0

    score += (
        boat["national_win_rate"]
        * 8.804
    )

    score += (
        boat["local_win_rate"]
        * 4.059
    )

    score += (
        boat["motor_top_2_percent"]
        * 0.417
    )

    score += (
        (
            0.20
            - boat["average_start_timing"]
        )
        * 117.952
    )

    if boat["entry_number"] == 1:

        score += 25.603

    return score


# ==========================================
# 数字を安全に取得
# ==========================================

def to_float(value, default=0):

    try:

        return float(value)

    except:

        return default


# ==========================================
# 払戻取得
# ==========================================

def get_trifecta_payout(
    result,
    actual_top3
):

    payouts = result.get(
        "payouts",
        {}
    )

    trifecta = payouts.get(
        "trifecta",
        []
    )

    actual_string = "".join(
        str(x)
        for x in actual_top3
    )

    for payout in trifecta:

        combination = str(
            payout.get(
                "combination",
                ""
            )
        )

        combination = (
            combination
            .replace("-", "")
            .replace(" ", "")
            .replace("→", "")
        )

        if combination == actual_string:

            return to_float(
                payout.get(
                    "amount",
                    0
                )
            )

    return 0


# ==========================================
# レースデータ取得
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

                            "entry_number":
                                entry,

                            "national_win_rate":
                                to_float(
                                    boat.get(
                                        "national_win_rate",
                                        0
                                    )
                                ),

                            "local_win_rate":
                                to_float(
                                    boat.get(
                                        "local_win_rate",
                                        0
                                    )
                                ),

                            "motor_top_2_percent":
                                to_float(
                                    boat.get(
                                        "motor_top_2_percent",
                                        0
                                    )
                                ),

                            "average_start_timing":
                                to_float(
                                    boat.get(
                                        "average_start_timing",
                                        0.20
                                    ),
                                    0.20
                                ),

                        })


                    if len(boats) != 6:

                        continue


                    # ==============================
                    # 実際の結果
                    # ==============================

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


                    # ==============================
                    # AI予想
                    # ==============================

                    ranking = sorted(

                        boats,

                        key=lambda boat:
                            calculate_score(
                                boat
                            ),

                        reverse=True

                    )


                    predicted = tuple(
                        boat["entry_number"]
                        for boat in ranking
                    )


                    predicted_top3 = predicted[:3]

                    top1 = predicted[0]

                    top1_score = calculate_score(
                        ranking[0]
                    )

                    top2_score = calculate_score(
                        ranking[1]
                    )

                    score_gap = (
                        top1_score
                        - top2_score
                    )


                    # ==============================
                    # 3連単払戻
                    # ==============================

                    trifecta_payout = (
                        get_trifecta_payout(
                            result,
                            actual_top3
                        )
                    )


                    races.append({

                        "stadium":
                            str(stadium_number),

                        "race_number":
                            int(race_number),

                        "predicted":
                            predicted,

                        "top1":
                            top1,

                        "top3":
                            predicted_top3,

                        "actual_top3":
                            actual_top3,

                        "score_gap":
                            score_gap,

                        "payout":
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
        f"分析レース数: {len(races)}"
    )

    print()

    return races


# ==========================================
# 指標計算
# ==========================================

def calculate_metrics(races):

    total = len(races)

    if total == 0:

        return {

            "count": 0,
            "win_rate": 0,
            "place3_rate": 0,
            "trifecta_rate": 0,
            "investment": 0,
            "payout": 0,
            "return_rate": 0,
            "profit": 0,

        }


    win_count = 0

    place3_count = 0

    trifecta_count = 0

    payout = 0


    for race in races:

        actual = race["actual_top3"]

        top1 = race["top1"]

        top3 = race["top3"]


        if top1 == actual[0]:

            win_count += 1


        if top1 in actual:

            place3_count += 1


        if top3 == actual:

            trifecta_count += 1

            payout += race["payout"]


    investment = total * 100

    return_rate = 0

    if investment > 0:

        return_rate = (
            payout
            / investment
            * 100
        )


    return {

        "count":
            total,

        "win_rate":
            win_count
            / total
            * 100,

        "place3_rate":
            place3_count
            / total
            * 100,

        "trifecta_rate":
            trifecta_count
            / total
            * 100,

        "investment":
            investment,

        "payout":
            payout,

        "return_rate":
            return_rate,

        "profit":
            payout
            - investment,

    }


# ==========================================
# 表示
# ==========================================

def print_metrics(
    title,
    races
):

    metrics = calculate_metrics(
        races
    )

    print()
    print(
        "-----------------------------------"
    )

    print(title)

    print(
        "-----------------------------------"
    )

    print(
        f"レース数: "
        f"{metrics['count']:,}"
    )

    print(
        f"本命1着率: "
        f"{metrics['win_rate']:.2f}%"
    )

    print(
        f"本命3着内率: "
        f"{metrics['place3_rate']:.2f}%"
    )

    print(
        f"3連単完全一致率: "
        f"{metrics['trifecta_rate']:.2f}%"
    )

    print(
        f"回収率: "
        f"{metrics['return_rate']:.2f}%"
    )

    print(
        f"収支: "
        f"{metrics['profit']:,.0f}円"
    )


# ==========================================
# メイン
# ==========================================

print()
print(
    "==================================="
)
print(
    "BOAT AI 条件別分析"
)
print(
    "==================================="
)
print()

races = make_races()


# ==========================================
# 全体
# ==========================================

print(
    "==================================="
)
print(
    "① 全体"
)
print(
    "==================================="
)

print_metrics(
    "2026/7/1 ～ 9/19",
    races
)


# ==========================================
# 競艇場別
# ==========================================

stadiums = sorted(
    set(
        race["stadium"]
        for race in races
    ),
    key=lambda x: int(x)
)


print()
print(
    "==================================="
)
print(
    "② 競艇場別"
)
print(
    "==================================="
)


for stadium in stadiums:

    stadium_races = [

        race

        for race in races

        if race["stadium"] == stadium

    ]


    if len(stadium_races) < 100:

        continue


    metrics = calculate_metrics(
        stadium_races
    )


    print(
        f"{stadium}場 "
        f"{metrics['count']}R "
        f"1着 {metrics['win_rate']:.1f}% "
        f"3着内 {metrics['place3_rate']:.1f}% "
        f"3連単 {metrics['trifecta_rate']:.1f}% "
        f"回収 {metrics['return_rate']:.1f}% "
        f"収支 {metrics['profit']:,.0f}円"
    )


# ==========================================
# 本命の号艇別
# ==========================================

print()
print(
    "==================================="
)
print(
    "③ AI本命の号艇別"
)
print(
    "==================================="
)


for boat_number in range(1, 7):

    boat_races = [

        race

        for race in races

        if race["top1"] == boat_number

    ]


    if len(boat_races) < 100:

        continue


    metrics = calculate_metrics(
        boat_races
    )


    print(
        f"{boat_number}号艇本命 "
        f"{metrics['count']}R "
        f"1着 {metrics['win_rate']:.1f}% "
        f"3着内 {metrics['place3_rate']:.1f}% "
        f"3連単 {metrics['trifecta_rate']:.1f}% "
        f"回収 {metrics['return_rate']:.1f}% "
        f"収支 {metrics['profit']:,.0f}円"
    )


# ==========================================
# AIスコア差別
# ==========================================

print()
print(
    "==================================="
)
print(
    "④ AIスコア差別"
)
print(
    "==================================="
)


gap_groups = [

    (
        "0～5",
        0,
        5
    ),

    (
        "5～10",
        5,
        10
    ),

    (
        "10～20",
        10,
        20
    ),

    (
        "20～30",
        20,
        30
    ),

    (
        "30以上",
        30,
        999999
    ),

]


for name, low, high in gap_groups:

    group = [

        race

        for race in races

        if low
        <= race["score_gap"]
        < high

    ]


    if len(group) < 100:

        continue


    metrics = calculate_metrics(
        group
    )


    print(
        f"スコア差 {name} "
        f"{metrics['count']}R "
        f"1着 {metrics['win_rate']:.1f}% "
        f"3着内 {metrics['place3_rate']:.1f}% "
        f"3連単 {metrics['trifecta_rate']:.1f}% "
        f"回収 {metrics['return_rate']:.1f}% "
        f"収支 {metrics['profit']:,.0f}円"
    )


# ==========================================
# レース番号別
# ==========================================

print()
print(
    "==================================="
)
print(
    "⑤ レース番号別"
)
print(
    "==================================="
)


for race_number in range(1, 13):

    group = [

        race

        for race in races

        if race["race_number"]
        == race_number

    ]


    if len(group) < 100:

        continue


    metrics = calculate_metrics(
        group
    )


    print(
        f"{race_number}R "
        f"{metrics['count']}R "
        f"1着 {metrics['win_rate']:.1f}% "
        f"3着内 {metrics['place3_rate']:.1f}% "
        f"3連単 {metrics['trifecta_rate']:.1f}% "
        f"回収 {metrics['return_rate']:.1f}% "
        f"収支 {metrics['profit']:,.0f}円"
    )


# ==========================================
# 信頼度候補
# ==========================================

print()
print(
    "==================================="
)
print(
    "⑥ 高信頼度候補"
)
print(
    "==================================="
)

print(
    "スコア差が大きいレースだけを"
    "取り出した場合の参考値"
)


high_confidence = [

    race

    for race in races

    if race["score_gap"] >= 20

]


print_metrics(
    "スコア差20点以上",
    high_confidence
)


very_high_confidence = [

    race

    for race in races

    if race["score_gap"] >= 30

]


print_metrics(
    "スコア差30点以上",
    very_high_confidence
)


# ==========================================
# 終了
# ==========================================

print()
print(
    "==================================="
)
print(
    "条件別分析終了"
)
print(
    "==================================="
)