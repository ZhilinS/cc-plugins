# Naming Rules

## Context Gives Meaning to Generic Names

The function name provides context for local variables. Generic names like `request`, `items`, `result`, `data` are clear when the surrounding function name establishes what they are.

```javascript
// Good - function context makes generic names clear
const fetchBacklinks = async (url) => {
  const request = buildRequest(url)    // Clearly a backlinks request
  const items = await api.get(request) // Clearly backlink items
  return items.map(parse)
}

const fetchUsers = async (orgId) => {
  const request = buildRequest(orgId)  // Clearly a users request
  const items = await api.get(request) // Clearly user items
  return items.map(parse)
}
```

The same `request` and `items` names work in both functions because the function name (`fetchBacklinks` vs `fetchUsers`) provides the context.

## When Generic Names Fail

Generic names become unclear when the function itself is generic or does multiple things.

```javascript
// Bad - function name doesn't establish context
const process = (data) => {
  const result = transform(data)
  const temp = validate(result)
  return temp
}

// Good - specific function name + generic locals work
const processOrder = (order) => {
  const validated = validate(order)
  const enriched = enrich(validated)
  return enriched
}
```

## No "is" Prefix for Boolean Adjectives

When a boolean reads naturally as an adjective, skip the `is` prefix. It adds noise without adding meaning.

```javascript
// Bad - noisy prefixes
const isActive = true
const isVisible = false
const isEnabled = true

if (isActive && isVisible) { }

// Good - clean adjectives
const active = true
const visible = false
const enabled = true

if (active && visible) { }
```

Keep verb prefixes that form natural questions:

```javascript
// Good - verb prefixes that form questions
const hasPermission = () => user.role === 'admin'
const canEdit = () => hasPermission() && !locked
const shouldRetry = () => attempts < MAX_RETRIES
```

## Collection Plurals

Use plural names for collections. Use singular for individual items when iterating.

```javascript
// Bad - redundant suffixes
const userList = fetchUsers()
const itemArray = []

for (const u of userList) { }

// Good - simple plurals
const users = fetchUsers()
const items = []

for (const user of users) {
  process(user)
}
```

## Keep Names Short

Names should be as short as possible while remaining clear in context. Avoid redundant qualifiers.

```javascript
// Bad - verbose names
const currentUserObject = getCurrentUser()
const requestUrlString = buildUrl(params)
const userDataList = fetchUserData()

// Good - concise names
const user = getCurrentUser()
const url = buildUrl(params)
const users = fetchUsers()
```

## Case Conventions

```javascript
// Variables and functions: camelCase
const userName = 'alice'
const fetchData = async () => { }

// Constructors and classes: PascalCase
class UserService { }
const HttpClient = createClient()

// Constants: SCREAMING_SNAKE_CASE
const MAX_RETRIES = 3
const API_BASE_URL = 'https://api.example.com'
const DEFAULT_TIMEOUT = 30000
```

## Private by Convention

Use underscore prefix for module-private functions and variables.

```javascript
// Good - underscore for private
const _cache = new Map()
const _validateInput = (data) => { }

// Public API
export const fetchUser = async (id) => {
  if (_cache.has(id)) return _cache.get(id)

  _validateInput(id)
  const user = await api.get(`/users/${id}`)
  _cache.set(id, user)
  return user
}
```

## Method Naming by Action

Use verb prefixes that describe what the function does.

| Prefix | Meaning | Example |
|--------|---------|---------|
| `fetch` | Retrieve from external source | `fetchUsers()` |
| `create` | Create and return new instance | `createOrder(items)` |
| `build` | Construct from parts | `buildRequest(params)` |
| `parse` | Extract structure from raw | `parseResponse(json)` |
| `validate` | Check and return valid/throw | `validateInput(data)` |
| `handle` | Process/react to something | `handleError(err)` |

```javascript
// Good - clear action prefixes
const fetchUser = async (id) => api.get(`/users/${id}`)
const createOrder = (items) => ({ id: uuid(), items, status: 'pending' })
const buildUrl = (path, params) => `${BASE}${path}?${stringify(params)}`
const parseUser = (json) => ({ id: json.id, name: json.full_name })
```

## Avoid Abbreviations

Use full words except for universally known abbreviations.

```javascript
// Bad - unclear abbreviations
const usrInfo = (usrId) => { }
const calcTtlAmt = () => { }
const cfg = loadCfg()

// Good - full words
const userInfo = (userId) => { }
const calculateTotalAmount = () => { }
const config = loadConfig()

// OK - universal abbreviations
const url = buildUrl()
const apiKey = getApiKey()
const userId = user.id
const httpClient = createClient()
```
