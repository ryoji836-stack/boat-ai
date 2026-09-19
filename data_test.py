import json
import urllib.request
from datetime import date, timedelta
import random

BASE_URL = "https://boatraceopenapi.github.io/api/v1"

# ==========================================
# 設定
# ==========================================

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 9, 19)

# 学習期間
TRAIN_END = date(2026, 6, 30)

# テスト期間
TEST_START = date(2026, 7, 1)

# 試すパラメータ数
SEARCH_COUNT = 150

# ==========================================
# データ取得
# ==========================================

def get_day_data(target_date):

    ymd = target_date.strftime("%Y%m%d")

    url = f"{BASE_URL}/{target_date.year}/{ymd}.json"

    try:

        with urllib.request.urlopen(url, timeout=20) as response:

            return json.load(response)

    except Exception as e:

        print(f"データ取得エラー {ymd}: {e}")

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

        print(f"取得中: {current}")

        data = get_day_data(current)

        if data is None:

            error_days += 1

            current += timedelta(days=1)

            continue

        success_days += 1

        try:

            stadiums = data["programs"]["stadiums"]

            for stadium_number, stadium in stadiums.items():

                stadium_races = stadium.get("races", {})

                for race_number, race in stadium_races.items():

                    racers = race.get("racers", {})

                    if len(racers) != 6:
                        continue

                    boats = []

                    for entry_number, boat in racers.items():

                        try:
                            entry = int(entry_number)
                        except:
                            continue

                        boats.append({
                            "entry_number": entry,

                            "national_win_rate":
                                float(boat.get("national_win_rate", 0) or 0),

                            "local_win_rate":
                                float(boat.get("local_win_rate", 0) or 0),

                            "motor_top_2_percent":
                                float(boat.get("motor_top_2_percent", 0) or 0),

                            "average_start_timing":
                                float(boat.get("average_start_timing", 0.20) or 0.20),
                        })

                    if len(boats) != 6:
                        continue

                    # ----------------------------------
                    # 結果
                    # ----------------------------------

                    result = race.get("result", {})

                    result_racers = result.get("racers", {})

                    if len(result_racers) < 3:
                        continue

                    actual_order = []

                    for entry_number, result_boat in result_racers.items():

                        try:
                            place = int(
                                result_boat.get("place_number", 99)
                            )
                        except:
                            place = 99

                        try:
                            entry = int(entry_number)
                        except:
                            continue

                        if place <= 3:

                            actual_order.append(
                                (place, entry)
                            )

                    actual_order.sort()

                    if len(actual_order) != 3:
                        continue

                    actual_top3 = tuple(
                        x[1] for x in actual_order
                    )

                    races.append({
                        "date": current,
                        "boats": boats,
                        "actual_top3": actual_top3,
                    })

        except Exception as e:

            print(
                f"解析エラー {current}: {e}"
            )

        current += timedelta(days=1)

    print()
    print("===================================")
    print("データ取得完了")
    print("===================================")
    print(f"成功日数: {success_days}")
    print(f"エラー日数: {error_days}")
    print(f"レース数: {len(races)}")
    print()

    return races


# ==========================================
# AIスコア
# ==========================================

def calculate_score(boat, weights):

    national_weight = weights[0]
    local_weight = weights[1]
    motor_weight = weights[2]
    st_weight = weights[3]
    lane_bonus = weights[4]

    score = 0

    # 全国勝率
    score += (
        boat["national_win_rate"]
        * national_weight
    )

    # 当地勝率
    score += (
        boat["local_win_rate"]
        * local_weight
    )

    # モーター2連対率
    score += (
        boat["motor_top_2_percent"]
        * motor_weight
    )

    # スタートタイミング
    score += (
        (0.20 - boat["average_start_timing"])
        * st_weight
    )

    # 1号艇ボーナス
    if boat["entry_number"] == 1:

        score += lane_bonus

    return score


# ==========================================
# 1レースを評価
# ==========================================

def evaluate_race(race, weights):

    boats = race["boats"]

    ranking = sorted(
        boats,
        key=lambda boat:
            calculate_score(boat, weights),
        reverse=True
    )

    predicted_order = tuple(
        boat["entry_number"]
        for boat in ranking
    )

    predicted_top3 = predicted_order[:3]

    actual_top3 = race["actual_top3"]

    top1_win = (
        predicted_top3[0]
        == actual_top3[0]
    )

    actual_set = set(actual_top3)

    predicted_set = set(predicted_top3)

    top3_all = (
        predicted_set == actual_set
    )

    exact_trifecta = (
        predicted_top3 == actual_top3
    )

    # 本命が3着以内か
    top1_place3 = (
        predicted_top3[0]
        in actual_set
    )

    return (
        top1_win,
        top1_place3,
        top3_all,
        exact_trifecta
    )


# ==========================================
# 複数レース評価
# ==========================================

def evaluate(races, weights):

    if not races:

        return {
            "races": 0,
            "win_rate": 0,
            "place3_rate": 0,
            "top3_rate": 0,
            "trifecta_rate": 0,
        }

    win_count = 0
    place3_count = 0
    top3_count = 0
    trifecta_count = 0

    for race in races:

        result = evaluate_race(
            race,
            weights
        )

        if result[0]:
            win_count += 1

        if result[1]:
            place3_count += 1

        if result[2]:
            top3_count += 1

        if result[3]:
            trifecta_count += 1

    total = len(races)

    return {
        "races": total,

        "win_rate":
            win_count / total * 100,

        "place3_rate":
            place3_count / total * 100,

        "top3_rate":
            top3_count / total * 100,

        "trifecta_rate":
            trifecta_count / total * 100,
    }


