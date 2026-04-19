# Python Style Principles

## Prefer Top-Level Imports

All imports at the top of the file. No imports inside functions, methods, or conditionals.

```python
# Bad - import inside function
def get_backlinks(url: str) -> BacklinksResponse:
    from app.services.backlinks import BacklinksService  # Hidden dependency!
    return BacklinksService().fetch(url)

# Bad - conditional import
def process(data: dict) -> Result:
    if data.get("format") == "json":
        import json  # Surprising!
        return json.dumps(data)

# Good - all imports at top
from app.services.backlinks import BacklinksService

def get_backlinks(url: str) -> BacklinksResponse:
    return BacklinksService().fetch(url)
```

Why:
- **Visibility** — Dependencies are declared upfront, not hidden in code
- **Fail-fast** — Import errors surface at startup, not runtime
- **Performance** — No repeated import overhead on each call
- **Tooling** — Linters, formatters, and IDEs work correctly

Exceptions:
- `TYPE_CHECKING` blocks for type hints that would cause circular imports
- Optional dependencies with try/except at module level

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import User  # Only for type hints, not runtime

# Optional dependency - still at top level
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
```

## Prefer Decorators for Cross-Cutting Concerns

Extract repeated patterns (logging, error handling, validation, retries) into decorators. Keep method bodies focused on business logic.

```python
# Bad - repeated error handling
async def fetch_users(self) -> list[User]:
    try:
        return await self._client.users()
    except ApiError as e:
        logger.error("event=fetch_users_failed", error=str(e))
        return []

async def fetch_orders(self) -> list[Order]:
    try:
        return await self._client.orders()
    except ApiError as e:
        logger.error("event=fetch_orders_failed", error=str(e))
        return []

# Good - decorator handles cross-cutting concern
@api_error_handler('fetch_users', list)
async def fetch_users(self) -> list[User]:
    return await self._client.users()

@api_error_handler('fetch_orders', list)
async def fetch_orders(self) -> list[Order]:
    return await self._client.orders()
```

## Prefer Loose Coupling

Dependencies should be injected, not created internally. Services receive their dependencies through constructors or factory functions.

```python
# Bad - tight coupling
class UserService:
    def __init__(self):
        self.db = Database()  # Creates its own dependency
        self.cache = RedisCache()

# Good - loose coupling
class UserService:
    def __init__(self, db: Database, cache: Cache):
        self._db = db
        self._cache = cache
```

## Prefer Immutable Classes with Eager Initialization

Initialize all dependencies in the constructor. Avoid lazy initialization - it makes classes mutable and harder to reason about. Classes should be fully ready to use after construction.

```python
# Bad - lazy initialization (mutable state)
class ApiClient:
    def __init__(self):
        self._connection: Connection | None = None

    @property
    def connection(self) -> Connection:
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection

# Good - eager initialization (immutable after construction)
class ApiClient:
    def __init__(self, connection: Connection):
        self._connection = connection

# Good - if creation is needed, use factory function
def create_api_client() -> ApiClient:
    connection = create_connection()
    return ApiClient(connection)
```

For expensive resources, prefer factory functions or dependency injection over lazy properties.

## Prefer Composition Over Inheritance

Build behavior by composing objects rather than deep inheritance hierarchies. Use protocols/interfaces for contracts.

```python
# Bad - inheritance hierarchy
class BaseService:
    def log(self): ...
    def validate(self): ...

class UserService(BaseService):
    def get_user(self): ...

class AdminUserService(UserService):
    def get_admin_user(self): ...

# Good - composition
class UserService:
    def __init__(self, logger: Logger, validator: Validator):
        self._logger = logger
        self._validator = validator
```

## Prefer Extract Helper Over Inline Logic

When a method grows beyond 15-20 lines, extract logical chunks into private helper methods. Name helpers by what they do.

```python
# Bad - long method with multiple responsibilities
async def process_order(self, order: Order) -> Result:
    # 50 lines of validation, transformation, saving, notification...

# Good - orchestrator with focused helpers
async def process_order(self, order: Order) -> Result:
    validated = self._validate_order(order)
    transformed = self._transform_for_storage(validated)
    saved = await self._save_order(transformed)
    await self._notify_completion(saved)
    return Result(order_id=saved.id)
```

## Prefer Explicit Over Implicit

Be explicit about types, return values, and behavior. Avoid magic or hidden side effects.

```python
# Bad - implicit behavior
def get_user(user_id):  # No types, might return None or raise
    return db.find(user_id)

# Good - explicit contract
def get_user(user_id: int) -> User | None:
    """Returns User if found, None otherwise. Never raises."""
    return db.find_by_id(User, user_id)
```

## Prefer Deferred Computation

Build pipelines where `__init__` only initializes empty state, methods fill and transform state, and terminal methods return results.

```python
class Response:
    def __init__(self):
        self._data: list[Item] = []  # Empty state, no execution

    def get(self, request: Request) -> 'Response':
        self._data = request.execute()  # Work happens here
        return self

    def filter(self, f: Filter) -> 'Response':
        self._data = [x for x in self._data if f.apply(x)]
        return self

    def list(self) -> list[Item]:  # Terminal
        return self._data

# Usage - vertical stacking for readability
result = (
    Response()
    .get(Backlinks(url=domain))
    .filter(TLD())
    .list()
)
```

Key points:
- `__init__` initializes empty state only, no execution
- Methods fill or transform internal state, return `self` for chaining
- Terminal methods (`list()`, `execute()`, `run()`) return the actual data
- Use strategy pattern for pluggable operations (e.g., `Filter` interface with `apply()` method)
