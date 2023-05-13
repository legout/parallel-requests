#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
@File    :   async_requests.py
@Time    :   2022/08/18 20:28:03
@Author  :   Volker Lorrmann
@Version :   0.1
@Contact :   volker.lorrmann@gmail.com
@License :   (C)Copyright 2020-2022, Volker Lorrmann
@Desc    :   None
"""

import asyncio
import aiohttp

# import backoff
import pandas as pd

from tenacity import retry, stop_after_attempt, wait_random
import progressbar

from typing import Callable
from .utils import random_user_agent, random_proxy

from async_requests.config import USER_AGENTS, PROXIES
from json import JSONDecodeError


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


# async def async_requests(
#     url: str | tuple | list,
#     params: dict | tuple | list | None = None,
#     key: str | int | tuple | list | None = None,
#     headers: dict | None = None,
#     parse_func: Callable | None = None,
#     sema: int = 50,
#     limits_per_host: int = 100,
#     method: str = "GET",
#     max_retries: int = 10,
#     max_time: int = 120,
#     return_type: str = "json",
#     proxy: str | None = None,
#     use_random_proxy: bool = False,
#     ssl: bool = True,
#     timeout: int = 30,
#     verbose: bool = True,
# ):

#     @backoff.on_exception(
#         backoff.expo,
#         aiohttp.ClientError,
#         max_time=max_time,
#         max_tries=max_retries,
#     )
#     async def _fetch_async(
#         method,
#         session,
#         sema,
#         url,
#         params,
#         key,
#         parse_func,
#         return_type,
#         headers,
#         proxy,
#         use_random_proxy,
#     ):
#         if use_random_proxy:
#             proxy = random_proxy()

#         if headers is None:
#             headers = random_user_agent()

#         async with sema, session.get(
#             url=url,
#             params=params,
#             headers=headers,
#             proxy=proxy,
#             timeout=timeout,
#         ) if method == "GET" else session.post(
#             url=url,
#             data=params,
#             headers=headers,
#             proxy=proxy,
#             timeout=timeout,
#         ) as response:

#             if return_type == "json":
#                 result = await response.json(content_type=None)

#             elif return_type == "text":
#                 result = await response.text()

#             else:
#                 result = await response.content()

#             if parse_func is not None:
#                 return (
#                     await parse_func(key, result)
#                     if key is not None
#                     else await parse_func(result)
#                 )
#             else:
#                 return {key: result} if key is not None else result

#     if isinstance(url, str):
#         url = [url]

#     if params is not None:
#         if isinstance(params, dict):
#             params = [params]
#     else:
#         params = [None]

#     if key is not None:
#         if isinstance(key, (str, int)):
#             key = [key]
#     else:
#         key = [None]

#     if len(url) == 1 and len(params) > 1:
#         url = url * len(params)
#     if len(params) == 1 and len(url) > 1:
#         params = params * len(url)
#     if len(key) < len(url):
#         key = key * len(url)

#     conn = aiohttp.TCPConnector(
#         limit_per_host=limits_per_host,
#         verify_ssl=ssl if not use_random_proxy else False,
#     )
#     sema_ = asyncio.Semaphore(sema)
#     timeout = aiohttp.ClientTimeout(total=timeout)

#     async with aiohttp.ClientSession(
#         connector=conn, trust_env=True, timeout=timeout
#     ) as session:
#         tasks = [
#             asyncio.create_task(
#                 _fetch_async(
#                     method=method,
#                     session=session,
#                     sema=sema_,
#                     url=url[n],
#                     params=params[n],
#                     key=key[n],
#                     parse_func=parse_func,
#                     headers=headers,
#                     return_type=return_type,
#                     proxy=proxy,
#                     use_random_proxy=use_random_proxy,
#                 )
#             )
#             for n in range(len(url))
#         ]
#         if verbose:
#             results = [
#                 await task
#                 for task in progressbar.progressbar(
#                     asyncio.as_completed(tasks), max_value=len(url)
#                 )
#             ]
#         else:
#             results = [await task for task in asyncio.as_completed(tasks)]

#     if key[0] is not None and isinstance(results, dict):
#         results = dict((k, _results[k]) for _results in results for k in _results)
#     if len(url) == 1 and isinstance(results, (list, tuple)):
#         results = results[0]

#     return results


# def requests(*args, **kwargs):
#     return asyncio.run(async_requests(*args, **kwargs))


# class AsyncRequests:
#     """A class used for asynchronous Http Requests."""

#     def __init__(
#         self,
#         headers: dict | None = None,
#         limits_per_host: int = 100,
#         semaphore: int = 100,
#         timeout: int = 120,
#         use_random_proxy: bool = False,
#     ):
#         """
#         Args:
#             headers (dict | None, optional): The request headers. Defaults to None.
#             semaphore (int, optional): The number of semaphores. Defaults to None.
#             timeout (int, optional): The request timeout. Defaults to None.
#             limits_per_host (int, optional): The limit number per host. Defaults to None.
#             use_random_proxy (bool, optional): Use a random proxy from list of proxies. Defaults to False.
#         """
#         self._semaphore = semaphore
#         self._timeout = timeout
#         self._limits_per_host = limits_per_host
#         self._headers = headers
#         self._use_random_proxy = use_random_proxy


