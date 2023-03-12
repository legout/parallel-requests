# FAST PARALLEL HTTP REQUESTS

A python library for fast parallel HTTP requests.

## Installation
```
pip install git+https://github.com/legout/parallel-requests
```

## Examples

...

### Use of a random proxy server.

**Note**
This library works fine without using random proxies and using proxies for running multiple http requests might be illegal.

When setting the parameter `random-proxy=True`  free proxies* are used. In my experience, these proxies are not reliable, but maybe you are lucky.

#### Webshare.io proxies
I am using proxies from [webshare.io](https://www.webshare.io/). I am very happy with their service and the pricing. If you wanna use their service too, sign up (use the [this link](https://www.webshare.io/?referral_code=upb7xtsy39kl) if you wanna support my work) and choose a plan that fits your needs. In the next step, go to Dashboard -> Proxy -> List -> Download and copy the download link. Place this download link into an `.env` file and name the variable `WEBSHARE_PROXIES_URL` (see the `.env-exmaple` in this repository).
```
WEBSHARE_PROXIES_URL="https://proxy.webshare.io/api/v2/proxy/list/download/abcdefg1234567/-/any/username/direct/-/"
```

*Free Proxies are scraped from here:
- "http://www.free-proxy-list.net"
- "https://free-proxy-list.net/anonymous-proxy.html"
- "https://www.us-proxy.org/"
- "https://free-proxy-list.net/uk-proxy.html"
- "https://www.sslproxies.org/"


<hr>

#### Support my work :-)

If you find this useful, you can buy me a coffee. Thanks!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W0ACJPB)

