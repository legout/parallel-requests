import asyncio
import random
import time
from typing import Callable

import requests
import requests.adapters
from asyncer import asyncify
from loguru import logger
from tqdm.asyncio import tqdm

from .constants import PROXIES, USER_AGENTS
from .utils import random_proxy, random_user_agent


def _to_list(x: list | str) -> list:
    if isinstance(x, (str, dict)):
        return [x]
    elif x is None:
        return [None]
    else:
        return x


def _extend_list(x: list, max_len: int) -> list:
    if len(x) == 1:
        return x * max_len
    else:
        return x


def unnest_results(results: list, urls: list, keys: list):
    if keys[0] is not None and isinstance(results, dict):
        results = dict((k, _results[k]) for _results in results for k in _results)

    if keys[0] is not None and isinstance(results[0], dict):
        results = dict((k, _results[k]) for _results in results for k in _results)

    if len(urls) == 1 and isinstance(results, (list, tuple)):
        results = results[0]

    return results


def single_requests(
    session: requests.Session,
    url: str,
    method: str = "GET",
    params: dict | None = None,
    key: str | None = None,
    headers: dict | None = None,
    with_random_user_agent: bool = True,
    with_random_proxy: bool = True,
    parse_func: Callable | None = None,
    max_retries: int = 5,
    retry_delay_multiplier: int | float = 1,
) -> dict:
    if with_random_user_agent:
        user_agent = random_user_agent(USER_AGENTS)
        if headers:
            headers.update(user_agent)
        else:
            headers = user_agent

    proxies = random_proxy(PROXIES, as_dict=True) if with_random_proxy else None

    tries = 0
    try:
        while tries < max_retries:
            try:
                resp = session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    proxies=proxies,
                )
                if resp.status_code < 300:
                    res = resp.json()

                    if parse_func is not None:
                        res = (
                            parse_func(key, res) if key is not None else parse_func(res)
                        )

                    return {key: res} if key else resp

                else:
                    resp.raise_for_status()

            except Exception:
                # ogger.exception(f"Failed with Exception {e}", e)
                tries += 1
                time.sleep(random.random() * retry_delay_multiplier)
            # logger.info(f"Retrying. {tries}/{max_retries}")
    except Exception as e:
        logger.exception(
            f"Failed even after {max_retries} retries with Exception {e}", e
        )
    return {key: None} if key else None


async def parallel_requests_async(
    url: list | str,
    method: str = "GET",
    key: list | str | None = None,
    params: list | dict | None = None,
    headers: dict | None = None,
    with_random_user_agent: bool = True,
    with_random_proxy: bool = True,
    parse_func: Callable | None = None,
    max_retries: int = 5,
    limits_per_host: int = 10,
    retry_delay_multiplier: int | float = 1,
    verbose: bool = True,
) -> dict | list:
    url = _to_list(url)
    params = _to_list(params)
    key = _to_list(key)

    max_len = max([len(url), len(params), len(key)])

    url = _extend_list(url, max_len)
    params = _extend_list(params, max_len)
    key = _extend_list(key, max_len)

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=limits_per_host,
        pool_maxsize=limits_per_host,
        max_retries=max_retries,
    )
    session.mount("http://", adapter)
    logger.info(f"Starting {max_len} requests.")
    tasks = [
        asyncio.create_task(
            asyncify(single_requests)(
                session=session,
                method=method,
                url=url_,
                key=key_,
                params=params_,
                headers=headers,
                with_random_user_agent=with_random_user_agent,
                with_random_proxy=with_random_proxy,
                parse_func=parse_func,
                max_retries=max_retries,
                retry_delay_multiplier=retry_delay_multiplier,
            )
        )
        for url_, params_, key_ in zip(url, params, key)
    ]
    if verbose:
        results = [(await task) for task in tqdm.as_completed(tasks)]
    else:
        results = [(await task) for task in asyncio.as_completed(tasks)]
    logger.info(f"Finished {max_len} requests.")

    return unnest_results(results=results, urls=url, keys=key)


def parallel_requests(
    url: list | str,
    method: str = "GET",
    key: list | str | None = None,
    params: list | dict | None = None,
    headers: dict | None = None,
    with_random_user_agent: bool = True,
    with_random_proxy: bool = True,
    parse_func: Callable | None = None,
    max_retries: int = 5,
    limits_per_host: int = 10,
    verbose: bool = True,
) -> dict | list:
    return asyncio.run(
        parallel_requests_async(
            url=url,
            method=method,
            key=key,
            params=params,
            headers=headers,
            with_random_user_agent=with_random_user_agent,
            with_random_proxy=with_random_proxy,
            parse_func=parse_func,
            max_retries=max_retries,
            limits_per_host=limits_per_host,
            verbose=verbose,
        )
    )
