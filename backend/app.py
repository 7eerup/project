import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import List
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv
from flask_openapi3 import OpenAPI, Info, Tag
from pydantic import BaseModel, Field

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

info = Info(
    title="Maknawa API",
    version="1.0.0"
)

app = OpenAPI(__name__, info=info)
CORS(app)

client = OpenAI(api_key=API_KEY)

quote_tag = Tag(name="PC Quote", description="PC 견적 생성 관련 API")

# ------------------------------------------------------------
# 함수 작성
# ------------------------------------------------------------


@dataclass
class PcRequest:
    budget: str               # 선택한 예산값 (그대로 문자열)
    mainUse: str             # 선택한 용도
    favProgramOrGame: List[str]   # , 기준으로 파싱된 프로그램/게임 리스트
    design: str               # 선택한 디자인
    storage: str              # 선택한 용량
    monitor: str              # 해상도 정보

def parse_request(payload: dict) -> PcRequest:
    raw_fav = payload.get("favProgramOrGame", "") or ""
    fav_list = [item.strip() for item in raw_fav.split(",") if item.strip()]

    return PcRequest(
        budget=str(payload.get("budget", "")),
        mainUse=str(payload.get("mainUse", "")),
        favProgramOrGame=fav_list,
        design=str(payload.get("design", "")),
        storage=str(payload.get("storage", "")),
        monitor=str(payload.get("monitor", "")),
    )

def build_prompt(req: PcRequest) -> str:
    fav_list_str = ", ".join(req.favProgramOrGame) if req.favProgramOrGame else "없음"

    return f"""
너는 PC 견적 맞춤 도우미다.

[사용자 입력]
- 예산: {req.budget}
- 주 사용 용도: {req.mainUse}
- 자주 사용하는 프로그램/게임: {fav_list_str}
- 선호 디자인: {req.design}
- SSD 용량 조건: {req.storage} 이상
- 모니터 해상도: {req.monitor}

[참고 자료]
- 업로드된 JSON 가이드라인 문서들:
  - gpu.json: 해상도/용도별 GPU 스펙 기준
  - ram.json: 최소 용량, 16GB/32GB/64GB 기준, 멀티 채널 규칙
  - psu.json: 총 소비전력의 2배, 상위 칩셋일수록 여유, 대기업 브랜드 우선
  - compatibility.json: 소켓/DDR/PCIe 호환성
  - price_allocation.json: 예산 분배, 예산 부족 시 raise_budget 규칙 등

[규칙]
0. 
- 절대로 자연어 설명, 사과문, 링크를 JSON 앞뒤에 쓰지 마라.
- 출력은 아래 JSON 객체 하나만 반환하라.
- JSON 밖에 다른 텍스트(문장, 줄바꿈, 주석, 출처 링크 등)를 절대로 포함하지 마라.
1. file_search 도구로 위 가이드라인들을 검색해, 현재 사용자 조건에 맞는 규칙을 찾아라.
2. price_allocation에서 action: "raise_budget" 규칙이 발견되면:
   - 입력 예산이 부족하다는 뜻이다.
   - 해당 규칙의 설명/최소 예산을 참고해, 내부적으로 예산을 상향 조정한 뒤 그 기준으로 견적을 구성하라.
3. web_search 도구는 GPU/CPU/SSD의 세대 및 대략적인 가격대를 참고할 때만 사용하라.
4. RAM은 최소 16GB, 스트리밍/영상 편집/고사양 작업이면 32GB 이상, 게이밍은 32GB까지만 추천하라.
5. 파워는 총 소비전력의 2배 이상, 고급 칩셋/고성능 GPU일수록 여유있게, 마이크로닉스/시소닉 등의 대기업 파워를 우선 선택하라.
6. 호환성이 맞지 않는 조합(DDR4 보드 + DDR5 메모리, 소켓 불일치 등)은 절대 추천하지 말고, 가이드라인에 맞는 조합으로 수정하라.

[출력 형식]
다음 JSON 스키마를 반드시 지켜라. 설명문 없이 JSON 객체 한 개만 출력하라.

{{
  "resale_set": {{
    "option": "중고가 방어형",
    "price": "약 XXX만원",
    "parts": [
      {{ "category": "CPU", "name": "..." }},
      {{ "category": "메인보드", "name": "..." }},
      {{ "category": "RAM", "name": "..." }},
      {{ "category": "그래픽카드", "name": "..." }},
      {{ "category": "SSD", "name": "..." }},
      {{ "category": "파워", "name": "..." }},
      {{ "category": "케이스", "name": "..." }}
    ]
  }},
  "upgrade_set": {{
    "option": "업그레이드형",
    "price": "약 XXX만원",
    "parts": [ ... 동일 구조 ... ]
  }},
  "performance_set": {{
    "option": "가성비/특가형",
    "price": "약 XXX만원",
    "parts": [ ... 동일 구조 ... ]
  }},
}}
""".strip()

def generate_quote(req: PcRequest) -> dict:
    prompt = build_prompt(req)

    resp = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [VECTOR_STORE_ID],
            },
            {
                "type": "web_search",
            },
        ],
    )

    # 2.x: output 안에 text / tool_call 섞여 있을 수 있음
    raw = None
    for item in resp.output:
        # 텍스트 출력인 경우
        if getattr(item, "type", None) == "message":
            # message.content 안에 text 조각들이 들어있음
            for c in item.content:
                if c.type == "output_text":
                    raw = c.text
                    break
        # 일부 버전에서는 바로 output_text 타입으로 나오는 경우도 있음
        elif getattr(item, "type", None) == "output_text":
            raw = item.text

        if raw is not None:
            break

    if raw is None:
        raise ValueError(f"텍스트 출력이 없고, tool 호출만 있었습니다: {resp}")

    import json
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM 응답이 유효한 JSON 형식이 아닙니다: {raw}")

# ------------------------------------------------------------
# API, API 명세 작성 코드
# ------------------------------------------------------------
class PcQuoteRequest(BaseModel):
    """요청 스키마 (문서화 전용)"""
    budget: str = Field(..., json_schema_extra={"example": "120만원 ~ 180만원"})
    mainUse: str = Field(..., json_schema_extra={"example": "게임"})
    favProgramOrGame: str = Field(default="", json_schema_extra={"example": "오버워치, 로스트아크"})
    design: str = Field(..., json_schema_extra={"example": "블랙 & 심플"})
    storage: str = Field(..., json_schema_extra={"example": "1TB"})
    # windows: str = Field(..., json_schema_extra={"example": "포함"})
    monitor: str = Field(..., json_schema_extra={"example": "QHD"})

# @app.post('/parse', tags=[quote_tag], summary = "json 파싱")
# def parse():
#     """json 파싱 및 서비스 확장 대비 용"""
#     data = request.json
#     pc_request = parse_request(data)
#     return jsonify(asdict(pc_request))

@app.post('/build-quote', tags=[quote_tag], summary="PC 견적 생성")
def build_quote(body: PcQuoteRequest):
    """사용자 입력 + 컨텍스트 문서 기반 현 시점 추천할 수 있는 PC 견적 생성"""
    data = request.json
    req_obj = parse_request(data)

    try:
        quote_json = generate_quote(req_obj)
        status = 200 #성공
        body = quote_json
    except Exception as e:
        status = 500 #서버 오류
        body = {"error": str(e)}

    return app.response_class(
        response=json.dumps(body, ensure_ascii=False),
        status=status,
        mimetype="application/json; charset=utf-8",
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)