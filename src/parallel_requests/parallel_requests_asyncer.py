import asyncio
import random
import time
from typing import Callable

import requests
from asyncer import asyncify
from loguru import logger
from requests.adapters import HTTPAdapter, Retry
from tqdm.asyncio import tqdm

from .utils import (extend_list, get_user_agents, get_webshare_proxies_list,
                    to_list, unnest_results)


class ParallelRequests:
    def __init__(
        self,
        concurrency: int = 100,
        max_retries: int = 5,
        random_delay_multiplier: int = 1,
        random_proxy: bool = False,
        random_user_agent: bool = True,
        proxies: list | str | None = None,
        user_agents: list | str | None = None,
        cookies:dict|None=None
    ) -> None:
        self._concurrency = concurrency
        self._random_user_agent = random_user_agent
        self._random_proxy = random_proxy
        self._max_retries = max_retries
        self._random_delay_multiplier = random_delay_multiplier
        self._cookies=cookies

        self._adapter = HTTPAdapter(
            pool_connections=concurrency,
            pool_maxsize=0,
            max_retries=Retry(
                total=max_retries, backoff_factor=random_delay_multiplier * 0.1
            ),
        )
        self._semaphore = asyncio.Semaphore(concurrency)

        self.set_proxies(proxies=proxies)
        self.set_user_agents(user_agents=user_agents)

    def set_proxies(self, proxies: list | str | None = None):
        if not proxies:
            # from .config import PROXIES

            proxies = get_webshare_proxies_list()

        proxies = proxies if proxies is not None else [None]
        self._proxies = proxies

    def set_user_agents(self, user_agents: list | str | None = None):
        if not user_agents:
            # from .config import USER_AGENTS

            user_agents = get_user_agents()

        self._user_agents = user_agents

    async def _single_request(
        self,
        url: str,
        method: str = "GET",
        key: str | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        # proxy: str | None = None,
        debug: bool = False,
        *args,
        **kwargs,
    ) -> dict:
        async with self._semaphore:
            if self._random_proxy and self._proxies is not None:
                proxy = random.choice(self._proxies)
                proxies = {"http://": proxy, "https://":proxy}
            else:
                proxy=None
                proxies = None
            if debug:
                logger.debug(
                    f"""{self._max_retries}  {method} request | url: {url}, params: {params}, headers: {headers}, proxy: {proxy}, key: {key}"""
                )
            try:
                response = await asyncify(self._session.request)(
                    method=method,
                    url=url,
                    params=params,
                    proxies=proxies,
                    headers=headers,
                    cookies=self._cookies,
                    *args,
                    **kwargs,
                )

                if self._return_type == "json":
                    result = response.json()

                elif self._return_type == "text":
                    result = response.text()

                else:
                    result = response.read()

                if self._parse_func:
                    result = self._parse_func(result)

                return {key: result} if key else result

            except Exception as e:
                logger.warning(
                    f"""{self._max_retries} failed {method} request with Exception {e} - url: {url}, params: {params}, headers: {headers}, proxy: {proxy}"""
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
        verbose: bool = True,
        debug: bool = False,
        *args,
        **kwargs,
    ) -> dict | list:
        for kw in kwargs:
            if kw in (
                "concurrency",
                "max_retries",
                "random_delay_mutliplier",
                "random_proxy",
                "random_user_agent",
            ):
                exec(f"self._{kw} = kwargs['{kw}']")
                kwargs.pop(kw)

        urls = to_list(urls)
        params = to_list(params)
        keys = to_list(keys)
        headers = to_list(headers)
        # proxies = to_list(self._proxies) if self._random_proxy else to_list(None)

        max_len = max([len(urls), len(params), len(keys)])

        urls = extend_list(urls, max_len)
        params = extend_list(params, max_len)
        keys = extend_list(keys, max_len)
        headers = extend_list(headers, max_len)
        # proxies = extend_list(proxies, max_len)

        if self._random_user_agent:
            random.shuffle(self._user_agents)

            headers = (
                [
                    dict({"user-agent": user_agent}, **headers_)
                    for headers_, user_agent in zip(
                        headers, extend_list(self._user_agents, max_len)
                    )
                ]
                if headers[0]
                else [
                    {"user-agent": user_agent}
                    for user_agent in extend_list(self._user_agents, max_len)
                ]
            )

        # if self._random_proxy:
        #     random.shuffle(self._proxies)

        self._parse_func = parse_func
        self._return_type = return_type
        with requests.Session() as self._session:
            self._session.mount("http://", self._adapter)
            tasks = [
                asyncio.create_task(
                    self._single_request(
                        url=url_,
                        key=key_,
                        params=params_,
                        headers=headers_,
                        method=method,
                        # proxy=proxy,
                        debug=debug,
                        *args,
                        **kwargs,
                    )
                )
                for url_, key_, params_, headers_ in zip(urls, keys, params, headers)
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
    verbose: bool = True,
    concurrency: int = 100,
    max_retries: int = 5,
    random_delay_multiplier: int = 1,
    random_proxy: bool = False,
    random_user_agent: bool = True,
    proxies: list | str | None = None,
    user_agents: list | None = None,
    debug: bool = False,
    cookies:dict|None=None,
    *args,
    **kwargs,
):
    pr = ParallelRequests(
        concurrency=concurrency,
        max_retries=max_retries,
        random_delay_multiplier=random_delay_multiplier,
        random_proxy=random_proxy,
        random_user_agent=random_user_agent,
        proxies=proxies,
        user_agents=user_agents,
        cookies=cookies
    )

    return await pr.request(
        urls=urls,
        keys=keys,
        params=params,
        headers=headers,
        method=method,
        parse_func=parse_func,
        verbose=verbose,
        return_type=return_type,
        debug=debug,
        *args,
        **kwargs,
    )


def parallel_requests(
    urls: str | list,
    keys: str | list | None = None,
    params: dict | list | None = None,
    headers: dict | None = None,
    method: str = "GET",
    parse_func: Callable | None = None,
    return_type: str = "json",
    verbose: bool = True,
    concurrency: int = 100,
    max_retries: int = 5,
    random_delay_multiplier: int = 1,
    random_proxy: bool = False,
    random_user_agent: bool = True,
    proxies: list | str | None = None,
    user_agents: list | None = None,
    debug: bool = False,
    cookies:dict|None=None,
    *args,
    **kwargs,
):
    return asyncio.run(
        parallel_requests_async(
            urls=urls,
            keys=keys,
            params=params,
            headers=headers,
            method=method,
            parse_func=parse_func,
            return_type=return_type,
            verbose=verbose,
            concurrency=concurrency,
            max_retries=max_retries,
            random_delay_multiplier=random_delay_multiplier,
            random_proxy=random_proxy,
            random_user_agent=random_user_agent,
            proxies=proxies,
            user_agents=user_agents,
            debug=debug,
            cookies=cookies,
            *args,
            **kwargs,
        )
    )
