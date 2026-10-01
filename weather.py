import sys
import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta

# Windows 콘솔 인코딩(cp949) 호환성 보장
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 5개 주요 도시 정보 (번호, 도시명, 위도, 경도)
CITIES = {
    1: {"name": "서울", "lat": 37.5665, "lon": 126.9780},
    2: {"name": "부산", "lat": 35.1796, "lon": 129.0756},
    3: {"name": "대구", "lat": 35.8714, "lon": 128.6014},
    4: {"name": "인천", "lat": 37.4563, "lon": 126.7052},
    5: {"name": "광주", "lat": 35.1595, "lon": 126.8526},
}

# WMO 날씨 코드 매핑 (기상 상태 설명)
WMO_WEATHER_CODES = {
    0: "맑음",
    1: "대체로 맑음",
    2: "구름 조금",
    3: "흐림",
    45: "안개",
    48: "서리 안개",
    51: "약한 이슬비",
    53: "중간 이슬비",
    55: "강한 이슬비",
    56: "약한 결빙성 이슬비",
    57: "강한 결빙성 이슬비",
    61: "약한 비",
    63: "중간 비",
    65: "강한 비",
    66: "약한 어는 비",
    67: "강한 어는 비",
    71: "약한 눈",
    73: "중간 눈",
    75: "폭설",
    77: "싸락눈",
    80: "약한 소나기",
    81: "중간 소나기",
    82: "격렬한 소나기",
    85: "약한 눈 소나기",
    86: "강한 눈 소나기",
    95: "뇌우",
    96: "뇌우 및 약한 우박",
    99: "뇌우 및 강한 우박",
}


def get_weather(city_choice="서울"):
    """
    선택한 도시의 오늘과 다음날 9시, 15시, 21시 날씨를 조회합니다.

    :param city_choice: 번호(int/str 1~5) 또는 도시명("서울", "부산" 등)
    """
    # 입력값을 기반으로 도시 좌표 찾기
    selected_city = None
    if isinstance(city_choice, int) and city_choice in CITIES:
        selected_city = CITIES[city_choice]
    elif isinstance(city_choice, str):
        if city_choice.isdigit() and int(city_choice) in CITIES:
            selected_city = CITIES[int(city_choice)]
        else:
            for info in CITIES.values():
                if info["name"] == city_choice:
                    selected_city = info
                    break

    if not selected_city:
        raise ValueError(
            f"유효하지 않은 도시입니다: {city_choice}. (가능한 도시: {[c['name'] for c in CITIES.values()]})"
        )

    city_name = selected_city["name"]
    lat = selected_city["lat"]
    lon = selected_city["lon"]

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    # Open-Meteo API 요청 URL 구성 (forecast_days=2로 오늘과 다음날 데이터 요청)
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m",
        "wind_speed_unit": "ms",
        "timezone": "Asia/Seoul",
        "forecast_days": 2,
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers={"User-Agent": "WeatherFetcher/1.0"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))

    hourly = data["hourly"]
    times = hourly["time"]

    # 조회 대상: 오늘과 다음날의 9시, 15시, 21시
    targets = {
        "오늘": {
            "date": today,
            "slots": {
                "09시": f"{today}T09:00",
                "15시": f"{today}T15:00",
                "21시": f"{today}T21:00",
            },
        },
        "다음날": {
            "date": tomorrow,
            "slots": {
                "09시": f"{tomorrow}T09:00",
                "15시": f"{tomorrow}T15:00",
                "21시": f"{tomorrow}T21:00",
            },
        },
    }

    result = {
        "location": city_name,
        "days": {},
    }

    for day_label, day_info in targets.items():
        date_str = day_info["date"]
        result["days"][day_label] = {
            "date": date_str,
            "forecasts": {},
        }
        for time_label, target_time in day_info["slots"].items():
            if target_time in times:
                idx = times.index(target_time)
                code = hourly["weather_code"][idx]
                result["days"][day_label]["forecasts"][time_label] = {
                    "time": target_time.replace("T", " "),
                    "weather": WMO_WEATHER_CODES.get(code, "알 수 없음"),
                    "temperature": f"{hourly['temperature_2m'][idx]}°C",
                    "apparent_temperature": f"{hourly['apparent_temperature'][idx]}°C",
                    "humidity": f"{hourly['relative_humidity_2m'][idx]}%",
                    "precipitation_probability": f"{hourly['precipitation_probability'][idx]}%",
                    "wind_speed": f"{hourly['wind_speed_10m'][idx]} m/s",
                }
            else:
                result["days"][day_label]["forecasts"][time_label] = None

    return result


def display_weather(weather_data):
    """조회된 날씨 정보를 콘솔에 보기 쉽게 출력합니다."""
    print("\n" + "=" * 45)
    print(f"[날씨 예보] 위치: {weather_data['location']}")
    print("=" * 45)

    for day_label, day_data in weather_data["days"].items():
        print(f"\n▶ {day_label} ({day_data['date']})")
        print("-" * 35)

        for slot_label, info in day_data["forecasts"].items():
            if info:
                print(f"  [{slot_label}] ({info['time'].split(' ')[1]})")
                print(f"    - 날씨 상태: {info['weather']}")
                print(f"    - 기온: {info['temperature']} (체감: {info['apparent_temperature']})")
                print(f"    - 습도: {info['humidity']}")
                print(f"    - 강수확률: {info['precipitation_probability']}")
                print(f"    - 풍속: {info['wind_speed']}")
            else:
                print(f"  [{slot_label}] 날씨 데이터를 찾을 수 없습니다.")
    print("\n" + "=" * 45)


def select_city():
    """사용자로부터 5개 주요 도시 중 하나를 선택받습니다."""
    print("=" * 45)
    print("날씨를 조회할 도시를 선택하세요:")
    for num, info in CITIES.items():
        print(f"  {num}. {info['name']}")
    print("=" * 45)

    user_input = input("번호를 입력하세요 (1-5, 엔터 입력 시 서울): ").strip()
    if not user_input:
        return "서울"
    return user_input


if __name__ == "__main__":
    choice = select_city()
    weather_info = get_weather(choice)
    display_weather(weather_info)
