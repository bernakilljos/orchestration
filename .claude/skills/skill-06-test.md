# SKILL-06 — Test (Automated Test Generation and Execution)

## Purpose
Automatically generate and execute test code after implementation is complete.
Cannot pass hook-02-post-impl quality gate without tests.

## Execution Method
```bash
# Run all tests
bash .claude/scripts/test.sh

# Generate + run tests for a specific file
bash .claude/scripts/test.sh src/path/to/TargetFile
```

## Test Classification

| Type | Target | Required |
|------|--------|----------|
| Smoke Test | Page rendering, API response | Required |
| Unit Test | Methods, calculation logic | When implementation is large |
| Integration Test | API + DB integration | Required for backend |

## Auto-Generate Tests with Codex

```bash
# Adapt prompt to your stack:
codex --model gpt-4o \
  --instructions "Generate [stack-specific] unit test.
  Rules:
  - Use [test framework appropriate for the stack]
  - Cover: happy path, error path, edge cases
  - File location: tests/[TestFileName]" \
  --context "$(cat src/path/to/TargetFile)" \
  "generate unit test"
```

## Test Patterns by Stack (Reference — pick what applies)

### Node.js / JavaScript (Jest)
```javascript
// tests/unit/target.spec.js
const { myFunction } = require('../../src/target')

describe('myFunction', function() {
  it('returns expected result', function() {
    expect(myFunction('input')).toBe('expected')
  })
})
```

### Python (pytest)
```python
# tests/test_target.py
from src.target import my_function

def test_returns_expected():
    assert my_function('input') == 'expected'
```

### Java / Spring Boot (JUnit 5 + Mockito)
```java
@ExtendWith(MockitoExtension.class)
class TargetServiceTest {
    @Mock TargetRepository targetRepository;
    @InjectMocks TargetService targetService;

    @Test
    void data_retrieval_success() {
        given(targetRepository.findAll()).willReturn(Collections.emptyList());
        List<TargetDto> result = targetService.findAll();
        assertNotNull(result);
        verify(targetRepository, times(1)).findAll();
    }
}
```

### Vue 2 (vue-test-utils + Jest) — Vue 프로젝트에만 적용
```javascript
import { shallowMount } from '@vue/test-utils'
import TargetPage from '@/pages/TargetPage.vue'

describe('TargetPage', function() {
  it('renders successfully', function() {
    var wrapper = shallowMount(TargetPage, {
      mocks: { $store: { getters: {}, dispatch: jest.fn() }, $router: { push: jest.fn() } }
    })
    expect(wrapper.exists()).toBe(true)
  })
})
```

## Failure Handling

```
Test FAIL
  → Analyze error log
  → Instruct Codex to fix
  → Re-implement → re-test
  → 2 consecutive failures → Team Lead re-review
```

## Extension Points
- skill-08-e2e.md: Cypress E2E tests
- Linked with quality-gate.sh: reflect test results in gate judgment
