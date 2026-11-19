import io
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from networkdatalabs import NetworkDataLabs, NetworkDataLabsError  # noqa: E402


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def ok(payload):
    return FakeResponse(json.dumps(payload).encode())


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.c = NetworkDataLabs(api_key="test_key")

    @mock.patch("urllib.request.urlopen")
    def test_lookup(self, urlopen):
        urlopen.return_value = ok({"ip": "8.8.8.8", "location": {"country_code": "US"}})
        r = self.c.lookup("8.8.8.8")
        self.assertEqual(r["location"]["country_code"], "US")
        req = urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.networkdatalabs.com/v0/ip/8.8.8.8")
        self.assertEqual(req.get_header("Authorization"), "Bearer test_key")

    @mock.patch("urllib.request.urlopen")
    def test_own_ip_and_ipv6(self, urlopen):
        urlopen.side_effect = [ok({}), ok({})]
        self.c.lookup()
        self.c.lookup("2001:4860:4860::8888")
        urls = [c[0][0].full_url for c in urlopen.call_args_list]
        self.assertEqual(urls[0], "https://api.networkdatalabs.com/v0/ip")
        self.assertEqual(urls[1], "https://api.networkdatalabs.com/v0/ip/2001%3A4860%3A4860%3A%3A8888")

    @mock.patch("urllib.request.urlopen")
    def test_me(self, urlopen):
        urlopen.return_value = ok({"ip": "4.2.2.2", "plan": "free"})
        self.assertEqual(self.c.me()["plan"], "free")
        self.assertTrue(urlopen.call_args[0][0].full_url.endswith("/v0/me"))

    @mock.patch("urllib.request.urlopen")
    def test_bulk(self, urlopen):
        urlopen.return_value = ok({"results": {}, "errors": {}})
        self.c.bulk(["8.8.8.8", "1.1.1.1"])
        req = urlopen.call_args[0][0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(json.loads(req.data), {"ips": ["8.8.8.8", "1.1.1.1"]})
        with self.assertRaises(ValueError):
            self.c.bulk([])
        with self.assertRaises(ValueError):
            self.c.bulk(["8.8.8.8"] * 101)

    @mock.patch("urllib.request.urlopen")
    def test_error(self, urlopen):
        body = json.dumps({"error": {"code": "QUOTA_EXCEEDED", "message": "Monthly quota reached"}}).encode()
        urlopen.side_effect = urllib.error.HTTPError("u", 429, "Too Many", {}, io.BytesIO(body))
        with self.assertRaises(NetworkDataLabsError) as ctx:
            self.c.lookup("8.8.8.8")
        self.assertEqual(ctx.exception.status, 429)
        self.assertEqual(ctx.exception.code, "QUOTA_EXCEEDED")

    @mock.patch("urllib.request.urlopen")
    def test_network_error(self, urlopen):
        urlopen.side_effect = urllib.error.URLError("timed out")
        with self.assertRaises(NetworkDataLabsError) as ctx:
            self.c.lookup("8.8.8.8")
        self.assertEqual(ctx.exception.status, 0)
        self.assertEqual(ctx.exception.code, "NETWORK_ERROR")

    def test_missing_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                NetworkDataLabs()


if __name__ == "__main__":
    unittest.main()
