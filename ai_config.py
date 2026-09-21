# ==========================================
# BOAT AI 設定ファイル
# ==========================================

# AIスコア係数
NATIONAL_WIN_RATE_WEIGHT = 8.804
LOCAL_WIN_RATE_WEIGHT = 4.059
MOTOR_TOP2_WEIGHT = 0.417
START_TIMING_WEIGHT = 117.952
LANE_1_BONUS = 25.603


# ------------------------------------------
# AIスコア計算
# ------------------------------------------

def calculate_score(boat):
    score = 0.0

    # 全国勝率
    score += boat.get("national_win_rate", 0) * NATIONAL_WIN_RATE_WEIGHT

    # 当地勝率
    score += boat.get("local_win_rate", 0) * LOCAL_WIN_RATE_WEIGHT

    # モーター2連率
    score += boat.get("motor_top_2_percent", 0) * MOTOR_TOP2_WEIGHT

    # 平均ST
    st = boat.get("average_start_timing", 0.20)
    score += (0.20 - st) * START_TIMING_WEIGHT

    # 1号艇補正
    if int(boat.get("entry_number", 0)) == 1:
        score += LANE_1_BONUS

    return score


# ------------------------------------------
# スコア差
# ------------------------------------------

def get_score_gap(ranking):
    if len(ranking) < 2:
        return 0.0

    return ranking[0]["score"] - ranking[1]["score"]


# ------------------------------------------
# 信頼度
# ------------------------------------------

def get_confidence(score_gap):
    if score_gap >= 30:
        return "高"
    elif score_gap >= 20:
        return "中"
    elif score_gap >= 10:
        return "低"
    else:
        return "見送り"


# ------------------------------------------
# 買い目判定
# ------------------------------------------

def is_recommended(score_gap):
    return score_gap >= 20


# ------------------------------------------
# 3連単予想
# ------------------------------------------

def get_trifecta(ranking):
    if len(ranking) < 3:
        return []

    return [
        ranking[0]["entry_number"],
        ranking[1]["entry_number"],
        ranking[2]["entry_number"]
    ]