async def async_requests(
    url: str | list | tuple,
    params: dict | list | tuple | None = None,
    data: dict | list | tuple | None = None,
    json: str | list | tuple | None = None,
    headers: dict = None,
    method: str = "GET",
    key: str | int | list | tuple | None = None,
    parse_func: Callable | None = None,
    limits_per_host: int = 50,
    semaphore: int = 50,
    max_tries: int = 5,
    max_time: int = 60,
    return_type: str = "json",
    ssl: bool = False,
    verbose: bool = True,
    timeout: int = 120,
    proxy: str | None = None,
    use_random_proxy: bool = False,
) -> dict | list | pd.DataFrame:
    """A function for asynchronous Http requests

    Args:
        url (str | list | tuple): The request url
        params (dict | list | tuple | None, optional): The request parameter. Defaults to None.
        data (dict | list | tuple | None, optional): The request data. Defaults to None.
        json (str | list | tuple | None, optional): The request json object. Defaults to None.
        headers (dict, optional): The request headers. Defaults to None.
        method (str, optional): he request method. Defaults to "GET".
        key (str | int | list | tuple | None, optional): A key to assign the request responses. Defaults to None.
        parse_func (callable, optional): A function for parsing the request responses. Defaults to None.
        limits_per_host (int, optional): The limit number per host. Defaults to 50.
        semaphore (int, optional): The number of semaphores. Defaults to 50.
        max_tries (int, optional): Number of maximum retries, if requests fails. Defaults to 5.
        max_time (int, optional): Number of maximum time for retries, if requests fails. Defaults to 60.
        return_type (str, optional):  Defines return type. Defaults to "json".
        ssl (bool, optional): Use ssl or not. Defaults to False.
        verbose (bool, optional): If True, a progressbar is displayed. Defaults to True.
        timeout (int, optional): The total request timeout. Defaults to 120.
        proxy (str | None, optional): proxy server. Defaults to None.
        use_random_proxy (bool, optional): Use a random proxy from list of proxies. Defaults to False.

    Raises:
        aiohttp.ClientError: Final Client Error, if request is not successful, due to a ClientError.
        aiohttp.ServerConnectionError: Final Client Error, if request is not successful, due to a ServerConnectionError.

    Returns:
        dict | list | pd.DataFrame: request response
    """

    # @backoff.on_exception(
    #     backoff.expo,
    #     aiohttp.ClientError,
    #     aiohttp.Server
    #     JSONDecodeError,
    #     max_time=max_time,
    #     max_tries=max_tries,
    # )
    @retry(wait=wait_random(1, 10), stop=stop_after_attempt(max_tries))
    async def _request(
        method: str,
        semaphore_: int,
        session: aiohttp.client.ClientSession,
        url: str,
        params: dict | None,
        data: dict | None,
        json: str | None,
        headers: dict | None,
        key: str | None,
        parse_func: Callable | None,
        return_type: str,
        proxy: str | None,
        use_random_proxy: bool,
    ) -> dict | str | list | pd.DataFrame:
        if headers is None:
            headers = random_user_agent(USER_AGENTS)

        if use_random_proxy:
            proxy = random_proxy(PROXIES)

        async with semaphore_, session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            proxy=proxy,
        ) as response:
            if response.status >= 400:
                raise aiohttp.ClientError(response.status)
            elif response.status >= 500:
                raise aiohttp.ServerConnectionError(response.status)

            if return_type == "json":
                result = await response.json(content_type=None)

            elif return_type == "text":
                result = await response.text()

            else:
                result = await response.read()

            if parse_func is not None:
                return (
                    await parse_func(key, result)
                    if key is not None
                    else await parse_func(result)
                )
            else:
                return {key: result} if key is not None else result

    url = _to_list(url)
    params = _to_list(params)
    data = _to_list(data)
    json = _to_list(json)
    key = _to_list(key)

    max_len = max([len(url), len(params), len(data), len(json), len(key)])

    url = _extend_list(url, max_len)
    params = _extend_list(params, max_len)
    data = _extend_list(data, max_len)
    json = _extend_list(json, max_len)
    key = _extend_list(key, max_len)

    timeout = aiohttp.ClientTimeout(total=timeout)
    conn = aiohttp.TCPConnector(limit_per_host=limits_per_host, verify_ssl=ssl)
    semaphore_ = asyncio.Semaphore(semaphore)

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        tasks = [
            asyncio.create_task(
                _request(
                    method=method,
                    semaphore_=semaphore_,
                    session=session,
                    url=url[n],
                    params=params[n],
                    data=data[n],
                    json=json[n],
                    headers=headers,
                    key=key[n],
                    parse_func=parse_func,
                    return_type=return_type,
                    proxy=proxy,
                    use_random_proxy=use_random_proxy,
                )
            )
            for n in range(len(url))
        ]

        if verbose:
            results = [
                await task
                for task in progressbar.progressbar(
                    asyncio.as_completed(tasks), max_value=len(url)
                )
            ]

        else:
            results = [await task for task in asyncio.as_completed(tasks)]

    if key[0] is not None and isinstance(results, dict):
        results = dict((k, _results[k]) for _results in results for k in _results)

    if key[0] is not None and isinstance(results[0], dict):
        results = dict((k, _results[k]) for _results in results for k in _results)

    if len(url) == 1 and isinstance(results, (list, tuple)):
        results = results[0]

    return results


