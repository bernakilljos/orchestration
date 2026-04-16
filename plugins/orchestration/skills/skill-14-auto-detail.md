# SKILL-14 — Auto Detail (Request Auto-Expansion)

## Purpose
When the user gives a short/vague request (e.g., "RMS architecture diagram"),
automatically collect project context and expand it into a detailed, actionable instruction
that can be used as a task-instruction.md or direct execution guide.

## Trigger Conditions
- User requests a diagram, architecture, or design document with insufficient detail
- Keywords: "설계도", "아키텍처", "다이어그램", "구조도", "ERD", "시스템 구성도", "플로우차트", "시퀀스", "배포 구성"
- The request lacks specifics like ports, IPs, tech stack, DB names, etc.
- User says "그려줘", "만들어줘", "작성해줘" for any design/documentation artifact

## NOT Triggered When
- User already provided full detail (ports, stack, DB, server info all present)
- Pure code implementation request (no diagram/doc needed)

---

## Execution Order

### 1. Detect Request Type

Classify the request into one of these categories:

| Type | Examples | Output Format |
|------|----------|---------------|
| system-architecture | "전체 아키텍처", "시스템 구성도" | Infra + App + DB + Network diagram spec |
| erd | "ERD", "DB 설계", "테이블 구조" | Entity list + Relations + Indexes |
| api-spec | "API 설계", "엔드포인트 정리" | Endpoint list + Request/Response + Auth |
| flow | "플로우차트", "시퀀스 다이어그램", "흐름도" | Step-by-step flow + Actors + Conditions |
| deploy | "배포 구성도", "인프라 구성" | Server + CI/CD + Reverse proxy + Ports |
| screen-map | "화면 설계", "화면 목록", "와이어프레임" | Page list + Navigation + Components |
| presentation | "PPT", "발표자료", "프레젠테이션", "슬라이드" | Slide structure + Content per slide + Visual style |
| general-doc | "설계 문서", "기술 명세" | Combined spec document |

### 2. Auto-Collect Project Context

Read the following sources (skip if not found):

```
Priority 1 — Config files (always check):
  .claude/deploy-config.env          → Server IP, port, PM2 name, deploy env
  package.json                       → Frontend stack, dependencies, scripts, ports
  pom.xml / build.gradle             → Backend stack, Java version, dependencies
  vue.config.js / vite.config.*      → Frontend port, proxy settings
  application.yml / application.properties → Backend port, DB connection, profiles
  nginx.conf / nginx/*.conf          → Reverse proxy rules, SSL, upstream
  docker-compose.yml                 → Container ports, service names, networks
  Dockerfile                         → Base image, exposed ports

Priority 2 — Source structure (check for context):
  src/ structure                     → Frontend page/component list
  src/main/java/ structure           → Backend package structure
  src/router/ or routes.*            → Route definitions
  src/store/ or store.*              → State management structure
  src/api/ or api.*                  → API endpoint patterns

Priority 3 — Existing docs (reuse if available):
  docs/research-report.md            → Previously analyzed stack info
  docs/architecture-decision.md      → Previous design decisions
  docs/design-decision.md            → Design patterns in use
  README.md                          → Project overview
  CLAUDE.md                          → Dev rules and constraints
```

### 3. Build Context Summary

Compile discovered information into structured context:

```markdown
## Auto-Detected Project Context

### Tech Stack
- Frontend: [자동 감지됨] (Port: [XXXX])
- Backend: [Spring Boot/Node/...] (Port: [XXXX])
- DB: [MySQL/MSSQL/Oracle] (Name: [db_name], Port: [XXXX])
- Server: [IP or hostname]
- Reverse Proxy: [Nginx/Apache/None] (Port: [80/443])

### Key Dependencies
- [dependency list relevant to the request]

### Existing Patterns
- [patterns found in source that relate to the request]

### Constraints (from CLAUDE.md)
- [프로젝트 CLAUDE.md에서 자동 감지된 규칙들]
```

