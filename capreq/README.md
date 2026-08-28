# capreq — Capability Request (로컬 LLM 라우터)

사용자 자연어 → **등록된 능력(capability) 코드**로 옮기는 **독립 모듈**.  
실행·게이트·증적은 백엔드(예: CapNet)가 하고, capreq는 **찾아 고르는 일**만 한다.

> CapNet Core의 일부가 **아니다.** 연결·해제 가능. 다른 프로젝트는 `CatalogSource` /
> `ExecutionBackend` 어댑터만 구현하면 붙는다.

## 모델 선택: Qwen2.5 (기본) · Gemma는 대안

| | Qwen2.5 (기본) | Gemma 2 |
|--|----------------|---------|
| 한국어 | 다국어(한·중·영 등) 실사용 강함 | 가능하나 라우팅에 덜 유리한 편 |
| JSON·구조화 출력 | 공식 강점 (라우팅에 적합) | 가능 |
| Ollama | `qwen2.5:3b` / `:7b` | `gemma2:2b` / `:9b` |

**기본값 `qwen2.5:3b`**. VRAM 여유 있으면 `qwen2.5:7b`.

```bash
ollama pull qwen2.5:3b
# 대안: ollama pull gemma2:2b  후  CAPREQ_OLLAMA_MODEL=gemma2:2b
```

## 설치

```bash
cd capreq
python -m pip install -e .
# 웹 UI: python -m pip install -e ".[server]"
```

## Gemma 일반 대화 (테스트용 · CapNet 없음)

능력 라우팅과 **별개**. 대화만 되는지 볼 때:

```bash
ollama pull gemma2:2b
cd capreq
python -m pip install -e ".[server]"
python -m capreq gemma --port 8091
```

브라우저: http://127.0.0.1:8091/  
모델 바꾸기: `python -m capreq gemma --model gemma2:9b` 또는 `CAPREQ_GEMMA_MODEL=...`

## 사용

```bash
# 라우팅만 (실행 안 함) — Core :8000
python -m capreq route "이 사진 분류해줘" --core http://127.0.0.1:8000

# 대화형 CLI
python -m capreq chat --core http://127.0.0.1:8000

# 웹 챗봇
python -m capreq serve --core http://127.0.0.1:8000 --port 8090

# 웹 챗봇 (파일 첨부 → Core 중개 업로드 → Task)
python -m capreq serve --core http://127.0.0.1:8000 --port 8090
# 브라우저 http://127.0.0.1:8090/ — + 버튼·드래그앤드롭으로 파일 첨부
# 첨부 + 「실행」체크 → POST /v1/inputs → /v1/tasks { inputId } (D22 · D8′)
# Core 인증 필요 시: CAPREQ_API_KEY=ck_... (CapNet-Key 스킴)

# CapNet Task까지 (allowlist 데모 · Agent 미지정)
python -m capreq route "이미지 분류해줘" --core http://127.0.0.1:8000 --execute \
  --dataset eurosat-rgb --case ic1-0001
```

능력이 해석됐으나 백엔드가 못 돌리면 **해석은 남기고** 실행 실패를 명시한다.

## 환경 변수

| 변수 | 기본 | 의미 |
|------|------|------|
| `CAPREQ_OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama |
| `CAPREQ_OLLAMA_MODEL` | `qwen2.5:3b` | 모델 |
| `CAPREQ_CORE_URL` | `http://127.0.0.1:8000` | CapNet Core |
| `CAPREQ_MIN_CONFIDENCE` | `0.45` | 미만이면 unknown |
| `CAPREQ_API_KEY` | (없음) | Core `CapNet-Key` 토큰 |

## 다른 프로젝트

```python
from capreq.adapters.base import CapabilityInfo
from capreq.router import CapabilityRouter
from capreq.ollama import OllamaClient

class MyCatalog:
    def list_capabilities(self) -> list[CapabilityInfo]:
        return [CapabilityInfo(code="foo.bar", version=1, name="Foo", description="...")]

router = CapabilityRouter(catalog=MyCatalog(), llm=OllamaClient())
print(router.route("foobar 해줘"))
```

## 경계

- 자유 업로드 창구 아님. CapNet 연결 시 dataset/case allowlist만.
- 목록에 없는 `code`는 거절 (allowlist).
- CapNet = 실행·통제·증적 / capreq = 말로 능력 선택.
