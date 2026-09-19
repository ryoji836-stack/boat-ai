import json

import urllib.request

url = "https://boatraceopenapi.github.io/api/v1/today.json"

try:

    with urllib.request.urlopen(url, timeout=10) as response:

        data = json.load(response)

    print("データ取得成功！")

    stadiums = data["programs"]["stadiums"]

    print("競艇場数:", len(stadiums))

    for stadium_number, stadium in stadiums.items():

        races = stadium.get("races", {})

        print(

            f"競艇場 {stadium_number}: "

            f"{len(races)}レース"

        )

except Exception as e:

    print("データ取得エラー:")

    print(e)