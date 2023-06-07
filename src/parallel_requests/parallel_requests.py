import asyncio
import os
import random
import time
from typing import Callable

import aiohttp
from loguru import logger
from tqdm.asyncio import tqdm

from .utils import extend_list, get_user_agents, get_webshare_proxies_list
from .utils import random_proxy as random_proxy_
from .utils import random_user_agent as random_user_agent_
from .utils import to_list, unnest_results


class ParallelRequests:
    def __init__(
        self,
        concurrency: int = 100,
        max_retries: int = 5,
        random_delay_multiplier: int = 1,
        random_proxy: bool = False,
        random_user_agent: bool = True,
        proxies: list | str | None = None, 
        user_agents: list | str | None = None
    ) -> None:
        self._concurrency = concurrency
        self._random_user_agent = random_user_agent
        self._random_proxy = random_proxy
        self._max_retries = max_retries
        self._random_delay_multiplier = random_delay_multiplier

        self._conn = aiohttp.TCPConnector(limit_per_host=concurrency, limit=concurrency)
        self._semaphore = asyncio.Semaphore(concurrency)

        self.set_proxies(proxies=proxies)
        self.set_user_agents(user_agents=user_agents)

    def set_proxies(self, proxies: list | str | None = None):
        if not proxies:
            #from .config import PROXIES

            proxies = get_webshare_proxies_list()
        self._proxies = proxies

    def set_user_agents(self, user_agents: list | str | None = None):
        if not user_agents:
            #from .config import USER_AGENTS

            user_agents = get_user_agents()

        self._user_agents = user_agents

    async def _single_request(
        self,
        url: str,
        method:str="GET",
        key: str | None = None,
        params: dict | None = None,
        headers:dict|None=None,
        proxy:str|None=None,
        *args,
        **kwargs,
    ) -> dict:  # sourcery skip: low-code-quality
        # if self._random_user_agent:
        #     user_agent = random_user_agent_(self._user_agents, as_dict=False)

        #     if self._headers:
        #         self._headers.update({"user-agent":self._user_agent})
        #     else:
        #         self._headers = {"user-agent":self._user_agent}
                

        # if self._random_proxy:
        #     if (
        #         self._proxies is None
        #         and os.getenv("WEBSHARE_PROXIES_URL", None) is not None
        #     ):
        #         self.set_proxies()

        #     proxy = random_proxy_(self._proxies, as_dict=False)

        # else:
        #     proxy = None

        async with self._semaphore:
            tries = 0
            while tries < self._max_retries:
                try:
                    async with self._session.request(
                        method=method,
                        url=url,
                        params=params,
                        proxy=proxy,
                        headers=headers,
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
                            f"""{self._max_retries} failed {method} request with Exception {e} - url: {url}, params: {params}, headers: {headers}, proxy: {proxy}"""
                        )
        self._proxy = proxy
        self._headers = headers
        self._key = key
        self._url = url
        self._params = params
        self._method = method
        
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

        max_len = max([len(urls), len(params), len(keys)])

        urls = extend_list(urls, max_len)
        params = extend_list(params, max_len)
        keys = extend_list(keys, max_len)

        if self._random_user_agent:
            random.shuffle(self._user_agents)
            if not headers:
                headers = {}
            headers = [dict({"user-agent": user_agent}, **headers) for user_agent in self._user_agents[:len(urls)]]
            
        if self._random_proxy:
            proxies = random.shuffle(self._proxies)[:len(urls)]
            
        self._parse_func = parse_func
        self._return_type = return_type


        async with aiohttp.ClientSession(connector=self._conn) as self._session:
            tasks = [
                asyncio.create_task(
                    self._single_request(
                        url=url_, key=key_, params=params_, headers=headers_, method=method, proxy=proxy, *args, **kwargs
                    )
                )
                for url_, key_, params_, headers_, proxy in zip(urls, keys, params, headers, proxies)
            ]

            if verbose:
                results = [await task for task in tqdm.as_completed(tasks)]
            else:
                results = [await task for task in asyncio.as_completed(tasks)]
        # print(keys)
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
    *args,
    **kwargs,
):
    pr = ParallelRequests(
        concurrency=concurrency,
        max_retries=max_retries,
        random_delay_multiplier=random_delay_multiplier,
        random_proxy=random_proxy,
        random_user_agent=random_user_agent,
    )
    if (proxies is not None) & (random_proxy):
        pr.set_proxies(proxies=proxies)

    if (user_agents is not None) & (random_user_agent):
        pr.set_user_agents(user_agents=user_agents)

    results = await pr.request(
        urls=urls,
        keys=keys,
        params=params,
        headers=headers,
        method=method,
        parse_func=parse_func,
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
    verbose: bool = True,
    concurrency: int = 100,
    max_retries: int = 5,
    random_delay_multiplier: int = 1,
    random_proxy: bool = False,
    random_user_agent: bool = True,
    proxies: list | str | None = None,
    user_agents: list | None = None,
    *args,
    **kwargs,
):
    results = asyncio.run(
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
            *args,
            **kwargs,
        )
    )

    return results
