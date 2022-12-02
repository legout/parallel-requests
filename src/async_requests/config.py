from dotenv import load_dotenv
import os
from .utils import get_user_agents, get_webshare_proxy_list, get_free_proxy_list


USER_AGENTS = get_user_agents()

# Set the variable URL_WEBSHARE_PROXY_LIST in your .env
load_dotenv()
URL_WEBSHARE_PROXY_LIST = os.getenv("URL_WEBSHARE_PROXY_LIST", None)


if URL_WEBSHARE_PROXY_LIST is not None:
    PROXIES = get_webshare_proxy_list(URL_WEBSHARE_PROXY_LIST)

else:
    try:
        PROXIES = get_free_proxy_list()
    except:
        PROXIES = None
