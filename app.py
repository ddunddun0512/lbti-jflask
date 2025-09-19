@app.route("/medication", methods=["POST"])
def medication():
    try:
        req = request.get_json(force=True)
        print("DEBUG req:", req)  # 로그 확인용
        params = req.get("action", {}).get("params", {})

        start_date = params.get("startDate")
        months_raw = params.get("months")

        # months 값 안전 변환 (문자/숫자 다 수용)
        try:
            months = int(str(months_raw).strip())
        except Exception:
            months = 0

        if not start_date or months <= 0:
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [
                        {"simpleText": {"text": f"⚠️ 입력값 오류 (startDate={start_date}, months={months_raw})"}}
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
        print("ERROR:", e)
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": f"⚠️ 서버 오류: {str(e)}"}}
                ]
            }
        })
