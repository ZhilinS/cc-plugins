# Method Structure

## Final Local Variables and Parameters

All local variables and method parameters must be `final`. This makes intent explicit — the reader immediately knows nothing gets reassigned.

```java
// Bad - unclear what might be reassigned later
public Order process(Order order, int discount) {
    var price = order.subtotal() - discount;
    var result = new Order(order.id(), price);
    return result;
}

// Good - final signals "this won't change"
public Order process(final Order order, final int discount) {
    final var price = order.subtotal() - discount;
    final var result = new Order(order.id(), price);
    return result;
}
```

Branching with if/else assigns to the variable exactly once, so it stays `final`:

```java
// Good - final even with branching
public Result process(final Data data) {
    final Result result;
    if (data.isValid()) {
        result = Result.complete(data);
    } else {
        result = Result.invalid();
    }
    return result;
}
```

## No Empty Lines Inside Methods

Method bodies should have no blank lines. If you feel the need for a visual separator, the method is doing too much — extract a helper instead.

```java
// Bad - empty lines break the flow
public Order process(final Order order) {
    final var validated = validate(order);

    final var enriched = enrich(validated);

    final var saved = save(enriched);
    return saved;
}

// Good - no empty lines, continuous flow
public Order process(final Order order) {
    final var validated = validate(order);
    final var enriched = enrich(validated);
    final var saved = save(enriched);
    return saved;
}
```

## Single Responsibility

A method should do one thing. If the name needs "and" to describe it, split it.

```java
// Bad - two concerns in one method
private Data fetchAndCache(String url) {
    var response = client.get(url);
    var data = parse(response);
    cache.put(url, data);
    return data;
}

// Good - separate concerns, compose at call site
private Data fetch(String url) {
    var response = client.get(url);
    return parse(response);
}

private Data cache(String url, Data data) {
    cache.put(url, data);
    return data;
}

// Usage: compose operations
var data = cache(url, fetch(url));
```

Or use a wrapper pattern:

```java
// Good - caching wraps fetching, single return
public Data data(String url) {
    var result = cache.get(url);
    if (result == null) {
        result = fetch(url);
        cache.put(url, result);
    }
    return result;
}
```

## Method Length

Keep methods short (15-20 lines max) so the method signature stays visible on screen.

**Why it matters:** Generic variable names like `request`, `items`, `result` get their meaning from the method name. When the method fits on one screen, the reader always sees `fetchBacklinks` at the top, which tells them `request` is a backlinks request.

```java
// Good - short method, context always visible
private List<BacklinkItem> fetchBacklinks(String url) {
    var request = buildRequest(url);
    return client.query(request).stream()
        .map(this::convertBacklink)
        .toList();
}
```

Long methods force scrolling. Once the method signature scrolls off screen, variable names lose their context.

```java
// Bad - 50+ line method, reader scrolls and forgets context
private List<BacklinkItem> fetchBacklinks(String url) {
    // ... 20 lines of setup ...
    var request = buildRequest(url);  // What kind of request? Can't see method name
    // ... 30 more lines ...
}
```

**Rule:** If a method is too long for generic names to be clear, the method is too long. Extract helpers.

## Extract When

Extract a helper method when:

1. **Logic is reused** - Same code appears in multiple places
2. **Logic is complex** - More than 3-5 lines doing one conceptual thing
3. **Logic needs a name** - The operation deserves explanation

```java
// Before - inline complexity
public Result processOrder(Order order) {
    for (var item : order.items()) {
        var stock = inventory.stock(item.sku());
        if (stock < item.quantity()) {
            throw new InsufficientStockException(item.sku());
        }
    }
    var subtotal = order.items().stream()
        .mapToDouble(i -> i.price() * i.quantity())
        .sum();
    var tax = subtotal * taxRate;
    var total = subtotal + tax;
    ...
}

// After - named operations
public Result processOrder(Order order) {
    validateInventory(order.items());
    var total = calculateTotal(order.items());
    return createCharge(order, total);
}
```

## Don't Extract When

Don't extract if it just moves code without adding clarity:

```java
// Bad - extraction adds no value
private long userId() {
    return user.id();
}

// Just use directly
var userId = user.id();
```

Don't extract single-use code that's already clear:

