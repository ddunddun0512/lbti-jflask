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

# 날짜 문자열 정규화 (예: 20250907 → 2025-09-07)
def normalize_date(date_str: str) -> str:
    try:
        if len(date_str) == 8 and date_str.isdigit():
            # YYYYMMDD → YYYY-MM-DD
            return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        elif len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
            # 이미 YYYY-MM-DD 형태
            return date_str
    except:
        pass
    # 인식 못 하면 그대로 반환 (에러 처리되도록)
    return date_str

# 복약 진행 계산
def calculate_progress(start_date_str: str, months: int):
    today = to_midnight(datetime.now())
    start = to_midnight(datetime.strptime(start_date_str, "%Y-%m-%d"))
    # 종료일 = 시작일 + 개월 수 (단순히 30일×개월수로 계산)
    end = to_midnight(start + timedelta(days=months * 30))

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

# 기본 페이지 (테스트용)
@app.route("/")
def home():
    return "📌 복약계산기 Flask 서버 실행 중!"

# 카카오 스킬 엔드포인트
@app.route("/medication", methods=["POST"])
def medication():
    try:
        req = request.get_json(force=True)  # 카카오에서 보내는 JSON 파라미터 받기
        params = req.get("action", {}).get("params", {})

        start_date = params.get("startDate")
        months = params.get("months")

        # 날짜 정규화
        if start_date:
            start_date = normalize_date(start_date)

        # months를 안전하게 정수 변환
        try:
            months = int(months)
        except Exception:
            months = 0

        if not start_date or not months:
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [
                        {"simpleText": {
                            "text": "❗ 시작일과 복약 개월 수를 입력해주세요 (예: 2025-09-07 또는 20250907, 3개월)"
                        }}
                    ]
                }
            })

        prog = calculate_progress(start_date, months)

        text = (
            f"📅 시작일: {prog['startDate']}\n"
            f"📌 복약 종료일: {prog['endDate']}\n"
            f"📈 복약 진행률: {prog['progressPercent']}%\n"
            f"📆 오늘은 {prog['elapsedDays']}일차 입니다\n"
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
                    {"label": "메인", "action": "message", "messageText": "메인메뉴"},
                    {"label": "다시계산", "action": "message", "messageText": "복약 진행 확인"}
                ]
            }
        })

        except Exception as e:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": f"⚠️ 오류 발생: {str(e)}"}}
                ],
                "quickReplies": [
                    {"label": "메인", "action": "message", "messageText": "메인메뉴"},
                    {"label": "다시계산", "action": "message", "messageText": "복약 진행 확인"}
                ]
            }
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)