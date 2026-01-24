# Method Signature Rules

## Type Safety Over Magic Strings

Use `Literal` or `Enum` for constrained string parameters. This enables IDE autocomplete and catches invalid values at type-check time.

```python
# Bad - any string accepted
def fetch(sort_direction: str = 'desc') -> list: ...

# Good - constrained to valid values
SortDirection = Literal['asc', 'desc']
def fetch(sort_direction: SortDirection = 'desc') -> list: ...
```

## Keyword Arguments for Clarity

Use kwargs when calling methods with 3+ parameters. Positional arguments beyond 2-3 become hard to read.

```python
# Bad - positional soup
items = await self._fetch_items(url, scope, 10, Direction.DESC)

# Good - named parameters
items = await self._fetch_items(
    url=url,
    scope=scope,
    limit=10,
    direction=Direction.DESC,
)
```

## Default Values for Optional Parameters

Provide sensible defaults for optional parameters. Put required parameters first, optional with defaults after.

```python
# Bad - required param after optional
def search(limit: int = 10, query: str) -> list: ...

# Good - required first, optional with defaults after
def search(query: str, limit: int = 10, offset: int = 0) -> list: ...
```

## Return Type Annotations

Always annotate return types. Use `| None` for functions that may not return a value.

```python
# Bad - no return type
def find_user(user_id: int):
    return db.get(user_id)

# Good - explicit return type
def find_user(user_id: int) -> User | None:
    return db.get(user_id)
```

## Method Naming Patterns

Follow consistent naming patterns:

| Pattern | Purpose | Example |
|---------|---------|---------|
| `*` (noun) | Public API, returns data | `backlinks()` or `backlinks_list()` |
| `_fetch_*` | Private data fetching | `_fetch_backlinks()` |
| `_convert_*` | Transform between types | `_convert_backlink()` |
| `_build_*` | Construct objects | `_build_target()` |
| `_validate_*` | Input validation | `_validate_limit()` |
| `_handle_*` | Process results | `_handle_error()` |

```python
# Good - clear naming hierarchy
async def backlinks(self, url: str) -> BacklinksResponse:
    """Public API - orchestrates the flow."""
    items = await self._fetch_backlinks(url)
    return BacklinksResponse(items=items)

async def _fetch_backlinks(self, url: str) -> list[Backlink]:
    """Private - handles data fetching."""
    request = self._build_request(url)
    raw = await self._client.fetch(request)
    return [self._convert_backlink(b) for b in raw]
```

## Avoid Boolean Parameters

Boolean parameters obscure meaning at call sites. Use enums or separate methods instead.

```python
# Bad - what does True mean?
def users(include_deleted: bool = False) -> list[User]: ...
result = users(True)

# Good - explicit enum
class UserFilter(Enum):
    ACTIVE = "active"
    ALL = "all"

def users(filter: UserFilter = UserFilter.ACTIVE) -> list[User]: ...
result = users(UserFilter.ALL)
```
