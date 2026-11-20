"""HTTP 层测试（离线；不发起任何网络请求）。"""

from __future__ import annotations

import time
import unittest
from unittest.mock import patch

from dlsite_tracker.http import Fetcher


def make_fetcher(delay: float) -> Fetcher:
    return Fetcher(
        user_agent="test",
        page_delay=delay,
        api_delay=delay,
        image_delay=delay,
        timeout=1,
        max_retries=0,
    )


class ThrottleTest(unittest.TestCase):
    def test_first_request_no_wait(self):
        # 回归：monotonic 基线接近 0 的环境下，首次请求不应等待（P11.1 修复）
        fetcher = make_fetcher(10.0)
        start = time.monotonic()
        fetcher._throttle("page")
        self.assertLess(time.monotonic() - start, 1.0)

    def test_second_request_waits(self):
        fetcher = make_fetcher(0.3)
        fetcher._throttle("page")
        start = time.monotonic()
        fetcher._throttle("page")
        self.assertGreaterEqual(time.monotonic() - start, 0.25)

    def test_kinds_are_independent(self):
        fetcher = make_fetcher(5.0)
        fetcher._throttle("page")
        start = time.monotonic()
        fetcher._throttle("api")
        self.assertLess(time.monotonic() - start, 1.0)


class ProxyTest(unittest.TestCase):
    @patch("dlsite_tracker.http.proxy_bypass", return_value=False)
    @patch("dlsite_tracker.http.getproxies", return_value={"https": "http://127.0.0.1:7897"})
    @patch("dlsite_tracker.http.http.client.HTTPSConnection")
    def test_https_tunnel_and_connection_reuse(self, connection, _proxies, _bypass):
        fetcher = make_fetcher(0)
        proxy = fetcher._proxy_for("https", "www.dlsite.com")
        first = fetcher._connection("https", "www.dlsite.com", 443, proxy)
        self.assertEqual(connection.call_args.args, ("127.0.0.1", 7897))
        first.set_tunnel.assert_called_once_with("www.dlsite.com", 443, headers={})
        self.assertIs(fetcher._connection("https", "www.dlsite.com", 443, proxy), first)
        connection.assert_called_once()

    @patch("dlsite_tracker.http.proxy_bypass", return_value=True)
    @patch("dlsite_tracker.http.getproxies", return_value={"https": "http://127.0.0.1:7897"})
    def test_bypass_uses_direct_connection(self, _proxies, _bypass):
        fetcher = make_fetcher(0)
        self.assertIsNone(fetcher._proxy_for("https", "localhost"))

    @patch("dlsite_tracker.http.proxy_bypass", return_value=False)
    @patch("dlsite_tracker.http.getproxies", return_value={"http": "http://127.0.0.1:7897"})
    @patch("dlsite_tracker.http.http.client.HTTPConnection")
    def test_http_proxy_uses_absolute_url(self, connection, _proxies, _bypass):
        fetcher = make_fetcher(0)
        response = connection.return_value.getresponse.return_value
        response.status = 200
        response.read.return_value = b"ok"
        self.assertEqual(fetcher.get_bytes("http://example.com/a?q=1"), b"ok")
        connection.return_value.request.assert_called_once_with(
            "GET", "http://example.com/a?q=1", headers=fetcher._headers()
        )


if __name__ == "__main__":
    unittest.main()
