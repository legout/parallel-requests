import asyncio
from typing import Callable
import aiohttp
import time
import random
from loguru import logger
from tqdm.asyncio import tqdm

from .utils import (
    random_proxy,
    random_user_agent,
    to_list,
    extend_list,
    unnest_results,
)


class ParallelRequests:
    def __init__(
        self,
        concurrency: int = 100,
        max_retries: int = 5,
        random_delay_multiplier: int = 1,
        with_random_proxy: bool = False,
        with_random_user_agent: bool = True,
    ) -> None:

        self._concurrency = concurrency
        self._with_random_user_agent = with_random_user_agent
        self._with_random_proxy = with_random_proxy
        self._max_retries = max_retries
        self._random_delay_multiplier = random_delay_multiplier

        self._conn = aiohttp.TCPConnector(limit_per_host=concurrency, limit=concurrency)
        self._semaphore = asyncio.Semaphore(concurrency)

        self.set_proxies()
        self.set_user_agents()

    def set_proxies(self, proxies: list | str | None = None):
        if not proxies:
            from .config import PROXIES

            proxies = PROXIES
        self._proxies = proxies

    def set_user_agents(self, user_agents: list | str | None = None):
        if not user_agents:
            from .config import USER_AGENTS

            user_agents = USER_AGENTS

        self._user_agents = user_agents

    async def _single_request(
        self,
        url: str,
        key: str | None = None,
        params: dict | None = None,
        *args,
        **kwargs,
    ) -> dict:

        if self._with_random_user_agent:
            user_agent = random_user_agent(self._user_agents, as_dict=True)

            if self._headers:
                self._headers.update(user_agent)
            else:
                self._headers = user_agent

        proxy = (
            random_proxy(self._proxies, as_dict=False)
            if self._with_random_proxy
            else None
        )

        async with self._semaphore:
            tries = 0
            while tries < self._max_retries:
                try:
                    async with self._session.request(
                        method=self._method,
                        url=url,
                        params=params,
                        proxy=proxy,
                        headers=self._headers,
                        *args,
                        **kwargs,
                    ) as response:
                        if response.status < 300:
                            if self._return_type == "json":
                                result = await response.json(content_type=None)

                            elif self._return_type == "text":
                                result = await response.text()

                            else:
                                result = await response.read()

                            if self._parse_func:
                                result = self._parse_func(result)

                            return {key: result} if key else result

                        else:
                            response.raise_for_status()

                except Exception as e:

                    tries += 1
                    time.sleep(random.random() * self._random_delay_multiplier)

                    if tries == self._max_retries:
                        logger.warning(
                            f"""{self._max_retries} failed {self._method} request with Exception {e} - url: {url}, params: {params}, headers: {self._headers}, proxy: {proxy}"""
                        )

        return {key: None} if key else None

    async def request(
        self,
        urls: str | list,
        keys: str | list | None = None,
        params: dict | list | None = None,
        headers: dict | None = None,
        method: str = "GET",
        parse_func: Callable | None = None,
        return_type: str = "json",
        proxy: str | None = None,
        verbose: bool = True,
        *args,
        **kwargs,
    ) -> dict | list:

        urls = to_list(urls)
        params = to_list(params)
        keys = to_list(keys)

        max_len = max([len(urls), len(params), len(keys)])

        urls = extend_list(urls, max_len)
        params = extend_list(params, max_len)
        keys = extend_list(keys, max_len)

        self._parse_func = parse_func
        self._return_type = return_type
        self._proxy = proxy
        self._headers = headers
        self._method = method

        for kw in kwargs:
            if kw in (
                "concurrency",
                "max_retries",
                "random_delay_mutliplier",
                "with_random_proxy",
                "with_random_user_agent",
                "concurrency",
            ):
                exec(f"self._{kw} = kwargs['{kw}']")

        async with aiohttp.ClientSession(connector=self._conn) as self._session:
            tasks = [
                asyncio.create_task(
                    self._single_request(
                        url=url_, key=key_, params=params_, *args, **kwargs
                    )
                )
                for url_, key_, params_ in zip(urls, keys, params)
            ]

            if verbose:
                results = [await task for task in tqdm.as_completed(tasks)]
            else:
                results = [await task for task in asyncio.as_completed(tasks)]

        results = unnest_results(results=results, keys=keys)

        return results


async def parallel_requests_async(
    urls: str | list,
    keys: str | list | None = None,
    params: dict | list | None = None,
    headers: dict | None = None,
    method: str = "GET",
    parse_func: Callable | None = None,
    return_type: str = "json",
    proxy: str | None = None,
    verbose: bool = True,
    concurrency: int = 100,
    max_retries: int = 5,
    random_delay_multiplier: int = 1,
    with_random_proxy: bool = False,
    with_random_user_agent: bool = True,
    *args,
    **kwargs,
):
    pr = ParallelRequests(
        concurrency=concurrency,
        max_retries=max_retries,
        random_delay_multiplier=random_delay_multiplier,
        with_random_proxy=with_random_proxy,
        with_random_user_agent=with_random_user_agent,
    )

    results = await pr.request(
        urls=urls,
        keys=keys,
        params=params,
        headers=headers,
        method=method,
        parse_func=parse_func,
        proxy=proxy,
        verbose=verbose,
        return_type=return_type,
        *args,
        **kwargs,
    )

    return results


def parallel_requests(
    urls: str | list,
    keys: str | list | None = None,
    params: dict | list | None = None,
    headers: dict | None = None,
    method: str = "GET",
    parse_func: Callable | None = None,
    return_type: str = "json",
    proxy: str | None = None,
    verbose: bool = True,
    concurrency: int = 100,
    max_retries: int = 5,
    random_delay_multiplier: int = 1,
    with_random_proxy: bool = False,
    with_random_user_agent: bool = True,
    *args,
    **kwargs,
):
    pr = ParallelRequests(
        concurrency=concurrency,
        max_retries=max_retries,
        random_delay_multiplier=random_delay_multiplier,
        with_random_proxy=with_random_proxy,
        with_random_user_agent=with_random_user_agent,
    )

    results = asyncio.run(
        pr.request(
            urls=urls,
            keys=keys,
            params=params,
            headers=headers,
            method=method,
            parse_func=parse_func,
            proxy=proxy,
            verbose=verbose,
            return_type=return_type,
            *args,
            **kwargs,
        )
    )

    return results
