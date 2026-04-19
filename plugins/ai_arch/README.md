# ai_arch — AI 모델 아키텍처 선택·라우팅

> **Prefix**: `ai_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 3

## ⚠️ 현재 상태
**spec-only** — 스펙. 실구현은 플랫폼에서.

## 📖 개요
LLM 외 **8가지 AI 아키텍처**를 작업 특성 기준으로 선택·라우팅.

| 아키텍처 | 전체 이름 | 용도 |
|---|---|---|
| **LCM** | Large Concept Models | 문장 단위 의미 (Meta SONAR) |
| **VLM** | Vision-Language | 이미지+텍스트 멀티모달 |
| **SLM** | Small Language Models | 엣지·로컬 (Ollama) |
| **MoE** | Mixture of Experts | 선택적 전문가 활성화 |
| **MLM** | Masked Language | 양방향 컨텍스트 (BERT 계열) |
| **LAM** | Large Action | 시스템 조작·도구 사용 |
| **SAM** | Segment Anything | 픽셀 세그먼트 (비전) |
| **LLM** | Large Language | 텍스트 추론 (GPT·Claude·Gemini) |

## 📋 커맨드

- `/arch-suggest` ⭐ 기본 — 작업 설명 → 최적 아키텍처 추천
- `/arch-compare` — 2개 이상 비교표
- `/arch-list` — 전체 목록 + 사용 사례

## 🧠 스킬

- `skill-arch-selector` — 작업 특성 ↔ 아키텍처 매핑 로직

## 🔗 의존성

- **플러그인**: `exec_orch` (route_dispatch 와 연동 예정)

## 참조

- 출처: `docs/upgrade-analysis-2026-04-19.md` § Reel 2 (8 AI Architectures)
- 라우팅 v3 연계: `plugins/exec_orch/skills/route_dispatch.md` (미래 업데이트)
