import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import List
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

@dataclass
class PcRequest:
    budget: str               # 선택한 예산값 (그대로 문자열)
    main_use: str             # 선택한 용도
    fav_programs: List[str]   # , 기준으로 파싱된 프로그램/게임 리스트
    design: str               # 선택한 디자인
    storage: str              # 선택한 용량
    windows: str              # 포함 여부 (문자열 그대로, 필요하면 나중에 bool로 가공)
    monitor: str              # 해상도 정보

def parse_request(payload: dict) -> PcRequest:
    raw_fav = payload.get("favProgramOrGame", "") or ""
    fav_list = [item.strip() for item in raw_fav.split(",") if item.strip()]

    return PcRequest(
        budget=str(payload.get("budget", "")),
        main_use=str(payload.get("mainUse", "")),
        fav_programs=fav_list,
        design=str(payload.get("design", "")),
        storage=str(payload.get("storage", "")),
        windows=str(payload.get("windows", "")),
        monitor=str(payload.get("monitor", "")),
    )

@app.route('/parse', methods=['POST'])
def parse():
    data = request.json
    pc_request = parse_request(data)
    return jsonify(asdict(pc_request))

def build_pc_prompt(req: PcRequest) -> str:
    fav_list_str = ", ".join(req.fav_programs) if req.fav_programs else "없음"

    prompt = f"""
너는 지금부터 PC 견적 맞춤 도우미 역할을 수행할거야.

예산: "{req.budget}"
주 사용 용도: "{req.main_use}"
자주 사용하는 프로그램/게임: {fav_list_str}
선호 디자인: "{req.design}"
SSD 용량 조건: "{req.storage}" 이상
사용 모니터 해상도: "{req.monitor}"

위 정보를 기반으로 아래 세 가지 견적을 구성해줘:
1. 중고가 방어형 (resale_set)
2. 업그레이드형 (upgrade_set)
3. 가성비/특가형 (performance_set)

각 견적은 다음 JSON 스키마를 반드시 지켜서 출력해야 한다.
설명 문장 없이, JSON만 출력해라.

정확한 출력 형식 예시는 다음과 같다:

{{
  "resale_set": {{
    "option": "중고가 방어형",
    "price": "약 120만원",
    "parts": [
      {{ "category": "CPU", "name": "인텔 i5-13400F" }},
      {{ "category": "메인보드", "name": "ASUS PRIME B760M-A" }},
      {{ "category": "RAM", "name": "삼성 DDR4 16GB" }},
      {{ "category": "그래픽카드", "name": "이엠텍 RTX 4060" }},
      {{ "category": "SSD", "name": "삼성 980 1TB" }},
      {{ "category": "파워", "name": "마이크로닉스 600W" }},
      {{ "category": "케이스", "name": "앱코 베놈" }}
    ]
  }},
  "upgrade_set": {{
    "option": "업그레이드형",
    "price": "약 155만원",
    "parts": [
      {{ "category": "CPU", "name": "AMD 라이젠5 7500F" }},
      {{ "category": "메인보드", "name": "MSI PRO B650M-A" }},
      {{ "category": "RAM", "name": "삼성 DDR5 32GB" }},
      {{ "category": "그래픽카드", "name": "MSI RTX 4060 Ti" }},
      {{ "category": "SSD", "name": "SK하이닉스 P31 1TB" }},
      {{ "category": "파워", "name": "시소닉 850W" }},
      {{ "category": "케이스", "name": "darkFlash DLX21" }}
    ]
  }},
  "performance_set": {{
    "option": "가성비/특가형",
    "price": "약 108만원",
    "parts": [
      {{ "category": "CPU", "name": "인텔 i5-12400F" }},
      {{ "category": "메인보드", "name": "ASRock B660M" }},
      {{ "category": "RAM", "name": "DDR4 16GB" }},
      {{ "category": "그래픽카드", "name": "COLORFUL RTX 4060" }},
      {{ "category": "SSD", "name": "마이크론 1TB" }},
      {{ "category": "파워", "name": "잘만 600W" }},
      {{ "category": "케이스", "name": "DAVEN D6" }}
    ]
  }}
}}

이 예시는 그냥 형식 참고용일 뿐이고,
실제 부품명과 가격은 위 사용자 정보에 맞게 새로 계산해서 채워라.
반드시 JSON 전체를 하나의 객체로 출력하고, 다른 텍스트는 붙이지 마라.
"""
    return prompt.strip()

@app.route("/build-quote", methods=["POST"])
def build_quote():
    data = request.json
    req_obj = parse_request(data)          # PcRequest
    prompt = build_pc_prompt(req_obj)      # 위에서 만든 프롬프트

    resp = client.responses.create(
        model="gpt-4.1-mini",              # 또는 "gpt-4.1"
        # tools=[{"type": "web_search"}],  # RAG + 실시간 검색 쓰고 싶으면 추가
        input=prompt,
    )

    raw_text = resp.output_text

    # LLM이 준 JSON 문자열을 파싱
    try:
        quote_json = json.loads(raw_text)
    except json.JSONDecodeError:
        # 혹시라도 모델이 앞뒤에 설명을 붙였을 때를 대비한 fallback
        # (초기에는 그냥 에러 메시지 반환해도 됨)
        return app.response_class(
            response=json.dumps(
                {
                    "error": "LLM 응답이 유효한 JSON 형식이 아닙니다.",
                    "raw": raw_text,
                },
                ensure_ascii=False,
            ),
            status=500,
            mimetype="application/json; charset=utf-8",
        )

    return app.response_class(
        response=json.dumps(quote_json, ensure_ascii=False),
        status=200,
        mimetype="application/json; charset=utf-8",
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)