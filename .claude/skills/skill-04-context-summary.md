# SKILL-04 — Context Summary (Context Compression)

## Purpose
Summarize files over 500 lines to prevent token waste.
Prevent Claude from pondering for 3 hours.

## Trigger Conditions
- File over 500 lines
- Expected to reference more than 10 files in context
- Same file referenced 3 or more times

## Auto-Detection and Summarization

```bash
#!/bin/bash
# Auto-detect large files and request summarization
CACHE_DIR=".claude/context-cache"
mkdir -p "$CACHE_DIR"

find . -type f \( -name "*.vue" -o -name "*.java" -o -name "*.js" -o -name "*.ts" \) \
  | grep -v node_modules | grep -v .git | grep -v dist \
  | while read f; do
    lines=$(wc -l < "$f")
    if [ "$lines" -gt 500 ]; then
      fname=$(echo "$f" | tr '/' '_')
      cache_file="$CACHE_DIR/${fname}.summary.md"
      if [ ! -f "$cache_file" ]; then
        echo "LARGE: $f ($lines lines) → summary needed: $cache_file"
      else
        echo "CACHED: $f → $cache_file"
      fi
    fi
done
```

## How to Create Summary Files

```bash
# Claude summarizes directly
cat target-file.vue | head -50   # understand structure
cat target-file.vue | tail -50   # understand end section

# Write summary and save to cache
cat > .claude/context-cache/src_pages_LargePage.vue.summary.md << 'EOF'
## File Summary: src/pages/LargePage.vue

### Role
[what this file does]

### Main Components
- data: [main variables]
- computed: [main computed properties]
- methods: [main method list]
- API calls: [endpoint list]

### Dependencies
- Components: [used components]
- Store: [used stores]
- Common utilities: [used utilities]

### Caution When Modifying
- [areas affected by changes]
EOF
```

## Context Loading Priority

```
Priority 1: .claude/context-cache/*.summary.md  (summaries)
Priority 2: docs/project-structure.md           (structure docs)
Priority 3: Actual source files                  (only when needed)
```

## Thinking Time Limit Rules

```
Simple implementation task:       no thinking → execute immediately
Design decision task:             thinking max 5 minutes
Complex architecture decision:    thinking max 15 minutes
Over 15 minutes:                  → decompose task into 3 or fewer subtasks and restart
```

## Extension Points
- Linked with skill-05 deploy: clean up unnecessary cache before deployment
- Linked with hook-01 pre-task: auto-load cache before task starts
