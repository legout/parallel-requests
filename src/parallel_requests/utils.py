import os
import random
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# from .config import USER_AGENTS, PROXIES


def get_user_agents():
    return requests.get(
        "https://gist.githubusercontent.com/pzb/b4b6f57144aea7827ae4/raw/cf847b76a142955b1410c8bcef3aabe221a63db1/user-agents.txt"
    ).text.split("\n")


def random_user_agent(user_agents: list | None = None, as_dict: bool = True) -> str:
    """Random user-agent from list USER_AGENTS.

    Returns:
        str: user-agent
    """
    if user_agents is None:
        try:
            user_agents=get_user_agents()
            user_agent = random.choice(user_agents)
        except Exception as e:
            user_agent = "my-fancy-user-agent"
    else:
        user_agent = random.choice(user_agents)

    return {"user-agent": user_agent} if as_dict else user_agent


def set_webshare_proxies_url(url: str):
    os.environ["WEBSHARE_PROXIES_URL"] = url


def get_webshare_proxies_list(url: str | None = None) -> list:
    """Fetches a list of fast and affordable proxy servers from http://webshare.io.

    After subsription for a plan, get the export url for your proxy list.
        Settings -> Proxy -> List -> Export
    """

    if not url:
        load_dotenv()
        load_dotenv(Path("~/.env").expanduser())
        url = os.getenv("WEBSHARE_PROXIES_URL", None)

    if url:
        set_webshare_proxies_url(url=url)
        proxies = [p for p in requests.get(url).text.split("\r\n") if len(p) > 0]
        proxies = [
            dict(zip(["ip", "port", "user", "pw"], proxy.split(":")))
            for proxy in proxies
        ]
        proxies = [
            f"http://{proxy['user']}:{proxy['pw']}@{proxy['ip']}:{proxy['port']}"
            for proxy in proxies
        ]
        return proxies


def get_free_proxies_list() -> list:
    urls = [
        "http://www.free-proxy-list.net",
        "https://free-proxy-list.net/anonymous-proxy.html",
        # "https://www.us-proxy.org/",
        "https://free-proxy-list.net/uk-proxy.html",
        # "https://www.sslproxies.org/",
    ]

    proxies = list()
    for url in urls:
        proxies.append(
            pd.read_html(
                requests.get(
                    url, headers={"user-agent": "yahoo-symbols-async-requests"}
                ).text
            )[0]
            .rename({"Last Checked": "LastChecked"}, axis=1)
            .query("LastChecked.str.contains('secs')")  # & Https=='no'")
        )

    proxies = pd.concat(proxies, ignore_index=True)
    proxies = (
        proxies.iloc[:, :2]
        .astype(str)
        .apply(lambda x: "http://" + ":".join(x.tolist()), axis=1)
        .tolist()
    )
    return proxies


def random_proxy(proxies: list | None = None, as_dict: bool = True) -> str:
    if proxies is not None:
        proxy = random.choice(proxies)
        return {"http:": proxy, "https": proxy} if as_dict else proxy


def to_list(x: list | str | int | float | pd.Series | None) -> list:
    """Returns a list of the given input"""
    if isinstance(x, (str, dict)):
        return [x]
    elif x is None:
        return [None]
    elif isinstance(x, pd.Series):
        x = x.tolist()
    else:
        return x


def extend_list(x: list, max_len: int) -> list:
    """extends a list of length 1 to `max_len`"""
    if len(x) == 1:
        return x * max_len
    elif len(x)>1 and len(x)<max_len:
        return (x*(max_len//len(x)+1))[:max_len]
    else:
        return x


def unnest_results(results: list, keys: list) -> dict:
    """Unnests a list of dicts.

    Args:
        results (list): list with dicts
        keys (list): keys

    Returns:
        dict: unnested dicts
    """

    if keys[0] is not None and isinstance(results, dict):
        results = dict((k, _results[k]) for _results in results for k in _results)

    if keys[0] is not None and isinstance(results[0], dict):
        results = dict((k, _results[k]) for _results in results for k in _results)

    if len(keys) == 1 and isinstance(results, (list, tuple)):
        results = results[0]

    return results