### 4. Expand to Detailed Instruction

Transform the short request into a detailed instruction using the collected context.

**Template per type:**

#### system-architecture
```markdown
# [Project Name] System Architecture Diagram

## Diagram Requirements
- Style: [hand-drawn sketch / formal / flowchart] (default: hand-drawn sketch style)
- Tool: [Figma / Canva / Mermaid / draw.io] (auto-select based on available MCP)

## Components to Include
1. Client Layer
   - Browser → [Frontend framework] (Port: [XXXX])

2. Web Server Layer
   - [Nginx/Apache] (Port: [80/443])
   - Reverse proxy rules: [detected proxy config]

3. Application Layer
   - Frontend: [framework] at [server]:[port]
   - Backend: [framework] at [server]:[port]
   - [PM2/systemd/docker] process management

4. Data Layer
   - [DB type]: [db_name] at [server]:[port]
   - [Redis/cache if detected]
   - [File storage if detected]

5. External Services
   - [APIs, OAuth, CDN, etc. if detected]

## Network Flow
  Client → Nginx(:80/:443) → Frontend(:XXXX) 
                            → /api/* → Backend(:XXXX) → DB(:XXXX)

## Visual Requirements
- Show port numbers on all connections
- Show protocol (HTTP/HTTPS/WebSocket) on arrows
- Include server IP/hostname labels
- Color coding: Frontend=blue, Backend=green, DB=orange, Infra=gray
```

#### erd
```markdown
# [Project Name] ERD

## Tables to Include
[Auto-detected from entity classes, migration files, or SQL scripts]

## Relationships
[FK references detected from JPA annotations or schema files]

## Requirements
- Show PK/FK indicators
- Show column types
- Show indexes
- Notation: [Crow's foot / Chen / UML]
```

#### presentation
```markdown
# [Project Name] — [Subject] Presentation

## Presentation Info
- Tool: Gamma MCP (auto-generate) / Canva MCP / Manual PPT
- Total slides: [auto-calculate based on content scope]
- Style: [professional / minimal / hand-drawn / corporate] (default: professional)
- Audience: [detected or ask: developers / management / client / internal]

## Slide Structure

### Slide 1 — Title
- Title: [Project Name] [Subject]
- Subtitle: [date, team/company name]

### Slide 2 — Overview / Agenda
- What this presentation covers (3-5 bullet points)

### Slide 3~N — Content Slides (auto-generated per topic)
[Each slide auto-populated with detected project info]

For system-architecture presentations:
  - Slide: Tech Stack Overview (Frontend/Backend/DB with versions)
  - Slide: System Architecture Diagram (component layout with ports/IPs)
  - Slide: Network Flow (Client → Nginx → App → DB)
  - Slide: Deployment Configuration (server, PM2, CI/CD)
  - Slide: Database Schema (key tables/relationships)
  - Slide: API Structure (major endpoints grouped by domain)
  - Slide: Security & Auth (if detected)
  - Slide: Monitoring & Logging (if detected)

For project-status presentations:
  - Slide: Completed Features (from git log / task history)
  - Slide: In Progress (from current tasks)
  - Slide: Upcoming (from backlog / plan)
  - Slide: Issues & Risks
  - Slide: Timeline / Roadmap

### Slide N+1 — Summary / Next Steps
### Slide N+2 — Q&A

## Visual Requirements
- Diagrams: include architecture/flow diagrams in relevant slides
- Color coding: match project's design system or default scheme
- Charts: use data from project metrics if available
- Icons: use relevant tech stack logos/icons
```

#### deploy
```markdown
# [Project Name] Deployment Architecture

## Server Configuration
- Host: [IP] ([cloud provider if known])
- OS: [if detectable]
- Nginx: [config summary]

## Service Ports
| Service | Port | Process Manager |
|---------|------|----------------|
| Nginx | 80/443 | systemd |
| Frontend | [XXXX] | [PM2/serve/nginx static] |
| Backend | [XXXX] | [java -jar/PM2/docker] |
| DB | [XXXX] | [systemd/docker] |

## CI/CD Pipeline
[Jenkins/GitHub Actions/etc. if detected]

## SSL/Domain
[If detected from nginx config]
```