def requests(*args, **kwargs):
    return asyncio.run(async_requests(*args, **kwargs))


# async def async_requests(
#     url: tp.Union[str, tuple, list],
#     headers: dict = None,
#     params: tp.Union[dict, tuple, list, None] = None,
#     data: tp.Union[dict, tuple, list, None] = None,
#     json: tp.Union[dict, tuple, list, None] = None,
#     key: tp.Union[str, int, tuple, list, None] = None,
#     parse_func: object = None,
#     method: str = "GET",
#     return_type: str = "json",
#     ssl: bool = False,
#     verbose: bool = True,
#     semaphore: int = 10,
#     timeout: int = 120,
#     proxy: str | None = None,
#     limits_per_host: int = 10,
#     use_random_proxy: bool = False,
# ) -> dict:
#     """A function for asynchronous Http requests.

#     Args:
#         url (tp.Union[str, tuple, list]): The request url.
#         params (tp.Union[dict, tuple, list, None], optional): The request parameter. Defaults to None.
#         data (tp.Union[dict, tuple, list, None], optional): The request data. Defaults to None.
#         json (tp.Union[dict, tuple, list, None], optional): The request json object. Defaults to None.
#         headers (dict, optional): The request headers. Defaults to None.
#         key (tp.Union[str, int, tuple, list, None], optional): A key to assign the request responses. Defaults to None.
#         parse_func (object, optional): A function for parsing the request responses. Defaults to None.
#         method (str, optional): The request method. Defaults to "GET".
#         return_type (str, optional): Defines return rype. Defaults to json.
#         ssl (bool, optional): Use ssl or not. Defaults to False.
#         verbose (bool, optional): If True, a progressbar is displayed. Defaults to False.
#         semaphore (int, optional): The number of semaphores. Defaults to None.
#         timeout (int, optional): The request timeout. Defaults to None.
#         limits_per_host (int, optional): The limit number per host. Defaults to None.
#         use_random_proxy (bool, optional): Use a random proxy from list of proxies. Defaults to False.