# ==========================================
# 重みをランダム生成
# ==========================================

def random_weights():

    # 全国勝率
    national_weight = random.uniform(
        5.0,
        15.0
    )

    # 当地勝率
    local_weight = random.uniform(
        4.0,
        14.0
    )

    # モーター2連対率
    motor_weight = random.uniform(
        0.1,
        1.0
    )

    # スタート
    st_weight = random.uniform(
        20.0,
        150.0
    )

    # 1号艇ボーナス
    lane_bonus = random.uniform(
        0.0,
        30.0
    )

    return (
        national_weight,
        local_weight,
        motor_weight,
        st_weight,
        lane_bonus,
    )


# ==========================================
# メイン
# ==========================================

print()
print("===================================")
print("BOAT AI スコア最適化")
print("===================================")
print()

random.seed(42)

# データ取得
all_races = make_races()

# 学習・テスト分割

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

print("===================================")
print("学習・テスト分割")
print("===================================")

print(
    f"学習データ: {len(train_races)}レース"
)

print(
    f"テストデータ: {len(test_races)}レース"
)

print()


# ==========================================
# 現在の設定
# ==========================================

baseline_weights = (
    10.0,   # 全国勝率
    8.0,    # 当地勝率
    0.5,    # モーター
    100.0,  # ST
    15.0,   # 1号艇
)

print("===================================")
print("現在のAI")
print("===================================")

print(
    "重み:",
    baseline_weights
)

baseline_train = evaluate(
    train_races,
    baseline_weights
)

baseline_test = evaluate(
    test_races,
    baseline_weights
)

print()
print("【学習期間】")

print(
    f"本命1着率: "
    f"{baseline_train['win_rate']:.2f}%"
)

print(
    f"本命3着内率: "
    f"{baseline_train['place3_rate']:.2f}%"
)

print(
    f"上位3艇一致率: "
    f"{baseline_train['top3_rate']:.2f}%"
)

print(
    f"3連単完全一致率: "
    f"{baseline_train['trifecta_rate']:.2f}%"
)

print()

print("【テスト期間】")

print(
    f"本命1着率: "
    f"{baseline_test['win_rate']:.2f}%"
)

print(
    f"本命3着内率: "
    f"{baseline_test['place3_rate']:.2f}%"
)

print(
    f"上位3艇一致率: "
    f"{baseline_test['top3_rate']:.2f}%"
)

print(
    f"3連単完全一致率: "
    f"{baseline_test['trifecta_rate']:.2f}%"
)

print()


# ==========================================
# 最適化
# ==========================================

print("===================================")
print("重み最適化開始")
print("===================================")

results = []

for i in range(SEARCH_COUNT):

    weights = random_weights()

    score = evaluate(
        train_races,
        weights
    )

    results.append({
        "weights": weights,
        "metrics": score
    })

    if (i + 1) % 10 == 0:

        print(
            f"探索中: {i + 1}/{SEARCH_COUNT}"
        )


# ==========================================
# 学習期間で上位を表示
# ==========================================

results.sort(
    key=lambda x: (
        x["metrics"]["place3_rate"],
        x["metrics"]["win_rate"],
        x["metrics"]["top3_rate"]
    ),
    reverse=True
)

print()
print("===================================")
print("学習期間 TOP10")
print("===================================")

for i, result in enumerate(
    results[:10],
    start=1
):

    w = result["weights"]
    m = result["metrics"]

    print()

    print(
        f"{i}位"
    )

    print(
        "重み:",
        tuple(
            round(x, 3)
            for x in w
        )
    )

    print(
        f"本命1着率: "
        f"{m['win_rate']:.2f}%"
    )

    print(
        f"本命3着内率: "
        f"{m['place3_rate']:.2f}%"
    )

    print(
        f"上位3艇一致率: "
        f"{m['top3_rate']:.2f}%"
    )

    print(
        f"3連単完全一致率: "
        f"{m['trifecta_rate']:.2f}%"
    )


# ==========================================
# 最適重みをテスト期間で評価
# ==========================================

best = results[0]

best_weights = best["weights"]

test_result = evaluate(
    test_races,
    best_weights
)

train_result = evaluate(
    train_races,
    best_weights
)

print()
print("===================================")
print("最適化後AI")
print("===================================")

print(
    "採用した重み:",
    tuple(
        round(x, 3)
        for x in best_weights
    )
)

print()

print("【学習期間】")

print(
    f"本命1着率: "
    f"{train_result['win_rate']:.2f}%"
)

print(
    f"本命3着内率: "
    f"{train_result['place3_rate']:.2f}%"
)

print(
    f"上位3艇一致率: "
    f"{train_result['top3_rate']:.2f}%"
)

print(
    f"3連単完全一致率: "
    f"{train_result['trifecta_rate']:.2f}%"
)

print()

print("【未知のテスト期間】")

print(
    f"本命1着率: "
    f"{test_result['win_rate']:.2f}%"
)

print(
    f"本命3着内率: "
    f"{test_result['place3_rate']:.2f}%"
)

print(
    f"上位3艇一致率: "
    f"{test_result['top3_rate']:.2f}%"
)

print(
    f"3連単完全一致率: "
    f"{test_result['trifecta_rate']:.2f}%"
)

print()

print("===================================")
print("最適化終了")
print("===================================")