import sys
import urllib.request
import urllib.parse
import json
from datetime import datetime

# Windows 콘솔 인코딩(cp949) 호환성 보장
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 서울 위도 및 경도 좌표
SEOUL_LAT = 37.5665
SEOUL_LON = 126.9780

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


def get_seoul_weather():
    """
    실행한 날(오늘)의 서울 기준 오전 9시 및 오후 3시 날씨를 조회합니다.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # Open-Meteo API 요청 URL 구성 (서울 좌표 고정, 당일 24시간 데이터 요청)
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": SEOUL_LAT,
        "longitude": SEOUL_LON,
        "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m",
        "wind_speed_unit": "ms",
        "timezone": "Asia/Seoul",
        "forecast_days": 1,
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers={"User-Agent": "WeatherFetcher/1.0"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))

    hourly = data["hourly"]
    times = hourly["time"]

    # 오전 9시(09:00), 오후 3시(15:00)의 시간 문자열
    target_times = {
        "오전 9시": f"{today}T09:00",
        "오후 3시": f"{today}T15:00",
    }

    result = {
        "location": "서울",
        "date": today,
        "forecasts": {},
    }

    for label, target_time in target_times.items():
        if target_time in times:
            idx = times.index(target_time)
            code = hourly["weather_code"][idx]
            result["forecasts"][label] = {
                "time": target_time.replace("T", " "),
                "weather": WMO_WEATHER_CODES.get(code, "알 수 없음"),
                "temperature": f"{hourly['temperature_2m'][idx]}°C",
                "apparent_temperature": f"{hourly['apparent_temperature'][idx]}°C",
                "humidity": f"{hourly['relative_humidity_2m'][idx]}%",
                "precipitation_probability": f"{hourly['precipitation_probability'][idx]}%",
                "wind_speed": f"{hourly['wind_speed_10m'][idx]} m/s",
            }
        else:
            result["forecasts"][label] = None

    return result


def display_weather(weather_data):
    """조회된 날씨 정보를 콘솔에 출력합니다."""
    print("=" * 45)
    print(f"[날씨 예보] 위치: {weather_data['location']} | 날짜: {weather_data['date']}")
    print("=" * 45)

    for label, info in weather_data["forecasts"].items():
        print(f"\n[{label}] ({info['time']})")
        if info:
            print(f"  - 날씨 상태: {info['weather']}")
            print(f"  - 기온: {info['temperature']} (체감: {info['apparent_temperature']})")
            print(f"  - 습도: {info['humidity']}")
            print(f"  - 강수확률: {info['precipitation_probability']}")
            print(f"  - 풍속: {info['wind_speed']}")
        else:
            print("  - 날씨 데이터를 찾을 수 없습니다.")
    print("\n" + "=" * 45)


if __name__ == "__main__":
    # 오늘 서울의 오전 9시 및 오후 3시 날씨 조회 및 출력
    weather_info = get_seoul_weather()
    display_weather(weather_info)