### 5. Present and Confirm

Output the expanded instruction to the user in this format:

```
[Auto-Detail] Request expanded with project context:

---
[Expanded detailed instruction here]
---

Shall I proceed with:
  1. Generate PPT via Gamma (presentation)
  2. Generate via Canva (graphic/document)
  3. Generate via Figma (UI design)
  4. Generate Mermaid diagram (code-based)
  5. Write as task-instruction.md for Codex/Gemini
  6. Modify details first

Available output formats:
  - PPT/Slide    → Gamma MCP (auto-generate presentation)
  - DOC/Page     → Gamma MCP (document mode) or Canva MCP
  - Diagram      → Figma MCP or Mermaid code
  - Image/Banner → Canva MCP or DALL-E
  - Markdown     → Direct output to docs/
```

### 6. Execute on Confirmation

Based on user's choice, route to appropriate tool:

| Choice | Tool | How |
|--------|------|-----|
| PPT/Slide | Gamma MCP | `generate` with type=presentation, auto-fill slide content from expanded spec |
| DOC/Page | Gamma MCP | `generate` with type=document or webpage |
| Canva Graphic | Canva MCP | `generate-design` → `export-design` |
| Figma Design | Figma MCP | `create_new_file` or `generate_diagram` |
| Mermaid | Direct | Generate mermaid code block, optionally render |
| task-instruction.md | AGENT-01 | Team Lead flow for Codex/Gemini execution |

#### Gamma PPT Generation Flow
```
1. Build prompt from expanded spec:
   - Title, subtitle, audience
   - Slide-by-slide content outline
   - Include project-specific data (ports, IPs, stack, DB schema)
   - Visual style preference

2. Call Gamma MCP:
   generate(
     topic: "[Project] [Subject]",
     audience: "[detected]",
     style: "[selected]",
     num_cards: [auto-calculated],
     additional_instructions: "[full expanded spec as context]"
   )

3. Check status with get_generation_status
4. Return Gamma URL to user for final editing
```

#### Gamma DOC Generation Flow
```
1. Build prompt from expanded spec:
   - Document structure (sections, subsections)
   - Technical content with detected project values filled in
   - Diagrams described for auto-rendering

2. Call Gamma MCP:
   generate(
     topic: "[Subject] Technical Document",
     output_type: "document",
     additional_instructions: "[full expanded spec]"
   )

3. Return Gamma URL for editing
```

---

## Expansion Rules

1. **Always fill in detected values** — never leave [placeholder] if the value was found
2. **Mark unknown values clearly** — use `[NOT DETECTED - please specify]` 
3. **Respect CLAUDE.md constraints** — include relevant rules in the instruction
4. **Default to hand-drawn sketch style** unless user specifies otherwise
5. **Include ALL detected ports/IPs** — don't omit even if they seem obvious
6. **Cross-reference deploy-config.env** — this is the primary source of truth for infra info
7. **If no config files found** — ask user for minimum required info before expanding

## Minimum Required Info (ask if not detectable)

| Request Type | Must Know |
|-------------|-----------|
| system-architecture | Frontend stack, Backend stack, DB type, Server IP |
| erd | DB type, Main entity names |
| api-spec | Backend framework, Auth method |
| deploy | Server IP, Port assignments |
| flow | Feature name, Actors involved |

---

## Output
- Expanded instruction displayed in conversation
- Optionally saved to `docs/design-request-[name].md`
- If task-instruction.md route chosen → `.claude/tasks/task-instruction.md`

## Extension Points
- Add new request types by extending the type table in Step 1
- Add new config sources by extending the Priority list in Step 2
- Connect to new diagram tools by adding options in Step 5
