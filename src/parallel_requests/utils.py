import random
import os
import pandas as pd
import requests

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
        user_agent = "my-fancy-user-agent"
    else:
        user_agent = random.choice(user_agents)

    return {"user-agent": user_agent} if as_dict else user_agent


def set_webshare_proxy_url(url: str):
    os.environ["WEBSHARE_PROXY_URL"] = url


def get_webshare_proxy_list(url: str | None) -> list:
    """Fetches a list of fast and affordable proxy servers from http://webshare.io.

    After subsription for a plan, get the export url for your proxy list.
        Settings -> Proxy -> List -> Export
    """
    if not url:
        url = os.getenv("WEBSHARE_PROXY_URL", None)

    if url:
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


def get_free_proxy_list() -> list:
    urls = [
        "http://www.free-proxy-list.net",
        "https://free-proxy-list.net/anonymous-proxy.html",
        "https://www.us-proxy.org/",
        "https://free-proxy-list.net/uk-proxy.html",
        "https://www.sslproxies.org/",
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
            .query("LastChecked.str.contains('secs') & Https=='no'")
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
    if proxies is None:
        return None
    else:
        proxy = random.choice(proxies)
        return {"http:": proxy, "https": proxy} if as_dict else proxy
