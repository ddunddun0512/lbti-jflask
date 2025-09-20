import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# 날짜 포맷 통일 (yyyy-mm-dd)
def format_date(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

# 자정으로 맞춰서 계산 안정화
def to_midnight(d: datetime) -> datetime:
    return d.replace(hour=0, minute=0, second=0, microsecond=0)

# ✅ 날짜 문자열 정규화 (20250907 → 2025-09-07)
def normalize_date(date_str: str) -> str:
    if not date_str:
        return ""
    date_str = date_str.strip()
    # yyyyMMdd → yyyy-MM-dd
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return date_str

# 복약 진행 계산
def calculate_progress(start_date_str: str, months: int):
    today = to_midnight(datetime.now())
    start = to_midnight(datetime.strptime(start_date_str, "%Y-%m-%d"))
    end = to_midnight(start + timedelta(days=months * 30))  # 단순 30일×개월 계산

    total_days = (end - start).days + 1
    elapsed_days = (today - start).days + 1
    safe_elapsed = max(0, min(elapsed_days, total_days))
    progress_percent = round((safe_elapsed / total_days) * 100, 1)
    remaining_days = max((end - today).days, 0)

    return {
        "startDate": format_date(start),
        "endDate": format_date(end),
        "elapsedDays": safe_elapsed,
        "totalDays": total_days,
        "progressPercent": progress_percent,
        "remainingDays": remaining_days
    }

@app.route("/")
def home():
    return "📌 복약계산기 Flask 서버 실행 중!"

@app.route("/medication", methods=["POST"])
def medication():
    try:
        req = request.get_json(force=True)
        print("DEBUG req:", req)  # 로그 확인용
        params = req.get("action", {}).get("params", {})

        start_date_raw = params.get("startDate")
        months_raw = params.get("months")

        # ✅ 날짜 정규화 적용
        start_date = normalize_date(start_date_raw)

        # ✅ 날짜 파라미터 검증 (엔터티 이름이 그대로 들어온 경우 방어)
        if start_date and start_date.startswith("sys."):
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [
                        {"simpleText": {"text": "⚠️ 날짜 입력이 잘못 전달됐어요. 예: 2025-09-07 또는 20250907"}}
                    ]
                }
            })

        # ✅ months 값 안전 변환
        try:
            months = int(str(months_raw).strip())
        except Exception:
            months = 0

        # ✅ 입력값 오류 처리
        if not start_date or months <= 0:
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [
                        {"simpleText": {"text": f"⚠️ 입력값 오류 (startDate={start_date_raw}, months={months_raw})"}}
                    ]
                }
            })

        # ✅ 정상 계산
        prog = calculate_progress(start_date, months)
        text = (
            f"📅 시작일: {prog['startDate']}\n"
            f"📌 복약 종료일: {prog['endDate']}\n"
            f"📈 복약 진행률: {prog['progressPercent']}%\n"
            f"⏳ 남은 일수: {prog['remainingDays']}일 (D-{prog['remainingDays']})\n\n"
            f"💪 오늘도 잊지 말고 복약 파이팅!"
        )

        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": text}}
                ],
                "quickReplies": [
                    {"label": "메인메뉴", "action": "message", "messageText": "메인메뉴"},
                    {"label": "다시 계산하기", "action": "message", "messageText": "복약 진행 확인"}
                ]
            }
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": f"⚠️ 서버 오류: {str(e)}"}}
                ]
            }
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
