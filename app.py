print("BOAT AI START")

races = [
    {
        "race": "住之江10R",
        "prediction": ["1-3-4", "1-4-3", "3-1-4"]
    }
]

for race in races:
    print(race["race"])
    print("AI予想:")
    
    for bet in race["prediction"]:
        print(bet)