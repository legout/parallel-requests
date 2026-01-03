# Explanations

Explain **how things work** under the hood and **why** design decisions were made.

## What are Explanations?

Explanations provide in-depth understanding of the library's internal mechanics, design philosophy, and algorithms. Unlike tutorials (which teach you how to do something) or how-to guides (which provide step-by-step solutions), explanations focus on the "why" and "how it works."

## Documentation Types

| Type | Purpose | Example |
|------|---------|---------|
| **Tutorials** | Learning-oriented, step-by-step lessons | "Make your first parallel request" |
| **How-to Guides** | Problem-solving, practical solutions | "Handle rate limits for an API" |
| **Reference** | Technical details, API documentation | `FastRequests` class parameters |
| **Explanations** | Understanding internal design | "Why token bucket for rate limiting?" |

## When to Consult Explanations

Consult explanations when you want to understand:

- **Design decisions** - Why certain algorithms or patterns were chosen
- **Internal mechanics** - How features work under the hood
- **Trade-offs** - Benefits and limitations of different approaches
- **Performance characteristics** - How different backends or settings affect performance
- **Algorithm details** - Mathematical formulas or implementation details

## Explanation Topics

### Architecture
**[Architecture](architecture.md)** - Design philosophy, component overview, and how parts interact

### Backends
**[Backends](backends.md)** - HTTP client library comparison, auto-detection, and when to use each

### Rate Limiting
**[Rate Limiting](rate-limiting.md)** - Token bucket algorithm, burst handling, and concurrency control

### Retry Strategy
**[Retry Strategy](retry-strategy.md)** - Exponential backoff, jitter, and thundering herd prevention

### Proxy Rotation
**[Proxy Rotation](proxy-rotation.md)** - IP rotation, proxy validation, and health tracking

## Related Documentation

- **[Tutorials](../tutorials/index.md)** - Start here for hands-on learning
- **[How-to Guides](../how-to-guides/index.md)** - Practical solutions to common problems
- **[Reference](../reference/index.md)** - Complete API documentation
