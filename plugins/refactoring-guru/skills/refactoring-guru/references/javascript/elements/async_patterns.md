# Async Patterns

## Async/Await Over .then()

Use async/await for cleaner, more readable async code. It's easier to debug and reason about.

```javascript
// Bad - .then() chains
fetchUser(id)
  .then(user => fetchOrders(user.id))
  .then(orders => processOrders(orders))
  .then(result => console.log(result))
  .catch(err => console.error(err))

// Good - async/await
const loadUserOrders = async (id) => {
  const user = await fetchUser(id)
  const orders = await fetchOrders(user.id)
  return processOrders(orders)
}
```

## Promise.all for Parallel Execution

Use `Promise.all` when operations are independent and can run concurrently.

```javascript
// Bad - sequential when parallel is possible
const fetchDashboard = async (userId) => {
  const user = await fetchUser(userId)
  const orders = await fetchOrders(userId)
  const notifications = await fetchNotifications(userId)
  return { user, orders, notifications }
}

// Good - parallel execution
const fetchDashboard = async (userId) => {
  const [user, orders, notifications] = await Promise.all([
    fetchUser(userId),
    fetchOrders(userId),
    fetchNotifications(userId),
  ])
  return { user, orders, notifications }
}
```

## Promise.allSettled for Partial Failures

Use `Promise.allSettled` when you want all results even if some fail.

```javascript
// Bad - one failure cancels all
const fetchAll = async (urls) => {
  return Promise.all(urls.map(fetch))
}

// Good - collect results and errors
const fetchAll = async (urls) => {
  const results = await Promise.allSettled(urls.map(fetch))

  return results.map((result, i) => {
    if (result.status === 'fulfilled') {
      return { url: urls[i], data: result.value }
    }
    return { url: urls[i], error: result.reason }
  })
}
```

## Error Handling at Boundaries

Let errors propagate through pure functions. Catch at the edges where you can handle them meaningfully.

```javascript
// Bad - catching too early
const fetchUser = async (id) => {
  try {
    return await api.get(`/users/${id}`)
  } catch (err) {
    console.log('Error:', err)
    return null
  }
}

const getUser = async (id) => {
  const user = await fetchUser(id)
  if (!user) return null  // Error already swallowed
  return user
}

// Good - let errors propagate, catch at boundary
const fetchUser = async (id) => api.get(`/users/${id}`)

const getUser = async (id) => fetchUser(id)

// Boundary handler (route, event handler, etc.)
const handleGetUser = async (req, res) => {
  try {
    const user = await getUser(req.params.id)
    res.json(user)
  } catch (err) {
    if (err.status === 404) {
      res.status(404).json({ error: 'User not found' })
    } else {
      res.status(500).json({ error: 'Internal error' })
    }
  }
}
```

## Avoid Mixing Callbacks and Promises

Pick one pattern. Convert callback-based APIs to promises.

```javascript
// Bad - mixing patterns
const readFile = (path, callback) => {
  fs.readFile(path, 'utf8', (err, data) => {
    if (err) callback(err)
    else callback(null, data)
  })
}

// Then trying to use with async
const process = async () => {
  // Can't await callback-based function
}

// Good - promisify or use promise-based API
import { readFile } from 'fs/promises'

const process = async (path) => {
  const data = await readFile(path, 'utf8')
  return parse(data)
}

// Good - wrap callback API in Promise
const readFileAsync = (path) => new Promise((resolve, reject) => {
  fs.readFile(path, 'utf8', (err, data) => {
    if (err) reject(err)
    else resolve(data)
  })
})
```

## Sequential vs Parallel Loops

Choose the right pattern based on dependencies.

```javascript
// Parallel - when items are independent
const processAll = async (items) => {
  return Promise.all(items.map(processItem))
}

// Sequential - when order matters or avoiding rate limits
const processSequentially = async (items) => {
  const results = []
  for (const item of items) {
    results.push(await processItem(item))
  }
  return results
}

// Controlled concurrency - parallel with limit
const processWithLimit = async (items, limit = 5) => {
  const results = []
  const chunks = []

  for (let i = 0; i < items.length; i += limit) {
    chunks.push(items.slice(i, i + limit))
  }

  for (const chunk of chunks) {
    const chunkResults = await Promise.all(chunk.map(processItem))
    results.push(...chunkResults)
  }

  return results
}
```

## Timeouts

Always set timeouts for external calls to prevent hanging.

```javascript
// Bad - no timeout
const fetchData = async (url) => {
  return fetch(url)
}

// Good - with timeout
const fetchWithTimeout = async (url, ms = 5000) => {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), ms)

  try {
    const response = await fetch(url, { signal: controller.signal })
    return response
  } finally {
    clearTimeout(timeout)
  }
}

// Good - Promise.race for simple timeout
const withTimeout = (promise, ms) => {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('Timeout')), ms)
  )
  return Promise.race([promise, timeout])
}

const data = await withTimeout(fetchData(url), 5000)
```

## Async Iteration

Use `for await...of` for async iterables.

```javascript
// Good - async iteration
const processStream = async (stream) => {
  const results = []
  for await (const chunk of stream) {
    results.push(process(chunk))
  }
  return results
}

// Good - async generator
async function* fetchPages(url) {
  let page = 1
  let hasMore = true

  while (hasMore) {
    const response = await fetch(`${url}?page=${page}`)
    const data = await response.json()
    yield data.items
    hasMore = data.hasMore
    page++
  }
}

// Usage
for await (const items of fetchPages('/api/users')) {
  processItems(items)
}
```
