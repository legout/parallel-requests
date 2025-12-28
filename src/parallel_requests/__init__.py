from parallel_requests.constants import PROXIES, USER_AGENTS, update_user_agents
from parallel_requests.parallel_requests_asyncer import ParallelRequests
from parallel_requests.parallel_requests_asyncer import (
    parallel_requests as parallel_requests,
)
from parallel_requests.parallel_requests_asyncer import (
    parallel_requests_async as parallel_requests_async,
)

# from parallel_requests.parallel_requests_aiohttp import (
#    parallel_requests as parallel_requests_aiohttp,
#    parallel_requests_async as parallel_requests_aiohttp_async,
# )
from parallel_requests.utils import random_proxy, random_user_agent

__all__ = [
    "ParallelRequests",
    "parallel_requests",
    "parallel_requests_async",
    "random_proxy",
    "random_user_agent",
    "update_user_agents",
    "PROXIES",
    "USER_AGENTS",
]
