# Screen Design — [Screen Name]

## Basic Info

| Item | Content |
|------|---------|
| Screen ID | SCR-[Number] |
| Screen Name | [Screen Name] |
| URL | /[path] |
| File Path | src/pages/[filename].vue |
| Assignee | |

## Screen Purpose
[Why this screen exists. What the user achieves on this screen.]

## Layout

```
+------------------------------------------+
| [Header / Navigation]                     |
+------------------------------------------+
| [Search/Filter Area]                      |
|   [Input Field1]  [Input Field2]  [Search Button] |
+------------------------------------------+
| [List/Table Area]                         |
|   Column1 | Column2 | Column3 | Action   |
|   --------+---------+---------+--------  |
|   data    | data    | data    | [Edit][Delete] |
+------------------------------------------+
| [Pagination]                              |
+------------------------------------------+
```

## Component List

| Component | Role | Path |
|-----------|------|------|
| [Component Name] | [Role] | src/components/[path] |

## Data Flow

```
mounted()
  -> API call: GET /api/v1/[resource]
  -> Save to data.list
  -> Render screen

Search button click
  -> Call searchData()
  -> API call (with filter parameters)
  -> Update results
```

## Main data / computed / methods

```javascript
data() {
  return {
    list: [],
    searchParams: {
      keyword: '',
      page: 0,
      size: 20
    },
    totalCount: 0
  }
},
methods: {
  async fetchList() { /* API call */ },
  async searchData() { /* Search */ },
  async deleteItem(id) { /* Delete */ }
}
```

## Alert Usage Rules

```javascript
// Use mapActions (direct this.$alert usage prohibited)
...mapActions("alert", ["ADD_ALERT"]),

this.ADD_ALERT({ message: "Saved successfully.", color: "success" })
this.ADD_ALERT({ message: "An error occurred.", color: "error" })
```

## Acceptance Criteria

- [ ] List query works correctly
- [ ] Search/filter works correctly
- [ ] Pagination works correctly
- [ ] Alert displayed on error
- [ ] No optional chaining
- [ ] No hardcoding
- [ ] lint passes