#     Returns:
#         Returns:
#             dict: Dictionary with the request response.
#     """
#     ar = AsyncRequests(
#         headers=headers,
#         semaphore=semaphore,
#         timeout=timeout,
#         limits_per_host=limits_per_host,
#         use_random_proxy=use_random_proxy,
#     )
#     return await ar.requests(
#         url=url,
#         params=params,
#         data=data,
#         json=json,
#         headers=headers,
#         proxy=proxy,
#         key=key,
#         parse_func=parse_func,
#         method=method,
#         return_type=return_type,
#         ssl=ssl,
#         verbose=verbose,
#     )


# def requests(
#     url: tp.Union[str, tuple, list],
#     headers: dict = None,
#     params: tp.Union[dict, tuple, list, None] = None,
#     data: tp.Union[dict, tuple, list, None] = None,
#     json: tp.Union[dict, tuple, list, None] = None,
#     key: tp.Union[str, int, tuple, list, None] = None,
#     parse_func: object = None,
#     method: str = "GET",
#     return_type: str = "json",
#     ssl: bool = False,
#     verbose: bool = True,
#     semaphore: int = 10,
#     timeout: int = 120,
#     proxy: str | None = None,
#     limits_per_host: int = 10,
#     use_random_proxy: bool = False,
# ) -> dict:
#     """A function for asynchronous Http requests.

#     Args:
#         url (tp.Union[str, tuple, list]): The request url.
#         params (tp.Union[dict, tuple, list, None], optional): The request parameter. Defaults to None.
#         data (tp.Union[dict, tuple, list, None], optional): The request data. Defaults to None.
#         json (tp.Union[dict, tuple, list, None], optional): The request json object. Defaults to None.
#         headers (dict, optional): The request headers. Defaults to None.
#         key (tp.Union[str, int, tuple, list, None], optional): A key to assign the request responses. Defaults to None.
#         parse_func (object, optional): A function for parsing the request responses. Defaults to None.
#         method (str, optional): The request method. Defaults to "GET".
#         return_type (str, optional): Defines return rype. Defaults to json.
#         ssl (bool, optional): Use ssl or not. Defaults to False.
#         verbose (bool, optional): If True, a progressbar is displayed. Defaults to False.
#         semaphore (int, optional): The number of semaphores. Defaults to None.
#         timeout (int, optional): The request timeout. Defaults to None.
#         limits_per_host (int, optional): The limit number per host. Defaults to None.
#         use_random_proxy (bool, optional): Use a random proxy from list of proxies. Defaults to False.

#     Returns:
#         Returns:
#             dict: Dictionary with the request response.
#     """
#     ar = AsyncRequests(
#         headers=headers,
#         semaphore=semaphore,
#         timeout=timeout,
#         limits_per_host=limits_per_host,
#         use_random_proxy=use_random_proxy,
#     )
#     return ar.run_requests(
#         url=url,
#         params=params,
#         data=data,
#         json=json,
#         headers=headers,
#         key=key,
#         parse_func=parse_func,
#         method=method,
#         return_type=return_type,
#         proxy=proxy,
#         ssl=ssl,
#         verbose=verbose,
#     )
