# SKILL-08 — Design (Design Asset Generation)

## Purpose
Reference design references before UI implementation and produce assets using Canva / DALL-E / video generation AI.
Lock layouts to prevent AI from arbitrarily changing them.

## Trigger Conditions
- New UI page/component implementation request
- Banner, image, video assets needed
- Design system reference required

---

## Execution Order

### 1. Load Design Reference
```
Check docs/design-system/ or ai_design_reference_system/ folder
  - layouts/      : Page layouts (do not modify)
  - components/   : Reusable component definitions
  - patterns/     : Screen composition patterns
  - references/   : External design inputs (images, URLs)
  - hooks/        : Layout lock rules
```

### 2. Verify Layout Lock (Delegated to HOOK-07)
- `layouts/` files → absolutely do not modify
- `components/` files → do not change structure, only add business logic
- If existing pattern exists, copy and reuse

### 3. Canva Asset Generation (Banners/Graphics/Social)
```
Tool: Canva MCP (mcp__claude_ai_Canva)

Procedure:
  1. Generate draft with generate-design
  2. Download PNG/PDF with export-design
  3. Save to docs/screens/

Use cases: Banners, thumbnails, social posts, presentations
```

### 4. DALL-E Image Generation (Custom Images)
```
Tool: OpenAI Images API

Procedure:
  gemini --yolo -p "Generate an image prompt for: [description]. Output only the English prompt."
  → Call OpenAI API with the generated prompt:
  curl https://api.openai.com/v1/images/generations \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"dall-e-3","prompt":"[PROMPT]","size":"1024x1024","n":1}'
  → Save URL to docs/screens/

Use cases: Illustrations, UI backgrounds, icon drafts
```

### 5. Figma Integration (UI Design)
```
Tool: Figma MCP (mcp__claude_ai_Figma)

Procedure:
  - If Figma URL exists: extract code with get_design_context
  - If not: capture reference with get_screenshot
  - Implement referencing the extracted component code

Use cases: Precision UI components, design system token extraction
```

### 6. Video Generation (Video Assets)
```
Tool: Sora API / Runway API / Pika API (selected via environment variable)

Procedure:
  gemini --yolo -p "Write a short video prompt for: [description]. Max 200 chars."
  → Call selected API with the generated prompt
  → Record result URL in docs/screens/videos/

Environment variables:
  VIDEO_PROVIDER=sora|runway|pika
  SORA_API_KEY=...
  RUNWAY_API_KEY=...
  PIKA_API_KEY=...

Use cases: Intro videos, tutorial clips, social short-form
```

---

## Output
- `docs/screens/[name].png` — Canva/DALL-E images
- `docs/screens/videos/[name].mp4` — Video assets
- `docs/design-decision.md` — Record of patterns used and layout decisions

## Prohibited Rules
- Do not modify layouts/ files
- Do not change components/ structure
- Do not hardcode image/video API keys (use process.env)
