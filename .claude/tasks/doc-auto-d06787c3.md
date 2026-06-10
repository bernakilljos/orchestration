# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\replace-with-llama.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/replace-with-llama.py b/.claude/scripts/replace-with-llama.py
new file mode 100644
index 0000000..fbce883
--- /dev/null
+++ b/.claude/scripts/replace-with-llama.py
@@ -0,0 +1,90 @@
+"""100 신상품 HTML — LLM 부분 모두 Llama 4 (오픈소스) 로 통일
+
+이유:
+- API 비용 0 (자체 운영)
+- 데이터 외부 유출 X (로컬·on-premise)
+- 한국 도메인 LoRA fine-tune 가능
+- 글로벌 OEM 의존도 ↓
+"""
+import re, os
+
+path = os.path.join(
+    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
+    'outputs', 'itcen', 'html', 'itcen-core-100신상품.html'
+)
+
+# LLM 명칭 → Llama 4 통일 매핑
+LLAMA_BASE = 'Llama 4 (오픈소스·자체 운영)'
+LLAMA_LORA = 'Llama 4 + LoRA fine-tune (한국 도메인 특화)'
+LLAMA_REASON = 'Llama 4 + Reasoning 모듈 (자체 운영)'
+LLAMA_LONG = 'Llama 4 Scout (1M context·자체 운영)'
+LLAMA_VISION = 'Llama 4 Multimodal (Vision)'
+LLAMA_VOICE = 'Llama 4 + 음성 모듈 (자체 운영)'
+LLAMA_AGENT = 'Llama 4 + Agentic 프레임워크 (자체 운영)'
+
+REPLACEMENTS = [
+    # Reasoning 모델
+    ('o3 API 또는 Claude Extended Thinking 활용', LLAMA_REASON),
+    ('o3 API', LLAMA_REASON),
+    ('Claude Extended Thinking API', LLAMA_REASON),
+    ('Claude Extended Thinking', LLAMA_REASON),
+
+    # Claude 일반
+    ('Claude Opus 4.7 (1M context) API', LLAMA_LONG),
+    ('Claude Opus 4.7 (1M context)', LLAMA_LONG),
+    ('Claude 1M context', LLAMA_LONG),
+    ('Claude·GPT 생성형', LLAMA_BASE),
+    ('Claude Computer Use', f'{LLAMA_AGENT}·Computer Use'),
+    ('Claude·Gemini·Haiku 다중 합의 패턴', 'Llama 4 ×3 다중 합의 (자체 운영)'),
+    ('Codex+Gemini+Haiku 다중 합의 패턴', 'Llama 4 ×3 다중 합의 (자체 운영)'),
+    ('Haiku-validator hook', 'Llama 4 ×2 검증 hook (자체)'),
+    ('Sonnet 1차 → Haiku 2차', 'Llama 4 1차 → Llama 4 2차 검증'),
+
+    # GPT
+    ('GPT-4o/Claude 4 Voice API', LLAMA_VOICE),
+    ('GPT-4 Vision/Claude Vision', LLAMA_VISION),
+    ('GPT-4o·Gemini 2.5 멀티모달', f'{LLAMA_VISION}·Multimodal'),
+    ('GPT-4o 또는 Gemini 2.5 멀티모달', f'{LLAMA_VISION}·Multimodal'),
+    ('GPT-4o', LLAMA_VISION),
+
+    # Llama 3 (기존) → Llama 4
+    ('Llama 3·Llama 4 base + LoRA fine-tune', LLAMA_LORA),
+    ('Llama 3 + 한국 금융 데이터 LoRA', LLAMA_LORA),
+    ('Llama 3', 'Llama 4'),
+
+    # 도메인 LLM
+    ('LangChain + 공급망 데이터', f'{LLAMA_BASE} + 공급망 데이터'),
+    ('Llama 4 base + 한국 금융·회계 LoRA', LLAMA_LORA),
+    ('Llama 4 base + LoRA', LLAMA_LORA),
+
+    # Hume API → 자체 모델
+    ('Hume AI EVI 3 API 라이선스', f'{LLAMA_BASE} + 감정인식 LoRA (자체)'),
+    ('Hume EVI + 매장 CCTV', f'{LLAMA_BASE} + 감정 모듈 + 매장 CCTV'),
+    ('Hume + 자체 분류기 결합', f'{LLAMA_BASE} + 자체 감정 분류기'),
+    ('Hume API', f'{LLAMA_BASE} 감정 모듈'),
+
+    # MoE 멀티모달
+    ('Gemini 2.5', 'Llama 4 Behemoth (MoE)'),
+]
+
+with open(path, 'r', encoding='utf-8') as f:
+    html = f.read()
+
+count = 0
+for old, new in REPLACEMENTS:
+    n = html.count(old)
+    if n > 0:
+        html = html.replace(old, new)
+        count += n
+
+# 헤더 메시지에 Llama 표기 추가
+old_msg = '<strong>📌 형식:</strong> 각 신상품 = <strong>접목 신기술 + 무엇을 새로 할지 + 대상 + 매출 잠재</strong>.<br>\n    행동위험분석 외 영역 위주. ITCEN CORE 자사 패키지 위에 AI 모듈 추가 → 기존 1위 채널 그대로 활용.'
+new_msg = '<strong>📌 형식:</strong> 각 신상품 = <strong>접목 신기술 + 무엇 + 어떻게 + 대상 + 매출</strong>.<br>\n    <strong style="color:#FFC107">⭐ LLM 부분 모두 Llama 4 (오픈소스·자체 운영) 통일</strong> — API 비용 0, 데이터 유출 X, 한국 도메인 LoRA fine-tune 가능.<br>\n    행동위험분석 외 영역 위주. ITCEN CORE 자사 패키지 위에 Llama 4 모듈 추가 → 기존 1위 채널 추가판매.'
+html = html.replace(old_msg, new_msg)
+
+with open(path, 'w', encoding='utf-8') as f:
+    f.write(html)
+
+llama_count = html.count('Llama 4')
+print(f'Total replacements: {count}')
+print(f'Total Llama 4 mentions: {llama_count}')
```

## Action
1. 변경된 public API 추출 (함수·클래스·exports)
2. CHANGELOG.md `[Unreleased]` 섹션에 entry 추가:
   - Added/Changed/Fixed/Removed/Security 분류
3. README.md 의 API 섹션 갱신 (있을 시)
4. docs/api/<module>.md 갱신 (있을 시)

## Constraints
- 기존 entry 덮어쓰기 X (append)
- 자동 commit X (사용자 review 대기)
- 내부 helper 변경 skip (public API 만)
