"""
벡터 데이터베이스 생성 및 문서 업로드 파일입니다. 컨텍스트 문서 수정 시 실행하면 됩니다.
"""
from openai import OpenAI

client = OpenAI(api_key="")

# 컨텍스트 문서 업로드
file_ids = []
for path in [
    "data/gpu.json",
    "data/price_allocation.json",
    "data/ram.json",
    "data/psu.json",
    "data/compatibility.json",
]:
    with open(path, "rb") as f:
        fobj = client.files.create(file=f, purpose="assistants")
        print(path, "->", fobj.id)
        file_ids.append(fobj.id)

# 2) 벡터 스토어 생성
vs = client.vector_stores.create(
    name="pc-guidelines",
    file_ids=file_ids,
)
print("VECTOR_STORE_ID =", vs.id)
