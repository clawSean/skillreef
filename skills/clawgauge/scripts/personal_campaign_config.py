#!/usr/bin/env python3
"""Admit a narrow disposable Gateway config, not an OS security sandbox.

Unknown fields fail closed: a copied config must not override disposable roots,
load external code/includes, inherit credentials, or enable production delivery.
Native startup and effective route qualification remain separate requirements.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse


def object_keys(value: Any, allowed: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError(f"{label}: unsupported config fields or object type")
    return value


def require(value: Any, expected: Any, label: str) -> None:
    if value != expected:
        raise ValueError(f"{label}: required isolated value is missing or different")


def validate_prepared_config(text: str, spec: dict[str, Any]) -> None:
    # Standard JSON only; do not evaluate JSON5/includes or expand secret refs.
    config = json.loads(text)
    preparation = spec["auth_preparation"]
    endpoint = preparation["provider_endpoint"]
    parsed = urlparse(endpoint)
    if (parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.hostname is None or parsed.port == 18789):
        raise ValueError("provider endpoint contains credentials, query, or production port")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port
    ):
        raise ValueError("provider endpoint must use HTTPS or explicit loopback HTTP")
    if preparation["kind"] == "provider-free-mock" and not (
        parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port
    ):
        raise ValueError("provider-free mock must use explicit loopback HTTP")

    # Synthetic lifecycle executable uses this inert config; a real OpenClaw
    # Gateway rejects these unknown top-level fields rather than executing them.
    if isinstance(config, dict) and "mock_provider_endpoint" in config:
        if preparation["kind"] != "provider-free-mock":
            raise ValueError("synthetic fixture config requires provider-free mock mode")
        object_keys(config, {"mock_provider_endpoint", "sleep_seconds", "fail_model", "fail_task"}, "fixture")
        require(config["mock_provider_endpoint"], endpoint, "fixture endpoint")
        return

    object_keys(config, {"gateway", "models", "agents", "tools", "plugins", "cron",
                         "browser", "discovery", "update", "channels"}, "config")
    for name in ("plugins", "cron", "browser"):
        require(config.get(name), {"enabled": False}, name)
    require(config.get("channels", {}), {}, "channels")
    require(config.get("discovery"), {"mdns": {"mode": "off"}}, "discovery")
    require(config.get("update"), {"checkOnStart": False, "auto": {"enabled": False}}, "update")
    gateway = object_keys(config.get("gateway"),
                          {"mode", "bind", "port", "auth", "reload", "controlUi", "tailscale"}, "gateway")
    require(gateway.get("mode"), "local", "gateway.mode")
    require(gateway.get("bind"), "loopback", "gateway.bind")
    require(gateway.get("port"), urlparse(spec["gateway_url"]).port, "gateway.port")
    require(gateway.get("auth"), {"mode": "none"}, "gateway.auth")
    require(gateway.get("reload"), {"mode": "off"}, "gateway.reload")
    require(gateway.get("controlUi"), {"enabled": False}, "gateway.controlUi")
    require(gateway.get("tailscale", {"mode": "off"}), {"mode": "off"}, "gateway.tailscale")

    models = object_keys(config.get("models"), {"mode", "catalogRefresh", "providers"}, "models")
    require(models.get("mode"), "replace", "models.mode")
    require(models.get("catalogRefresh"), {"enabled": False}, "models.catalogRefresh")
    providers = object_keys(models.get("providers"), {spec["provider"]}, "providers")
    provider = object_keys(providers.get(spec["provider"]),
                           {"baseUrl", "api", "apiKey", "models"}, "provider")
    require(provider.get("baseUrl"), endpoint, "provider.baseUrl")
    expected_key = ("mock-only" if preparation["kind"] == "provider-free-mock"
                    else "${CLAWGAUGE_ISOLATED_API_KEY}")
    require(provider.get("apiKey"), expected_key, "provider.apiKey")
    if provider.get("api") not in {"openai-completions", "openai-responses", "anthropic-messages"}:
        raise ValueError("provider.api: unsupported adapter for isolated config")
    definitions = provider.get("models")
    if not isinstance(definitions, list) or not definitions:
        raise ValueError("provider.models must be nonempty")
    ids = set()
    for definition in definitions:
        object_keys(definition, {"id", "name", "reasoning", "input", "contextWindow", "maxTokens", "cost"}, "model")
        if not isinstance(definition.get("id"), str):
            raise ValueError("model.id must be a string")
        ids.add(definition["id"])
        if "cost" in definition:
            costs = object_keys(definition["cost"], {"input", "output", "cacheRead", "cacheWrite"}, "model.cost")
            if any(type(value) not in (int, float) or value < 0 for value in costs.values()):
                raise ValueError("model.cost must contain nonnegative numbers")
        for key, value in definition.items():
            if key == "cost":
                continue
            if isinstance(value, dict) or (isinstance(value, list) and (key != "input" or value != ["text"])):
                raise ValueError("model definition contains unsupported nested metadata")
    requested = spec["model"].removeprefix(spec["provider"] + "/")
    if requested not in ids:
        raise ValueError("requested model is absent from the isolated provider config")

    agents = object_keys(config.get("agents"), {"defaults"}, "agents")
    defaults = object_keys(agents.get("defaults"), {"model", "skipBootstrap", "heartbeat"}, "agent defaults")
    route = object_keys(defaults.get("model"), {"primary", "fallbacks"}, "default model")
    if route.get("primary") not in {spec["provider"] + "/" + value for value in ids}:
        raise ValueError("default model is outside the isolated provider catalog")
    require(route.get("fallbacks"), [], "model.fallbacks")
    require(defaults.get("skipBootstrap"), True, "skipBootstrap")
    require(defaults.get("heartbeat"), {"every": "0m"}, "heartbeat")
    tools = object_keys(config.get("tools"), {"allow", "fs"}, "tools")
    allow = tools.get("allow")
    if (not isinstance(allow, list) or not allow
            or not set(allow).issubset({"read", "write", "edit", "apply_patch", "exec", "process"})):
        raise ValueError("tools.allow must explicitly restrict the coding-only surface")
    require(tools.get("fs"), {"workspaceOnly": True}, "tools.fs")
