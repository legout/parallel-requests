import niquests
import asyncio
import random
from loguru import logger
from niquests.adapters import Retry
from niquests import Response
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
        backoff_factor: int = 0.05,
        backoff_max: int = 10,
        backoff_jitter: float = 0.1,
        random_proxy: bool = False,
        random_user_agent: bool = True,
        proxies: list | str | None = None,
        user_agents: list | str | None = None,
        cookies: dict | None = None,
        verbose: bool = True,
        debug: bool = False,
        warnings: bool = False,
    ) -> None:
        self._concurrency = concurrency
        self._random_user_agent = random_user_agent
        self._random_proxy = random_proxy
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._backoff_jitter = backoff_jitter
        self._backoff_max = backoff_max
        self._cookies = cookies
        self._parse_func = None
        self._debug = debug
        self._warnings = warnings
        self._verbose = verbose

        self._semaphore = asyncio.Semaphore(concurrency)

        self._session = niquests.AsyncSession(
            pool_connections=concurrency * 2,
            # pool_maxsize=0,
            retries=Retry(
                total=max_retries,
                backoff_factor=backoff_factor,
                backoff_max=backoff_max,
                backoff_jitter=backoff_jitter,
            ),
        )

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

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()
        return False

    async def close(self):
        """Close the underlying session."""
        await self._session.close()

    async def _request(
        self,
        url: str,
        method: str = "GET",
        key: str | None = None,
        params: dict | None = None,
        data: dict | str | None = None,
        json: dict | None = None,
        headers: str | None = None,
        proxies: dict | None = None,
        # return_type: str | None = None,
        # parse_func: Callable | None = None,
        *args,
        **kwargs,
    ) -> Response:
        if self._debug:
            logger.debug(
                f"""
                {self._max_retries}  {method} request | 
                url: {url}, 
                params: {params}, 
                headers: {headers}, 
                proxy: {proxies["http"]}, 
                key: {key}
                """
            )
        try:
            response = await self._session.request(
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

            return {key: response} if key else response

        except Exception as e:
            if self._warnings:
                logger.warning(
                    f"{self._max_retries} failed {method} request with Exception {e} - "
                    "url: {url}, "
                    "params: {params}, "
                    "headers: {headers}, "
                    "proxy: {proxies['http']}, "
                    "key: {key}"
                )
                logger.exception(e)

        return {key: None} if key else None

    async def request(
        self,
        urls: str | list,
        keys: str | list | None = None,
        params: dict | list | None = None,
        data: dict | str | list | None = None,
        json: dict | list | None = None,
        headers: dict | None = None,
        method: str = "GET",
        # parse_func: Callable | None = None,
        # return_type: str = None,
        *args,
        **kwargs,
    ) -> list[Response]:
        urls = to_list(urls)
        params = to_list(params)
        data = to_list(data)
        json = to_list(json)
        keys = to_list(keys)
        headers = to_list(headers)

        max_len = max([len(urls), len(params), len(keys), len(data), len(json)])

        urls = extend_list(urls, max_len)
        params = extend_list(params, max_len)
        data = extend_list(data, max_len)
        json = extend_list(json, max_len)
        keys = extend_list(keys, max_len)
        headers = extend_list(headers, max_len)

        if self._random_proxy and self._proxies:
            random.shuffle(self._proxies)
            proxies = extend_list(
                [{"http": proxy, "https": proxy} for proxy in self._proxies], max_len
            )
        else:
            proxies = extend_list([{"http": None, "https": None}], max_len)

        if self._random_user_agent and self._user_agents:
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

        tasks = []

        for url, key, param, d, j, h, p in zip(urls, keys, params, data, json, headers, proxies):
            tasks.append(
                asyncio.create_task(
                    self._request(
                        url=url,
                        method=method,
                        key=key,
                        params=param,
                        data=d,
                        json=j,
                        headers=h,
                        proxies=p,
                        *args,
                        **kwargs,
                    )
                )
            )
        if self._verbose:
            responses = [await task for task in tqdm.as_completed(tasks)]
        else:
            responses = [await task for task in asyncio.as_completed(tasks)]

        responses = unnest_results(results=responses, keys=keys)

        return responses
