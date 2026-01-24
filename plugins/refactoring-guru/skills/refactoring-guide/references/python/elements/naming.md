# Naming Rules

## Context Gives Meaning to Generic Names

The function/method context provides meaning to local variables. Generic names like `request`, `items`, `result`, `data` are clear when the surrounding function name establishes context.

```python
# Good - function context makes generic names clear
async def _fetch_backlinks(self, url: str) -> list[BacklinkItem]:
    request = self._build_request(url)  # Clearly a backlinks request
    items = []                          # Clearly backlink items
    async for item in self._stub.Backlinks(request):
        items.append(self._convert(item))
    return items

async def _fetch_users(self, org_id: int) -> list[User]:
    request = self._build_request(org_id)  # Clearly a users request
    items = []                             # Clearly user items
    async for item in self._stub.Users(request):
        items.append(self._convert(item))
    return items
```

The same `request` and `items` names work in both functions because the function name (`_fetch_backlinks` vs `_fetch_users`) provides the context.

## When Generic Names Fail

Generic names become unclear when the function itself is generic or does multiple things.

```python
# Bad - function name doesn't establish context
def process(data):
    result = transform(data)
    temp = validate(result)
    return temp

# Good - specific function name + generic locals work
def process_order(order: Order) -> ProcessedOrder:
    validated = validate(order)      # Clear: validating the order
    enriched = enrich(validated)     # Clear: enriching the validated order
    return ProcessedOrder(enriched)

# Also good - when function is truly generic, qualify the names
def process_entity(entity: Entity, entity_type: str) -> ProcessedEntity:
    if entity_type == "order":
        order_data = extract_order_data(entity)
        return process_order_data(order_data)
    elif entity_type == "user":
        user_data = extract_user_data(entity)
        return process_user_data(user_data)
```

## Boolean Variables and Methods

Boolean names should read naturally. Adjectives work as-is. For verbs, use prefixes that form questions.

```python
# Good - adjectives work without prefix
active = True
visible = False
enabled = True

# Good - verb prefixes form natural questions
def has_permission() -> bool: ...    # "has permission?" - natural
def should_retry() -> bool: ...      # "should retry?" - natural
def can_edit() -> bool: ...          # "can edit?" - natural

# Awkward - is_ prefix often redundant with adjectives
is_active = True      # "is active" vs "active" - both clear
is_visible = False    # prefix adds little value

# Bad - unclear boolean intent
def check_permission(): ...   # Returns bool? Raises? Unclear
def permission(): ...         # Not obviously boolean
```

**Rule:** If the name reads as a yes/no question without a prefix, skip the prefix.

## Collection Plurals

Use plural names for collections. Use singular for individual items.

```python
# Bad
user_list = fetch_users()
for u in user_list: ...

# Good
users = fetch_users()
for user in users:
    process(user)
```

## Constants in SCREAMING_SNAKE_CASE

Module-level constants use uppercase with underscores.

```python
# Good
DEFAULT_LIMIT = 10
MAX_RETRIES = 3
API_TIMEOUT_SECONDS = 30
```

## Private Names with Single Underscore

Use single underscore prefix for private methods and attributes.

```python
# Good
class Service:
    def __init__(self):
        self._cache = {}  # Private attribute

    def data(self):  # Public method
        return self._load()

    def _load(self):  # Private method
        ...
```

## Avoid Abbreviations

Use full words except for universally known abbreviations (URL, HTTP, ID, API).

```python
# Bad
def usr_info(usr_id): ...
def calc_ttl_amt(): ...

# Good
def user_info(user_id: int): ...
def calculate_total_amount(): ...

# OK - universal abbreviations
def fetch_url(url: str): ...
def api_key(): ...
```

## Method Naming by Action

Method names should indicate their action clearly.

**Simple getters:** Use the field name directly, no prefix needed.

```python
# Bad - redundant prefix
def get_user(self) -> User: ...
def get_config(self) -> Config: ...

# Good - name is what it returns
def user(self) -> User: ...
def config(self) -> Config: ...
```

**Action methods:** Use prefixes that describe the action.

| Prefix | Meaning | Example |
|--------|---------|---------|
| `fetch_` | Retrieve from external source | `fetch_user()` |
| `create_` | Create and return new instance | `create_order()` |
| `build_` | Construct from parts | `build_request()` |
| `parse_` | Extract structure from raw | `parse_response()` |
| `validate_` | Check and return valid/raise | `validate_input()` |
| `convert_` | Transform between types | `convert_to_dto()` |
| `handle_` | Process/react to something | `handle_error()` |

## Type Alias Names

Use PascalCase for type aliases. Make them descriptive.

```python
# Good
UserId = int
SortDirection = Literal['asc', 'desc']
BacklinkItems = list[BacklinkItem]
JsonDict = dict[str, Any]
```
