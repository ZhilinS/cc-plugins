# Class Body Rules

## Private Attributes with Underscore Prefix

Use single underscore for internal attributes. Double underscore only for name mangling needs.

```python
# Bad - public attributes for internal state
class Service:
    def __init__(self):
        self.client = Client()
        self.cache = {}

# Good - private attributes
class Service:
    def __init__(self, client: Client):
        self._client = client
        self._cache: dict[str, Any] = {}
```

## Constructor Dependency Injection

Receive dependencies through constructor, store as private attributes.

```python
# Bad - creates dependencies internally
class UserService:
    def __init__(self):
        self._db = Database()
        self._cache = RedisCache()

# Good - dependencies injected
class UserService:
    def __init__(self, db: Database, cache: Cache):
        self._db = db
        self._cache = cache
```

## Alternative Constructors with @classmethod

Use `@classmethod` factory methods with `from_*` prefix when a class needs multiple ways to be instantiated. Keep `__init__` focused on receiving and assigning dependencies; put wiring logic in factory methods. The `__init__` should only assign—no creation, no logic—making the class immutable after construction.

```python
# Bad - God __init__ with conditional logic
class SpectrumAdapter:
    def __init__(self, channel: Channel = None, services: dict = None):
        if channel:
            self._overview = OverviewService(SummaryStub(channel))
            self._position = PositionService(OrganicStub(channel))
        elif services:
            self._overview = services['overview']
            self._position = services['position']

# Good - simple __init__ + factory method
class SpectrumAdapter:
    def __init__(
        self,
        overview_service: OverviewService,
        position_service: PositionService,
    ) -> None:
        self._overview_service = overview_service
        self._position_service = position_service

    @classmethod
    def from_channel(cls, channel: Channel) -> 'SpectrumAdapter':
        return cls(
            overview_service=OverviewService(SummaryStub(channel)),
            position_service=PositionService(OrganicStub(channel)),
        )

# Usage
adapter = SpectrumAdapter.from_channel(channel)  # Production
adapter = SpectrumAdapter(mock_overview, mock_position)  # Tests
```

Standard library examples: `datetime.date.fromtimestamp()`, `dict.fromkeys()`, `pathlib.Path.from_uri()`.

## Immutable After Construction

Classes should be fully initialized in the constructor. No lazy initialization, no `None` placeholders that get filled later. After `__init__` completes, the object is ready and its structure doesn't change.

```python
# Bad - lazy initialization (mutable)
class BacklinksAdapter:
    def __init__(self, channel: Channel):
        self._channel = channel
        self._stub: BacklinksStub | None = None  # Filled later

    def _get_stub(self) -> BacklinksStub:
        if self._stub is None:
            self._stub = BacklinksStub(self._channel)
        return self._stub

# Good - eager initialization (immutable)
class BacklinksAdapter:
    def __init__(self, channel: Channel):
        self._channel = channel
        self._stub = BacklinksStub(channel)  # Ready immediately

# Good - if stub creation is complex, inject it
class BacklinksAdapter:
    def __init__(self, stub: BacklinksStub):
        self._stub = stub
```

## Method Organization

Order methods consistently: public API first, then private helpers.

```python
class BacklinksService:
    # Constructor
    def __init__(self, stub: BacklinksStub):
        self._stub = stub

    # Public API methods
    async def get_backlinks_list(self, url: str) -> BacklinksResponse:
        """Public orchestrator method."""
        items = await self._fetch_backlinks(url)
        return BacklinksResponse(items=items)

    async def get_backlinks_overview(self, url: str) -> OverviewResponse:
        """Another public method."""
        ...

    # Private fetch methods
    async def _fetch_backlinks(self, url: str) -> list[Backlink]:
        """Fetches data from API."""
        ...

    # Private conversion methods
    def _convert_backlink(self, raw: RawBacklink) -> Backlink:
        """Converts API response to domain model."""
        ...

    # Private utility methods
    def _build_request(self, url: str) -> Request:
        """Builds API request."""
        ...

    def _validate_limit(self, limit: int) -> int:
        """Validates and clamps limit."""
        ...
```

## Single Responsibility Per Class

Each class should have one clear purpose. Split large classes into focused collaborators.

```python
# Bad - multiple responsibilities
class UserManager:
    def create_user(self): ...
    def send_email(self): ...
    def generate_report(self): ...
    def backup_database(self): ...

# Good - focused classes
class UserService:
    def create_user(self): ...

class EmailService:
    def send_email(self): ...

class ReportGenerator:
    def generate_report(self): ...
```

## Dataclasses for Data Containers

Use dataclasses for classes that primarily hold data.

```python
# Bad - verbose boilerplate
class BacklinkItem:
    def __init__(self, url: str, score: int, anchor: str):
        self.url = url
        self.score = score
        self.anchor = anchor

# Good - dataclass
@dataclass
class BacklinkItem:
    url: str
    score: int
    anchor: str
```

## Frozen Dataclasses for Immutability

Use `frozen=True` for value objects that shouldn't change.

```python
@dataclass(frozen=True)
class Target:
    url: str
    scope: UrlScope
```

## Protocol for Interfaces

Use `Protocol` instead of abstract base classes when you only need structural typing.

```python
# Good - protocol defines interface
class Cache(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any) -> None: ...

# Any class with these methods satisfies the protocol
class RedisCache:
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any) -> None: ...

class InMemoryCache:
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any) -> None: ...
```

