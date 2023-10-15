import asyncio
import random
import re
import time
from ast import parse
from operator import le
from typing import Callable

import requests
from asyncer import asyncify
from loguru import logger
from requests.adapters import HTTPAdapter, Retry
from tqdm.asyncio import tqdm

from .utils import (
    extend_list,
    get_user_agents,
    get_webshare_proxies_list,
    to_list,
    unnest_results,
)


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
        cookies: dict | None = None,
    ) -> None:
        self._concurrency = concurrency
        self._random_user_agent = random_user_agent
        self._random_proxy = random_proxy
        self._max_retries = max_retries
        self._random_delay_multiplier = random_delay_multiplier
        self._cookies = cookies
        self._parse_func = None

        self._adapter = HTTPAdapter(
            pool_connections=concurrency,
            pool_maxsize=0,
            max_retries=Retry(
                total=max_retries, backoff_factor=random_delay_multiplier * 0.1
            ),
        )
        self._semaphore = asyncio.Semaphore(concurrency)
        self._session = requests.Session()
        self._session.mount("http://", self._adapter)
        self._session.mount("https://", self._adapter)

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

    def single_request(
        self,
        url: str,
        method: str = "GET",
        key: str | None = None,
        params: dict | None = None,
        data: dict | str | None = None,
        json: dict | None = None,
        headers: str | None = None,
        debug: bool = False,
        warnings: bool = False,
        return_type: str | None = None,
        parse_func: Callable | None = None,
        *args,
        **kwargs,
    ) -> dict | str | None:
        if self._random_proxy and self._proxies is not None:
            proxy = random.choice(self._proxies)
            proxies = {"http://": proxy, "https://": proxy}
        else:
            proxy = None
            proxies = None
        if debug:
            logger.debug(
                f"""{self._max_retries}  {method} request | url: {url}, params: {params}, headers: {headers}, proxy: {proxy}, key: {key}"""
            )
        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json,
                proxies=proxies,
                headers=headers,
                cookies=self._cookies,
                *args,
                **kwargs,
            )
            response.raise_for_status()

            if return_type == "json":
                result = response.json()

            elif return_type == "text":
                result = response.text

            elif return_type == "content":
                result = response.content

            else:
                result = response

            if parse_func:
                result = parse_func(result)

            return {key: result} if key else result

        except Exception as e:
            if warnings:
                logger.warning(
                    f"""{self._max_retries} failed {method} request with Exception {e} - url: {url}, params: {params}, headers: {headers}, proxy: {proxy}"""
                )
            logger.exception(e)

        return {key: None} if key else None

    async def single_request_async(
        self,
        url: str,
        method: str = "GET",
        key: str | None = None,
        params: dict | None = None,
        data: dict | str | None = None,
        json: dict | None = None,
        headers: dict | None = None,
        # proxy: str | None = None,
        debug: bool = False,
        warnings: bool = False,
        return_type: str | None = None,
        parse_func: Callable | None = None,
        *args,
        **kwargs,
    ) -> dict | str | None:
        async with self._semaphore:
            return await asyncify(self.single_request)(
                url=url,
                method=method,
                key=key,
                params=params,
                data=data,
                json=json,
                headers=headers,
                debug=debug,
                warnings=warnings,
                return_type=return_type,
                parse_func=parse_func,
                *args,
                **kwargs,
            )

    async def request_async(
        self,
        urls: str | list,
        keys: str | list | None = None,
        params: dict | list | None = None,
        data: dict | str | list | None = None,
        json: dict | list | None = None,
        headers: dict | None = None,
        method: str = "GET",
        parse_func: Callable | None = None,
        return_type: str = None,
        verbose: bool = True,
        debug: bool = False,
        warnings: bool = False,
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
                # kwargs.pop(kw)

        urls = to_list(urls)
        params = to_list(params)
        data = to_list(data)
        json = to_list(json)
        keys = to_list(keys)
        headers = to_list(headers)
        # proxies = to_list(self._proxies) if self._random_proxy else to_list(None)

        max_len = max([len(urls), len(params), len(keys), len(data), len(json)])

        urls = extend_list(urls, max_len)
        params = extend_list(params, max_len)
        data = extend_list(data, max_len)
        json = extend_list(json, max_len)
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

        tasks = [
            asyncio.create_task(
                self.single_request_async(
                    url=url_,
                    key=key_,
                    params=params_,
                    data=data_,
                    json=json_,
                    headers=headers_,
                    method=method,
                    return_type=return_type,
                    parse_func=parse_func,
                    # proxy=proxy,
                    debug=debug,
                    warnings=warnings,
                    *args,
                    **kwargs,
                )
            )
            for url_, key_, params_, data_, json_, headers_ in zip(
                urls, keys, params, data, json, headers
            )
        ]

        if verbose:
            results = [await task for task in tqdm.as_completed(tasks)]
        else:
            results = [await task for task in asyncio.as_completed(tasks)]

        if self._return_type == "json" or self._return_type == "text":
            results = unnest_results(results=results, keys=keys)

        return results


async def parallel_requests_async(
    urls: str | list,
    keys: str | list | None = None,
    params: dict | list | None = None,
    data: dict | str | list | None = None,
    json: dict | list | None = None,
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
    warnings: bool = False,
    cookies: dict | None = None,
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
        cookies=cookies,
    )
    # if isinstance(urls, str) or len(urls) == 1:

    #     if params is None or isinstance(params, dict) or len(params or "") == 1:

    #         return await pr.single_request_async(
    #             url=urls,
    #             key=keys,
    #             params=params,
    #             headers=headers,
    #             method=method,
    #             #parse_func=parse_func,
    #             return_type=return_type,
    #             parse_func=parse_func,
    #             debug=debug,
    #             warnings=warnings,
    #             *args,
    #             **kwargs,
    #         )

    return await pr.request_async(
        urls=urls,
        keys=keys,
        params=params,
        data=data,
        json=json,
        headers=headers,
        method=method,
        parse_func=parse_func,
        verbose=verbose,
        return_type=return_type,
        debug=debug,
        warnings=warnings,
        *args,
        **kwargs,
    )


def parallel_requests(
    urls: str | list,
    keys: str | list | None = None,
    params: dict | list | None = None,
    data: dict | str | list | None = None,
    json: dict | list | None = None,
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
    warnings: bool = False,
    cookies: dict | None = None,
    *args,
    **kwargs,
):
    return asyncio.run(
        parallel_requests_async(
            urls=urls,
            keys=keys,
            params=params,
            data=data,
            json=json,
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
            warnings=warnings,
            cookies=cookies,
            *args,
            **kwargs,
        )
    )
