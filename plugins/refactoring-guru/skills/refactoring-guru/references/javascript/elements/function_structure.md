# Function Structure

## Arrow Functions by Default

Use arrow functions for most cases. They're concise and avoid `this` binding issues.

```javascript
// Good - arrow functions
const add = (a, b) => a + b
const double = (x) => x * 2
const fetchUser = async (id) => api.get(`/users/${id}`)

// Good - multiline arrow
const processOrder = (order) => {
  const validated = validate(order)
  const total = calculateTotal(validated.items)
  return { ...validated, total }
}
```

## When to Use Regular Functions

Use `function` declarations for:
- Functions that need hoisting
- Recursive functions that reference themselves by name
- Generator functions
- Methods that genuinely need `this`

```javascript
// Good - hoisting allows calling before definition
processAll(items)

function processAll(items) {
  return items.map(processItem)
}

// Good - named recursion
function fibonacci(n) {
  if (n <= 1) return n
  return fibonacci(n - 1) + fibonacci(n - 2)
}

// Good - generator
function* range(start, end) {
  for (let i = start; i < end; i++) {
    yield i
  }
}
```

## Single Responsibility

A function should do one thing. If you need "and" to describe it, split it.

```javascript
// Bad - two operations mixed
const fetchAndCache = async (url) => {
  const response = await fetch(url)
  const data = await response.json()
  cache.set(url, data)
  return data
}

// Good - separate concerns
const fetchData = async (url) => {
  const response = await fetch(url)
  return response.json()
}

const withCache = (fn) => {
  const cache = new Map()
  return async (key) => {
    if (cache.has(key)) return cache.get(key)
    const result = await fn(key)
    cache.set(key, result)
    return result
  }
}

const cachedFetch = withCache(fetchData)
```

## Method Length

Keep functions short (15-20 lines max) so the function name stays visible on screen. This matters because generic variable names get their meaning from context.

```javascript
// Good - short function, context always visible
const fetchBacklinks = async (url) => {
  const request = buildRequest(url)
  const items = await api.get(request)
  return items.map(parse)
}

// Bad - 50+ lines, reader scrolls and loses context
const fetchBacklinks = async (url) => {
  // ... 20 lines of setup ...
  const request = buildRequest(url)  // What kind of request? Can't see function name
  // ... 30 more lines ...
}
```

**Rule:** If a function is too long for generic names to be clear, the function is too long. Extract helpers.

## Extract When

Extract a helper function when:

1. **Logic is reused** - Same code appears in multiple places
2. **Logic is complex** - More than 3-5 lines doing one conceptual thing
3. **Logic needs a name** - The operation deserves explanation

```javascript
// Before - inline complexity
const processOrder = async (order) => {
  // Validate inventory
  for (const item of order.items) {
    const stock = await inventory.check(item.sku)
    if (stock < item.quantity) {
      throw new InsufficientStock(item.sku)
    }
  }

  // Calculate totals
  const subtotal = order.items.reduce((sum, item) =>
    sum + item.price * item.quantity, 0)
  const tax = subtotal * TAX_RATE
  const total = subtotal + tax

  // Save
  return database.save({ ...order, total })
}

// After - named operations
const validateInventory = async (items) => {
  for (const item of items) {
    const stock = await inventory.check(item.sku)
    if (stock < item.quantity) {
      throw new InsufficientStock(item.sku)
    }
  }
}

const calculateTotal = (items) => {
  const subtotal = items.reduce((sum, item) =>
    sum + item.price * item.quantity, 0)
  return subtotal + subtotal * TAX_RATE
}

const processOrder = async (order) => {
  await validateInventory(order.items)
  const total = calculateTotal(order.items)
  return database.save({ ...order, total })
}
```

## Don't Extract When

Don't extract if it just moves code without adding clarity:

```javascript
// Bad - unnecessary extraction
const getUserId = (user) => user.id

// Just use directly
const id = user.id

// Bad - single-use code that's already clear
const buildGreeting = (name) => `Hello, ${name}`
const greet = (name) => console.log(buildGreeting(name))

// Good - inline is clearer
const greet = (name) => console.log(`Hello, ${name}`)
```

## Early Returns Over Nesting

Use guard clauses to handle edge cases at the top. Keep the happy path at the lowest indentation level.

```javascript
// Bad - nested conditionals
const processOrder = (order) => {
  if (order) {
    if (order.items.length > 0) {
      if (order.status === 'pending') {
        const total = calculateTotal(order.items)
        return { ...order, total }
      } else {
        return null
      }
    } else {
      return null
    }
  } else {
    return null
  }
}

// Good - early returns, flat flow
const processOrder = (order) => {
  if (!order) return null
  if (order.items.length === 0) return null
  if (order.status !== 'pending') return null

  const total = calculateTotal(order.items)
  return { ...order, total }
}
```

## Pure Core, Impure Shell

Keep the core logic pure. Push side effects to the edges.

```javascript
// Bad - side effects mixed with logic
const processUser = async (userId) => {
  console.log('Starting process')
  const user = await database.find(userId)
  const transformed = { ...user, processed: true }
  await database.save(transformed)
  analytics.track('user_processed', userId)
  return transformed
}

// Good - pure core, impure shell
const transformUser = (user) => ({
  ...user,
  processed: true,
})

const processUser = async (userId) => {
  const user = await database.find(userId)
  const transformed = transformUser(user)  // Pure
  await database.save(transformed)
  return transformed
}
```