```java
// Bad - unnecessary extraction
private String buildGreeting(String name) {
    return "Hello, " + name;
}

public void greet(String name) {
    System.out.println(buildGreeting(name));
}

// Good - inline is clearer
public void greet(String name) {
    System.out.println("Hello, " + name);
}
```

## Single Return Per Method

Each method should have one return statement at the end. Build up the result through the method body and return it once. This makes the flow linear and easy to follow.

```java
// Bad - multiple returns scattered throughout
public Result process(Data data) {
    if (!data.isValid()) {
        return Result.invalid();
    }
    if (data.needsTransform()) {
        var transformed = transform(data);
        if (!transformed.isComplete()) {
            return Result.partial(transformed);
        }
        return Result.complete(transformed);
    }
    return Result.complete(data);
}

// Good - single return, linear flow
public Result process(Data data) {
    final Result result;
    if (!data.isValid()) {
        result = Result.invalid();
    } else {
        final Data toFinalize;
        if (data.needsTransform()) {
            toFinalize = transform(data);
        } else {
            toFinalize = data;
        }
        if (toFinalize.isComplete()) {
            result = Result.complete(toFinalize);
        } else {
            result = Result.partial(toFinalize);
        }
    }
    return result;
}
```

For validation, throw exceptions instead of returning early — they're not returns, they're exceptional exits:

```java
// Good - exception is not a return, single return at the end
public Order processOrder(Order order) {
    if (!order.isValid()) {
        throw new InvalidOrderException(order.id());
    }
    var validated = validate(order);
    var enriched = enrich(validated);
    var saved = save(enriched);
    return saved;
}
```

## Flatten with If-Else and Pipelines

Avoid deep nesting by using if-else assignments, pipelines, and extracted methods to keep the flow flat. Always use `if` statements — never ternary operators.

```java
// Bad - deeply nested conditionals with multiple returns
public Price calculate(Order order) {
    if (order.hasDiscount()) {
        if (order.discount().type() == DiscountType.PERCENTAGE) {
            return new Price(order.subtotal() * (1 - order.discount().value()));
        } else {
            return new Price(order.subtotal() - order.discount().value());
        }
    } else {
        return new Price(order.subtotal());
    }
}

// Good - flat with if-else, single return
public Price calculate(Order order) {
    final double discount;
    if (order.hasDiscount()) {
        discount = applyDiscount(order.subtotal(), order.discount());
    } else {
        discount = 0.0;
    }
    return new Price(order.subtotal() - discount);
}
```

## Use Switch Expressions for Branching

Prefer switch expressions over if-else chains when mapping a value to an outcome. Switch expressions are exhaustive (compiler enforces all cases) and return a value directly.

```java
// Bad - if-else chain, easy to miss a case
public double discount(CustomerTier tier) {
    if (tier == CustomerTier.BRONZE) {
        return 0.05;
    } else if (tier == CustomerTier.SILVER) {
        return 0.10;
    } else if (tier == CustomerTier.GOLD) {
        return 0.15;
    } else {
        return 0.0;
    }
}

// Good - switch expression, exhaustive and concise
public double discount(CustomerTier tier) {
    return switch (tier) {
        case BRONZE -> 0.05;
        case SILVER -> 0.10;
        case GOLD   -> 0.15;
    };
}
```

Works well with sealed interfaces for complex branching:

```java
public sealed interface PaymentResult permits Approved, Declined, PendingReview {}

public String message(PaymentResult result) {
    return switch (result) {
        case Approved a   -> "Payment of %s confirmed".formatted(a.amount());
        case Declined d   -> "Declined: %s".formatted(d.reason());
        case PendingReview p -> "Under review, ref: %s".formatted(p.referenceId());
    };
}
```

When a case needs multiple statements, use a block with `yield`:

```java
public Order applyPromotion(Order order, PromoType promo) {
    var discount = switch (promo) {
        case PERCENTAGE -> order.subtotal() * 0.1;
        case FIXED_AMOUNT -> 10.0;
        case BUY_ONE_GET_ONE -> {
            var cheapest = order.items().stream()
                .mapToDouble(Item::price)
                .min()
                .orElse(0.0);
            yield cheapest;
        }
    };
    return order.withDiscount(discount);
}
```
