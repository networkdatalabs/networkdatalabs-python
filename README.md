# networkdatalabs

Official Python client for the [Network Data Labs](https://www.networkdatalabs.com) IP geolocation API. No dependencies (standard library `urllib`), Python 3.9+.

```bash
pip install networkdatalabs
```

```python
from networkdatalabs import NetworkDataLabs

ndl = NetworkDataLabs()  # reads NDL_API_KEY, or pass api_key="..."

r = ndl.lookup("8.8.8.8")
print(r["location"]["country_code"], r["location"]["city"], r["network"]["asn"])  # US Mountain View 15169

ndl.lookup()                       # the caller's own IP
ndl.me()                           # plan, usage and limits
ndl.bulk(["8.8.8.8", "1.1.1.1"])   # up to 100 IPs, paid plans
```

Errors raise `NetworkDataLabsError` with `status` and `code` (for example `429` / `QUOTA_EXCEEDED`).

## Plans

Free: 1,000 requests/month, 1 request/second, geolocation + ASN, personal and non-commercial use. Paid plans add bulk, commercial use and risk flags (`is_tor`, `is_vpn` for known VPN networks, `is_relay` for privacy relay, `is_hosting`); on Free those keys are omitted. See [pricing](https://www.networkdatalabs.com/pricing) and the [docs](https://www.networkdatalabs.com/docs).

Get a free key: <https://www.networkdatalabs.com/dashboard/?mode=signup>

## Links

- Homepage: <https://www.networkdatalabs.com>
- Docs: <https://www.networkdatalabs.com/docs>
- Source: <https://github.com/networkdatalabs/networkdatalabs-python>
- Issues: <https://github.com/networkdatalabs/networkdatalabs-python/issues>

## License

MIT
