from parallel_requests.exceptions import (
    ConfigurationError,
    FailureDetails,
    ParallelRequestsError,
    PartialFailureError,
    ProxyError,
    RateLimitExceededError,
    RetryExhaustedError,
    ValidationError,
    BackendError,
)
from parallel_requests.config import GlobalConfig
from parallel_requests.backends.base import Backend, NormalizedResponse, RequestConfig
from parallel_requests.client import (
    ParallelRequests,
    RequestOptions,
    ReturnType,
    parallel_requests,
    parallel_requests_async,
)

__version__ = "2.0.0"

__all__ = [
    "__version__",
    "ParallelRequestsError",
    "BackendError",
    "ProxyError",
    "RetryExhaustedError",
    "RateLimitExceededError",
    "ValidationError",
    "ConfigurationError",
    "PartialFailureError",
    "FailureDetails",
    "GlobalConfig",
    "Backend",
    "RequestConfig",
    "NormalizedResponse",
    "ParallelRequests",
    "RequestOptions",
    "ReturnType",
    "parallel_requests",
    "parallel_requests_async",
]
