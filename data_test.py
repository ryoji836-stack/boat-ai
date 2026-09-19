import json
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")

yesterday = (
    datetime.now(JST) - timedelta(days=1)
).strftime("%Y%m%d")

year = yesterday[:4]

url = (
    f"https://boatraceopenapi.github.io/"
    f"api/v1/{year}/{yesterday}.json"
)


print("=== 過去データテスト ===")
print("取得日:", yesterday)
print("URL:", url)

try:

    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.load(response)

    print("データ取得成功！")

    stadiums = data["programs"]["stadiums"]

    print("競艇場数:", len(stadiums))

    race_count = 0
    result_count = 0

    for stadium_number, stadium in stadiums.items():

        races = stadium.get("races", {})

        for race_number, race in races.items():

            race_count += 1

            result = race.get("result")

            if result and result.get("racers"):
                result_count += 1

    print("総レース数:", race_count)
    print("結果ありレース数:", result_count)

    if result_count > 0:
        print("過去結果データの取得に成功！")
    else:
        print("結果データが見つかりませんでした。")

except Exception as e:

    print("データ取得エラー:")
    print(e)