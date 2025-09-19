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

# 복약 진행 계산
def calculate_progress(start_date_str: str, months: int):
    today = to_midnight(datetime.now())
    start = to_midnight(datetime.strptime(start_date_str, "%Y-%m-%d"))
    # 종료일 = 시작일 + 개월 수 (포함 계산 위해 하루 빼줌)
    end = to_midnight(start + timedelta(days=months*30))  # 단순히 30일×개월수로 계산

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
        months = int(params.get("months", 0))

        if not start_date or not months:
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [
                        {"simpleText": {"text": "❗ 시작일과 복약 개월 수를 입력해주세요 (예: 2025-09-01, 3개월)"}}
                    ]
                }
            })

        prog = calculate_progress(start_date, months)

        text = (
            f"📌 복약 종료일: {prog['endDate']}\n"
            f"📈 복약 진행률: {prog['progressPercent']}%\n"
            f"⏳ 남은 일수: D-{prog['remainingDays']}"
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
                ]
            }
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)