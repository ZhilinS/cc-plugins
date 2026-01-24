# JavaScript Style Principles

## Const by Default

Use `const` for all bindings unless you need to reassign. Never use `var`. Use `let` only for loop counters or values that genuinely need reassignment.

```javascript
// Bad - var and unnecessary let
var users = []
let config = loadConfig()
let total = calculateTotal(items)

// Good - const by default
const users = []
const config = loadConfig()
const total = calculateTotal(items)

// Good - let only when reassignment needed
let count = 0
for (let i = 0; i < items.length; i++) {
  count += items[i].quantity
}
```

## Pure Functions First

Prefer functions that return the same output for the same input and have no side effects. Pure functions are easier to test, reason about, and compose.

```javascript
// Bad - impure, modifies external state
let total = 0
const addToTotal = (amount) => {
  total += amount
}

// Good - pure, returns new value
const add = (a, b) => a + b
const sum = (numbers) => numbers.reduce(add, 0)

// Bad - mutates input
const addItem = (cart, item) => {
  cart.items.push(item)
  return cart
}

// Good - returns new object
const addItem = (cart, item) => ({
  ...cart,
  items: [...cart.items, item],
})
```

## Immutability Over Mutation

Return new objects and arrays instead of mutating existing ones. Use spread operators for updates.

```javascript
// Bad - mutating array
const users = []
users.push(newUser)
users[0].name = 'Updated'

// Good - creating new arrays
const users = []
const updated = [...users, newUser]
const renamed = users.map((user, i) =>
  i === 0 ? { ...user, name: 'Updated' } : user
)

// Bad - mutating object
const config = { timeout: 30 }
config.timeout = 60
config.retries = 3

// Good - spreading into new object
const config = { timeout: 30 }
const updated = { ...config, timeout: 60, retries: 3 }
```

## Composition Over Inheritance

Build behavior by composing small functions rather than class hierarchies. Use factory functions instead of classes when possible.

```javascript
// Bad - inheritance hierarchy
class BaseService {
  log(msg) { console.log(msg) }
  validate(data) { return true }
}

class UserService extends BaseService {
  fetchUser(id) {
    this.log('Fetching user')
    // ...
  }
}

// Good - composition with functions
const withLogging = (fn) => (...args) => {
  console.log(`Calling ${fn.name}`)
  return fn(...args)
}

const fetchUser = async (id) => {
  const response = await api.get(`/users/${id}`)
  return response.data
}

const fetchUserWithLogging = withLogging(fetchUser)

// Good - factory function over class
const createUserService = (api, logger) => ({
  fetch: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  log: (msg) => logger.info(msg),
})
```

## Explicit Over Magic

Be explicit about behavior. Avoid hidden side effects, magical `this` bindings, and implicit type coercion.

```javascript
// Bad - implicit behavior, magic this
function UserCard() {
  this.render = function() {
    setTimeout(function() {
      this.update()  // 'this' is wrong
    }, 100)
  }
}

// Good - explicit, arrow functions
const createUserCard = (user) => {
  const update = () => { /* ... */ }

  const render = () => {
    setTimeout(update, 100)  // No 'this' confusion
  }

  return { render, update }
}

// Bad - implicit coercion
if (value == null) { }
if (items.length) { }

// Good - explicit checks
if (value === null || value === undefined) { }
if (items.length > 0) { }
```

## Early Returns

Use guard clauses at the top of functions. Keep the happy path at the lowest indentation level.

```javascript
// Bad - nested conditionals
const processOrder = (order) => {
  if (order) {
    if (order.items.length > 0) {
      if (order.status === 'pending') {
        // actual logic buried in nesting
        return calculateTotal(order)
      }
    }
  }
  return null
}

// Good - early returns, flat flow
const processOrder = (order) => {
  if (!order) return null
  if (order.items.length === 0) return null
  if (order.status !== 'pending') return null

  return calculateTotal(order)
}
```
