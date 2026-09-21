import json
import urllib.request

from ai_config import (
    calculate_score,
    get_score_gap,
    get_confidence,
    is_recommended,
    get_trifecta,
)

# ==========================================
# BOAT AI
# 今日のレースデータ取得
# ==========================================

URL = "https://boatraceopenapi.github.io/api/v1/today.json"


def get_data():
    with urllib.request.urlopen(URL, timeout=10) as response:
        return json.load(response)


# ==========================================
# レースをAI予想
# ==========================================

def predict_race(race):
    racers = race.get("racers", {})

    boats = []

    for entry_number, boat in racers.items():

        boat = dict(boat)

        boat["entry_number"] = int(entry_number)

        boat["score"] = calculate_score(boat)

        boats.append(boat)

    # 6艇揃っていないレースは除外
    if len(boats) != 6:
        return None

    # スコア順
    ranking = sorted(
        boats,
        key=lambda x: x["score"],
        reverse=True
    )

    score_gap = get_score_gap(ranking)

    confidence = get_confidence(score_gap)

    recommended = is_recommended(score_gap)

    trifecta = get_trifecta(ranking)

    return {
        "ranking": ranking,
        "score_gap": score_gap,
        "confidence": confidence,
        "recommended": recommended,
        "trifecta": trifecta,
    }


# ==========================================
# メイン処理
# ==========================================

def main():

    print("=" * 50)
    print("              BOAT AI")
    print("          今日のAI予想")
    print("=" * 50)

    try:
        data = get_data()
    except Exception as e:
        print()
        print("データ取得エラー")
        print(e)
        return

    programs = data.get("programs", {})
    stadiums = programs.get("stadiums", {})

    print()
    print(f"競艇場数: {len(stadiums)}")
    print()

    total_races = 0
    recommended_races = 0

    # ==========================================
    # 競艇場
    # ==========================================

    for stadium_number, stadium in stadiums.items():

        races = stadium.get("races", {})

        # ======================================
        # レース
        # ======================================

        for race_number, race in races.items():

            prediction = predict_race(race)

            if prediction is None:
                continue

            total_races += 1

            ranking = prediction["ranking"]
            score_gap = prediction["score_gap"]
            confidence = prediction["confidence"]
            recommended = prediction["recommended"]
            trifecta = prediction["trifecta"]

            if recommended:
                recommended_races += 1

            print("-" * 50)

            print(
                f"競艇場 {stadium_number} "
                f"第{race_number}R"
            )

            print()

            # ----------------------------------
            # AI順位
            # ----------------------------------

            ranking_numbers = [
                str(boat["entry_number"])
                for boat in ranking
            ]

            print(
                "AI順位:",
                " → ".join(ranking_numbers)
            )

            # ----------------------------------
            # AIスコア
            # ----------------------------------

            print()
            print("AIスコア")

            for boat in ranking:

                print(
                    f'{boat["entry_number"]}号艇: '
                    f'{boat["score"]:.2f}'
                )

            # ----------------------------------
            # 本命
            # ----------------------------------

            print()

            print(
                "AI本命:",
                f'{ranking[0]["entry_number"]}号艇'
            )

            # ----------------------------------
            # 上位3艇
            # ----------------------------------

            print(
                "AI上位3艇:",
                trifecta
            )

            # ----------------------------------
            # スコア差
            # ----------------------------------

            print(
                f"スコア差: {score_gap:.2f}"
            )

            # ----------------------------------
            # 信頼度
            # ----------------------------------

            print(
                f"信頼度: {confidence}"
            )

            # ----------------------------------
            # 推奨判定
            # ----------------------------------

            if recommended:

                print(
                    "AI判定: ★ 推奨候補"
                )

            else:

                print(
                    "AI判定: △ 見送り候補"
                )

            # ----------------------------------
            # 3連単
            # ----------------------------------

            print()

            if len(trifecta) == 3:

                print(
                    "3連単予想:",
                    f"{trifecta[0]}"
                    f"→{trifecta[1]}"
                    f"→{trifecta[2]}"
                )

    # ==========================================
    # 集計
    # ==========================================

    print()
    print("=" * 50)
    print("BOAT AI 今日の集計")
    print("=" * 50)

    print()
    print(
        f"分析レース数: {total_races}"
    )

    print(
        f"推奨候補: {recommended_races}"
    )

    if total_races > 0:

        rate = (
            recommended_races
            / total_races
            * 100
        )

        print(
            f"推奨候補率: {rate:.1f}%"
        )

    print()
    print("AI予想処理完了")
    print("=" * 50)


# ==========================================
# 実行
# ==========================================

if __name__ == "__main__":
    main()