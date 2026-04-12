# SKILL-12 — Domain Auto-Detection

## Purpose

Automatically detect project technology stack and domain on first run (HOOK-00 init) to configure appropriate tools, lint rules, test frameworks, and deployment strategies.

Inspired by claude-buddy.dev's domain system, adapted for the multi-AI orchestration kit.

---

## Detection Method

Scan project root for indicator files. Each match adds confidence points to the corresponding domain. A domain is considered "detected" when its cumulative score meets or exceeds the threshold.

---

## Scoring Rules

### Frontend Domains

#### Vue 2.x (priority: 80)

| Indicator | Points |
|-----------|--------|
| package.json contains `"vue": "^2"` or `"vue": "~2"` | 90 |
| `.vue` files exist in project | 30 |
| `nuxt.config.js` exists | 20 |
| `vue.config.js` exists | 20 |

**Threshold: 60**

#### Vue 3.x (priority: 80)

| Indicator | Points |
|-----------|--------|
| package.json contains `"vue": "^3"` | 90 |
| `vite.config.ts` exists | 20 |

**Threshold: 60**

#### React (priority: 70)

| Indicator | Points |
|-----------|--------|
| package.json contains `"react"` | 90 |
| `.jsx` or `.tsx` files exist in project | 30 |
| `next.config.js` exists | 20 |

**Threshold: 60**

#### Vanilla JS / Node (priority: 30)

| Indicator | Points |
|-----------|--------|
| package.json exists but no framework dependency detected | 50 |
| `.js` files present in `src/` | 20 |

**Threshold: 60**

---

### Backend Domains

#### Spring Boot (priority: 80)

| Indicator | Points |
|-----------|--------|
| `pom.xml` contains `spring-boot` | 90 |
| `build.gradle` contains `spring-boot` | 90 |
| `src/main/java` directory exists | 30 |
| `application.yml` or `application.properties` exists | 20 |

**Threshold: 60**

#### Node.js Express (priority: 60)

| Indicator | Points |
|-----------|--------|
| package.json contains `"express"` | 90 |

**Threshold: 60**

#### Python Django / Flask (priority: 60)

| Indicator | Points |
|-----------|--------|
| `requirements.txt` contains `django` or `flask` | 90 |
| `manage.py` exists | 30 |

**Threshold: 60**

---

### Database Domains

Databases are detected from connection strings, environment files, or framework configuration:

| Database   | Detection Pattern |
|------------|-------------------|
| MSSQL      | Config contains `sqlserver` or `mssql` |
| MySQL      | Config contains `mysql` |
| Oracle     | Config contains `oracle` |
| PostgreSQL | Config contains `postgres` or `pg` |

Scanned files: `application.yml`, `application.properties`, `.env`, `config/*.js`, `database.yml`, `settings.py`, `knexfile.js`

---

## Detection Algorithm

```
1. Read project root file listing
2. For each domain definition:
   a. Check each indicator against the project
   b. Sum matched indicator points
   c. If sum >= threshold, mark domain as detected with confidence = sum
3. If multiple domains in the same category match (e.g., Vue 2 and Vue 3):
   a. Select the one with higher confidence
   b. If tied, select the one with higher priority
4. Compile results into domain profile
```

---

## Detection Output

Save result to `.claude/context-cache/domain-profile.md`:

```markdown
# Domain Profile (auto-detected)
Generated: YYYY-MM-DD HH:mm

## Stack
- Frontend: Vue 2.x (confidence: 90)
- Backend: Spring Boot 2.x (confidence: 110)
- Database: MSSQL (detected from application.yml)
- Build: Maven / npm
- Test: Jest + JUnit

## Applicable Rules
- No optional chaining (?.) — Vue 2 requirement
- ES5/ES2015 syntax — Node compatibility
- Java 8-11 — Spring Boot 2.x constraint
- Single-line annotations — project convention

## Recommended Tools
- Lint: ESLint (frontend), Checkstyle (backend)
- Test: @vue/test-utils + Jest, JUnit + Mockito
- Build: npm run build, mvnw package
- Deploy: deploy.bat → EC2
```

---

## When to Run

| Trigger | Condition |
|---------|-----------|
| HOOK-00 init | Automatically on first install (domain-profile.md does not exist) |
| User request | User says "re-detect stack" or "detect domain" |
| Missing profile | domain-profile.md is absent when a pipeline step needs it |

---

## Integration Points

- **HOOK-00 init.bat**: Calls SKILL-12 after folder creation. Detection result feeds into all subsequent pipeline steps.
- **SKILL-02 implement**: Reads domain profile to apply correct syntax rules (e.g., no optional chaining for Vue 2).
- **SKILL-06 test.bat**: Selects test runner based on detected stack (Jest, JUnit, pytest).
- **HOOK-02 quality-gate.bat**: Uses domain profile to pick the right linter and build command.
- **SKILL-05 deploy.bat**: Chooses deployment strategy based on detected backend/infra.

---

## Fallback Behavior

If no domain matches the threshold:

1. Set profile to `default` with generic rules (no framework-specific constraints).
2. Claude asks the user to confirm or manually specify the stack.
3. User response is saved to domain-profile.md with `(manual)` tag.

```markdown
## Stack
- Frontend: unknown (manual confirmation needed)
- Backend: unknown (manual confirmation needed)
```

---

## Re-detection

When re-detection is triggered:

1. Rename existing `domain-profile.md` to `domain-profile.md.bak`
2. Run full detection scan
3. Diff old vs new profile
4. If changes found, notify user:
   ```
   [DOMAIN] Stack change detected:
     Frontend: Vue 2.x → Vue 3.x
     Confirm? [Y/N]
   ```
5. On confirmation, apply new profile. On rejection, restore backup.
