# Python Style Principles

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

## Prefer Lazy Initialization

Initialize expensive resources only when first needed, not at module load time or class instantiation.

```python
# Bad - eager initialization
class ApiClient:
    def __init__(self):
        self._connection = self._create_connection()  # Always created

# Good - lazy initialization
class ApiClient:
    def __init__(self):
        self._connection: Connection | None = None

    @property
    def connection(self) -> Connection:
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection
```

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
