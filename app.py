print("=== BOAT AI 予想エンジン ===")

boats = [
    {
        "number": 1,
        "win_rate": 6.80,
        "local_rate": 7.10,
        "motor_rate": 42.5,
        "st": 0.15,
    },
    {
        "number": 2,
        "win_rate": 6.20,
        "local_rate": 6.50,
        "motor_rate": 38.2,
        "st": 0.16,
    },
    {
        "number": 3,
        "win_rate": 6.50,
        "local_rate": 6.80,
        "motor_rate": 45.1,
        "st": 0.14,
    },
    {
        "number": 4,
        "win_rate": 5.90,
        "local_rate": 6.10,
        "motor_rate": 40.8,
        "st": 0.17,
    },
    {
        "number": 5,
        "win_rate": 5.50,
        "local_rate": 5.80,
        "motor_rate": 35.4,
        "st": 0.18,
    },
    {
        "number": 6,
        "win_rate": 5.20,
        "local_rate": 5.60,
        "motor_rate": 37.9,
        "st": 0.19,
    },
]


def calculate_score(boat):
    score = 0

    # 全国勝率
    score += boat["win_rate"] * 10

    # 当地勝率
    score += boat["local_rate"] * 8

    # モーター
    score += boat["motor_rate"] * 0.5

    # STは小さいほど有利
    score += (0.20 - boat["st"]) * 100

    # 1号艇のコース優位
    if boat["number"] == 1:
        score += 15

    return score


for boat in boats:
    boat["score"] = calculate_score(boat)


ranking = sorted(
    boats,
    key=lambda x: x["score"],
    reverse=True
)


print("\n=== AI予想順位 ===")

for i, boat in enumerate(ranking, start=1):
    print(
        f"{i}位：{boat['number']}号艇 "
        f"スコア {boat['score']:.2f}"
    )


print("\n=== AI本命 ===")
print(f"{ranking[0]['number']}号艇")

print("\n=== AI上位3艇 ===")

top3 = [boat["number"] for boat in ranking[:3]]

print(top3)

print("\n=== 3連単候補 ===")

for first in top3:
    for second in top3:
        for third in top3:
            if len({first, second, third}) == 3:
                print(f"{first}-{second}-{third}")