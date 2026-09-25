#!/usr/bin/env python3
"""Provider-free config admission regressions; never start OpenClaw."""
import copy
import json
import unittest

from personal_campaign_config import validate_prepared_config


def fixture():
    return {
        "gateway": {"mode": "local", "bind": "loopback", "port": 28791,
                    "auth": {"mode": "none"}, "reload": {"mode": "off"},
                    "controlUi": {"enabled": False}},
        "plugins": {"enabled": False}, "cron": {"enabled": False},
        "browser": {"enabled": False}, "channels": {},
        "discovery": {"mdns": {"mode": "off"}},
        "update": {"checkOnStart": False, "auto": {"enabled": False}},
        "models": {"mode": "replace", "catalogRefresh": {"enabled": False},
                   "providers": {"mock": {"baseUrl": "http://127.0.0.1:28792/v1",
                    "apiKey": "mock-only", "api": "openai-completions",
                    "models": [{"id": "a", "name": "Synthetic A", "input": ["text"]}]}}},
        "agents": {"defaults": {"model": {"primary": "mock/a", "fallbacks": []},
                                "skipBootstrap": True, "heartbeat": {"every": "0m"}}},
        "tools": {"allow": ["read", "write", "edit", "exec", "process"],
                  "fs": {"workspaceOnly": True}},
    }


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.spec = {"gateway_url": "ws://127.0.0.1:28791", "provider": "mock", "model": "mock/a",
                     "auth_preparation": {"kind": "provider-free-mock",
                                          "provider_endpoint": "http://127.0.0.1:28792/v1"}}

    def test_valid_mock(self):
        validate_prepared_config(json.dumps(fixture()), self.spec)

    def test_escape_surfaces(self):
        changes = [
            (("$include",), "/private/config.json"),
            (("env",), {"shellEnv": {"enabled": True}}),
            (("agents", "defaults", "workspace"), "/private/workspace"),
            (("agents", "entries"), {"prod": {"agentDir": "/private/agent"}}),
            (("gateway", "remote"), {"url": "ws://127.0.0.1:18789"}),
            (("gateway", "port"), 18789),
            (("plugins",), {"enabled": True}),
            (("channels",), {"telegram": {"enabled": True}}),
            (("hooks",), {"enabled": True}),
            (("models", "providers", "mock", "baseUrl"), "https://unapproved.invalid/v1"),
            (("models", "providers", "mock", "apiKey"), "synthetic-literal-secret"),
            (("models", "providers", "mock", "localService"), {"command": "/tmp/unapproved"}),
            (("models", "providers", "mock", "headers"), {"Authorization": "Bearer synthetic"}),
            (("agents", "defaults", "model", "fallbacks"), ["other/route"]),
            (("tools", "allow"), ["message"]),
            (("tools", "fs", "workspaceOnly"), False),
        ]
        for keys, value in changes:
            with self.subTest(keys=keys):
                config = fixture()
                target = config
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                with self.assertRaises(ValueError):
                    validate_prepared_config(json.dumps(config), self.spec)

    def test_api_reference_only(self):
        config = fixture()
        spec = copy.deepcopy(self.spec)
        spec["auth_preparation"]["kind"] = "isolated-api-config"
        config["models"]["providers"]["mock"]["apiKey"] = "${CLAWGAUGE_ISOLATED_API_KEY}"
        validate_prepared_config(json.dumps(config), spec)
        config["models"]["providers"]["mock"]["apiKey"] = "${OPENAI_API_KEY}"
        with self.assertRaises(ValueError):
            validate_prepared_config(json.dumps(config), spec)

    def test_string_endpoint_in_comment_is_not_proof(self):
        config = fixture()
        config["comment"] = self.spec["auth_preparation"]["provider_endpoint"]
        config["models"]["providers"]["mock"]["baseUrl"] = "http://127.0.0.1:18789"
        with self.assertRaises(ValueError):
            validate_prepared_config(json.dumps(config), self.spec)

    def test_synthetic_config_cannot_smuggle_paths(self):
        config = {"mock_provider_endpoint": self.spec["auth_preparation"]["provider_endpoint"]}
        validate_prepared_config(json.dumps(config), self.spec)
        config["agents"] = {"defaults": {"workspace": "/private"}}
        with self.assertRaises(ValueError):
            validate_prepared_config(json.dumps(config), self.spec)


if __name__ == "__main__":
    unittest.main()
