# RSS Default Feeds Plan

1. Add a failing settings service test proving built-in defaults are returned when store and env feeds are empty.
2. Add a failing provider settings API test proving default feeds appear from `/settings/providers` fallback.
3. Implement a shared built-in default RSS feed constant in backend config or settings service.
4. Wire settings fallback order to persisted -> env -> built-in defaults.
5. Update README/backend README to mention the built-in five-feed default set.
6. Run targeted tests, then backend full test suite.
