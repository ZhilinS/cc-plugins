# Async Patterns Rules

## Async Comprehensions Over Manual Loops

Use `[x async for x in stream]` for gRPC/async streaming responses. More concise and Pythonic.

```python
# Bad - manual loop
items = []
async for item in self._stub.List(request):
    items.append(convert(item))

# Good - async comprehension
items = [convert(item) async for item in self._stub.List(request)]
```

## Async Comprehension with Filtering

```python
# Bad - manual loop with condition
items = []
async for item in self._stub.List(request):
    if item.is_active:
        items.append(convert(item))

# Good - async comprehension with filter
items = [
    convert(item)
    async for item in self._stub.List(request)
    if item.is_active
]
```

## Parallel Execution with gather

Use `asyncio.gather` for independent async operations that can run concurrently.

```python
# Bad - sequential execution
users = await fetch_users()
orders = await fetch_orders()
products = await fetch_products()

# Good - parallel execution
users, orders, products = await asyncio.gather(
    fetch_users(),
    fetch_orders(),
    fetch_products(),
)
```

## Gather with Error Handling

Use `return_exceptions=True` when you want to handle partial failures.

```python
# Bad - one failure cancels all
results = await asyncio.gather(
    fetch_a(),
    fetch_b(),
    fetch_c(),
)

# Good - collect results and errors
results = await asyncio.gather(
    fetch_a(),
    fetch_b(),
    fetch_c(),
    return_exceptions=True,
)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        logger.warning("event=fetch_data_partial_failure", index=i, error=str(result))
    else:
        process(result)
```

## Semaphore for Rate Limiting

Use `asyncio.Semaphore` to limit concurrent operations.

```python
# Bad - unbounded concurrency
async def fetch_all(urls: list[str]) -> list[Response]:
    return await asyncio.gather(*[fetch(url) for url in urls])

# Good - bounded concurrency
async def fetch_all(urls: list[str], max_concurrent: int = 10) -> list[Response]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_limit(url: str) -> Response:
        async with semaphore:
            return await fetch(url)

    return await asyncio.gather(*[fetch_with_limit(url) for url in urls])
```

## Timeout for Async Operations

Always set timeouts for external calls to prevent hanging.

```python
# Bad - no timeout
result = await external_api.call()

# Good - explicit timeout
try:
    result = await asyncio.wait_for(
        external_api.fetch_user(user_id),
        timeout=30.0,
    )
except asyncio.TimeoutError:
    logger.warning("event=fetch_user_timeout", user_id=user_id)
    result = default_value
```

## Context Manager for Async Resources

Use async context managers for resources that need cleanup.

```python
# Bad - manual cleanup
client = await create_client()
try:
    result = await client.fetch()
finally:
    await client.close()

# Good - async context manager
async with create_client() as client:
    result = await client.fetch()
```

## Async Generator for Streaming

Use async generators when producing items incrementally.

```python
# Good - async generator for streaming
async def stream_results(query: str) -> AsyncIterator[Result]:
    async for page in self._fetch_pages(query):
        for item in page.items:
            yield self._convert(item)

# Usage
async for result in stream_results("query"):
    process(result)
```
