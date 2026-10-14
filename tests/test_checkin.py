"""Offline regression tests. Only synthetic cookies and simulated HTTP responses."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

import requests

import checkin


class CheckinTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.network_guard = patch("socket.socket", side_effect=AssertionError("Live network is forbidden in tests"))
        self.network_guard.start()
        self.addCleanup(self.network_guard.stop)
        self.log_capture = self.assertLogs(level="INFO")
        self.log_capture.__enter__()
        self.addCleanup(self.log_capture.__exit__, None, None, None)
        self.requests = []

    def install_service(self, accepted=None, points=1000, network_error=False):
        accepted = accepted or {}

        def request(method, url, **kwargs):
            parsed = urlsplit(url)
            cookie = kwargs.get("headers", {}).get("cookie", "")
            self.requests.append((method, parsed.netloc, parsed.path, cookie))
            if network_error:
                raise requests.ConnectionError("Simulated offline service")
            code = accepted.get((cookie, parsed.netloc), -2)
            data = {"code": code, "message": "No permission"}
            if code in (0, 1):
                if parsed.path.endswith("/status"):
                    data = {"code": 0, "data": {"leftDays": "15.5"}}
                elif parsed.path.endswith("/points"):
                    data = {"code": 0, "points": points}
                elif parsed.path.endswith("/exchange"):
                    data = {"code": 0, "message": "Exchange succeeded"}
                else:
                    data = {"code": code, "message": "OK", "points": 1}
            response = requests.Response()
            response.status_code = 200
            response._content = json.dumps(data).encode()
            return response

        transport = patch("requests.sessions.Session.request", side_effect=request)
        transport.start()
        self.addCleanup(transport.stop)

    def exchange_requests(self):
        return [item for item in self.requests if item[2].endswith("/exchange")]

    def test_missing_cookie_returns_failure(self):
        self.assertEqual(checkin.main(), 1)

    def test_invalid_cookie_configuration_returns_failure_without_crashing(self):
        os.environ["GLADOS_COOKIES"] = " & "
        self.assertEqual(checkin.main(), 1)

    def test_rejected_on_both_domains_returns_failure(self):
        os.environ["GLADOS_COOKIES"] = "synthetic-expired"
        self.install_service()
        self.assertEqual(checkin.main(), 1)

    def test_success_on_one_domain_is_enough_for_cookie(self):
        os.environ["GLADOS_COOKIES"] = "synthetic-valid"
        self.install_service({("synthetic-valid", "railgun.info"): 0})
        self.assertEqual(checkin.main(), 0)

    def test_already_checked_in_is_success(self):
        os.environ["GLADOS_COOKIES"] = "synthetic-repeat"
        self.install_service({("synthetic-repeat", "glados.cloud"): 1})
        self.assertEqual(checkin.main(), 0)

    def test_one_working_cookie_does_not_hide_another_failed_cookie(self):
        os.environ["GLADOS_COOKIES"] = "synthetic-valid&synthetic-expired"
        self.install_service({("synthetic-valid", "railgun.info"): 0})
        self.assertEqual(checkin.main(), 1)

    def test_each_cookie_can_succeed_on_a_different_domain(self):
        os.environ["GLADOS_COOKIES"] = " synthetic-first & synthetic-second "
        self.install_service({("synthetic-first", "glados.cloud"): 0, ("synthetic-second", "railgun.info"): 1})
        self.assertEqual(checkin.main(), 0)

    def test_no_domain_results_is_failure(self):
        os.environ["GLADOS_COOKIES"] = "synthetic-valid"
        with patch.object(checkin.Config, "DOMAINS", []):
            self.assertEqual(checkin.main(), 1)

    def test_network_failure_returns_failure(self):
        os.environ["GLADOS_COOKIES"] = "synthetic-valid"
        self.install_service(network_error=True)
        self.assertEqual(checkin.main(), 1)

    def test_unexpected_error_returns_failure(self):
        os.environ["GLADOS_COOKIES"] = "synthetic-valid"
        with patch.object(checkin.Checker, "checkin_all", side_effect=RuntimeError("Simulated failure")):
            self.assertEqual(checkin.main(), 1)

    def test_exchange_is_disabled_by_default_even_with_enough_points(self):
        os.environ["GLADOS_COOKIES"] = "synthetic-valid"
        self.install_service({("synthetic-valid", "glados.cloud"): 0})
        checkin.main()
        self.assertEqual(self.exchange_requests(), [])

    def test_invalid_exchange_flag_stays_disabled(self):
        os.environ.update(GLADOS_COOKIES="synthetic-valid", GLADOS_AUTO_EXCHANGE="maybe")
        self.install_service({("synthetic-valid", "glados.cloud"): 0})
        checkin.main()
        self.assertEqual(self.exchange_requests(), [])

    def test_exchange_only_occurs_on_accepted_domain_after_opt_in(self):
        os.environ.update(GLADOS_COOKIES="synthetic-valid", GLADOS_AUTO_EXCHANGE="true")
        self.install_service({("synthetic-valid", "railgun.info"): 0})
        checkin.main()
        self.assertEqual(self.exchange_requests(), [("POST", "railgun.info", "/api/user/exchange", "synthetic-valid")])

    def test_exchange_is_not_attempted_when_points_are_insufficient(self):
        os.environ.update(GLADOS_COOKIES="synthetic-valid", GLADOS_AUTO_EXCHANGE="true")
        self.install_service({("synthetic-valid", "railgun.info"): 0}, points=499)
        checkin.main()
        self.assertEqual(self.exchange_requests(), [])

    def test_cli_exits_nonzero_without_cookies(self):
        # The child has no service credentials; missing cookies must stop all HTTP work.
        process = subprocess.run([sys.executable, "checkin.py"], cwd=Path(__file__).resolve().parents[1], env={}, capture_output=True, text=True)
        self.assertEqual(process.returncode, 1)
        self.assertNotIn("Traceback", process.stdout + process.stderr)
        checkin.logger.info("CLI exit code verified")


if __name__ == "__main__":
    unittest.main()
