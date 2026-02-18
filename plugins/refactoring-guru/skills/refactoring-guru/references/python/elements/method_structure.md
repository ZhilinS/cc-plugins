# Method Structure

## Single Responsibility

A method should do one thing. If the name needs "and" to describe it, split it.

```python
# Bad - two complex operations in one method
def _fetch_and_cache(self, url: str) -> Data:
    response = await self._client.get(url)
    data = self._parse(response)
    self._cache[url] = data
    return data

# Good - separate concerns, compose at call site
def _fetch(self, url: str) -> Data:
    response = await self._client.get(url)
    return self._parse(response)

def _cache(self, url: str, data: Data) -> Data:
    self._cache[url] = data
    return data

# Usage: compose operations
data = self._cache(url, await self._fetch(url))
```

Or use a wrapper pattern:

```python
# Good - caching wraps fetching
async def data(self, url: str) -> Data:
    if url in self._cache:
        return self._cache[url]
    data = await self._fetch(url)
    self._cache[url] = data
    return data
```

## Method Length

Keep methods short (15-20 lines max) so the method signature stays visible on screen.

**Why it matters:** Generic variable names like `request`, `items`, `result` get their meaning from the method name. When the method fits on one screen, the reader always sees `_fetch_backlinks` at the top, which tells them `request` is a backlinks request.

```python
# Good - short method, context always visible
async def _fetch_backlinks(self, url: str) -> list[BacklinkItem]:
    request = self._build_request(url)
    return [
        self._convert(item)
        async for item in self._stub.Backlinks(request)
    ]
```

Long methods force scrolling. Once the method signature scrolls off screen, variable names lose their context.

```python
# Bad - 50+ line method, reader scrolls and forgets context
async def _fetch_backlinks(self, url: str) -> list[BacklinkItem]:
    # ... 20 lines of setup ...
    request = self._build_request(url)  # What kind of request? Can't see method name
    # ... 30 more lines ...
```

**Rule:** If a method is too long for generic names to be clear, the method is too long. Extract helpers.

## Extract When

Extract a helper method when:

1. **Logic is reused** - Same code appears in multiple places
2. **Logic is complex** - More than 3-5 lines doing one conceptual thing
3. **Logic needs a name** - The operation deserves explanation

```python
# Before - inline complexity
async def process_order(self, order: Order) -> Result:
    # Validate inventory
    for item in order.items:
        stock = await self._inventory.stock(item.sku)
        if stock < item.quantity:
            raise InsufficientStock(item.sku)

    # Calculate totals
    subtotal = sum(item.price * item.quantity for item in order.items)
    tax = subtotal * self._tax_rate
    total = subtotal + tax

    # Create charge
    ...

# After - named operations
async def process_order(self, order: Order) -> Result:
    await self._validate_inventory(order.items)
    total = self._calculate_total(order.items)
    return await self._create_charge(order, total)
```

## Don't Extract When

Don't extract if it just moves code without adding clarity:

```python
# Bad - extraction adds no value
def _user_id(self) -> int:
    return self._user.id

# Just use directly
user_id = self._user.id
```

Don't extract single-use code that's already clear:

```python
# Bad - unnecessary extraction
def _build_greeting(self, name: str) -> str:
    return f"Hello, {name}"

def greet(self, name: str) -> None:
    print(self._build_greeting(name))

# Good - inline is clearer
def greet(self, name: str) -> None:
    print(f"Hello, {name}")
```

## Composition Over Nesting

Prefer flat composition over deeply nested logic.

```python
# Bad - nested conditionals
def process(self, data: Data) -> Result:
    if data.is_valid:
        if data.needs_transform:
            transformed = transform(data)
            if transformed.is_complete:
                return finalize(transformed)
            else:
                return partial(transformed)
        else:
            return finalize(data)
    else:
        raise InvalidData()

# Good - early returns, flat flow
def process(self, data: Data) -> Result:
    if not data.is_valid:
        raise InvalidData()

    to_finalize = transform(data) if data.needs_transform else data

    if not to_finalize.is_complete:
        return partial(to_finalize)

    return finalize(to_finalize)
```
