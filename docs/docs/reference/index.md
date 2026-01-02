# Reference

Complete API reference and technical documentation for parallel-requests.

## Core API

Auto-generated API documentation using mkdocstrings:

- [ParallelRequests Class](api/parallelrequests.md) - Main client class
- [parallel_requests()](api/parallel_requests.md) - Synchronous convenience function
- [parallel_requests_async()](api/parallel_requests_async.md) - Async convenience function
- [ReturnType](api/returntype.md) - Response parsing options
- [GlobalConfig](api/globalconfig.md) - Global configuration

## Key Components

- [Return Types](return-types.md) - JSON, TEXT, CONTENT, RESPONSE, STREAM
- [Configuration](configuration.md) - Client parameters and environment variables
- [Exceptions](exceptions.md) - Exception hierarchy and error handling
- [Backend Interface](backend.md) - Backend abstraction and dataclasses

## Features

- [Rate Limiting](rate-limiting.md) - Token bucket algorithm
- [Retry Strategy](retry-strategy.md) - Exponential backoff with jitter
- [Proxy Rotation](proxy-rotation.md) - Proxy management and validation
- [Header Management](header-management.md) - User-agent rotation
- [Validation](validation.md) - Input validation functions
