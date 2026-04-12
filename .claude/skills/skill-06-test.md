# SKILL-06 — Test (Automated Test Generation and Execution)

## Purpose
Automatically generate and execute test code after implementation is complete.
Cannot pass hook-02-post-impl quality gate without tests.

## Execution Method
```bash
# Run all tests
bash .claude/scripts/test.sh

# Generate + run tests for a specific component
bash .claude/scripts/test.sh src/pages/TargetPage.vue
```

## Test Classification

| Type | Target | Required |
|------|--------|----------|
| Smoke Test | Page rendering, API response | Required |
| Unit Test | Methods, calculation logic | When implementation is large |
| Integration Test | API + DB integration | Required for backend |

## Auto-Generate Tests with Codex

```bash
codex --model gpt-4o \
  --instructions "Generate Vue 2 smoke test.
  Rules:
  - Use @vue/test-utils shallowMount
  - Do not use optional chaining (?.)
  - Mock $store/$router with jest.fn()
  - File location: tests/unit/[ComponentName].spec.js" \
  --context "$(cat src/pages/TargetPage.vue)" \
  "generate smoke test"
```

## Vue 2 Test Pattern (Reference)

```javascript
// tests/unit/TargetPage.spec.js
import { shallowMount } from '@vue/test-utils'
import TargetPage from '@/pages/TargetPage.vue'

describe('TargetPage', function() {
  var wrapper
  beforeEach(function() {
    wrapper = shallowMount(TargetPage, {
      mocks: {
        $store: { getters: {}, dispatch: jest.fn(), commit: jest.fn() },
        $router: { push: jest.fn() },
        $route: { params: {}, query: {} }
      }
    })
  })

  it('renders successfully', function() {
    expect(wrapper.exists()).toBe(true)
  })
})
```

## Spring Boot Test Pattern (Reference)

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
