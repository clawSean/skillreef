# OpenClaw Plugin Manifest And Build Requirements

Use this when creating or auditing an OpenClaw plugin package.

## `openclaw.plugin.json`

Every plugin needs a manifest. Beyond `id`, `name`, `description`, and `configSchema` when used, activation fields matter for performance and correct loading.

### `activation.onStartup`

OpenClaw is moving away from implicit startup loading. Declare this explicitly:

```json
{
  "activation": { "onStartup": false }
}
```

- `false`: plugin is lazy-loaded on demand for CLI commands, provider/channel triggers, or other declared activation.
- `true`: plugin must import during Gateway startup. Required for chat slash commands registered with `api.registerCommand`, channel adapters, startup HTTP routes, and gateway methods needed before listen.

Chat slash commands require `onStartup: true`. The chat command dispatcher only knows about commands registered by plugins loaded at startup. `activation.onCommands` helps terminal `openclaw <command>` discovery; it does not on its own load a plugin when someone types `/mycommand` in Telegram or another chat surface. The Telegram native slash menu is also built at startup.

Without explicit activation, OpenClaw may fall back to deprecated implicit startup behavior, loading too eagerly and adding startup/per-turn overhead.

### Narrower activation triggers

```json
{
  "activation": {
    "onStartup": false,
    "onCommands": ["mycommand"],
    "onProviders": ["myprovider"],
    "onChannels": ["mychannel"]
  }
}
```

Available trigger families include `onCommands`, `onProviders`, `onChannels`, `onAgentHarnesses`, `onRoutes`, `onConfigPaths`, and `onCapabilities`.

## Side-Effect Guarding

OpenClaw calls `register(api)` during discovery and full activation. Guard expensive or live side effects:

```ts
register(api) {
  api.registerCommand({ name: "mycommand", /* ... */ });

  if (api.registrationMode !== "full") return;

  startBackgroundWorker();
  openDatabase();
}
```

Known modes: `full`, `discovery`, `setup-only`, `setup-runtime`, and `cli-metadata`.

## Other Manifest Fields

| Field | Use |
|---|---|
| `enabledByDefault` | Bundled plugins only; omit for external plugins. |
| `providerAuthEnvVars` | Cheap auth detection for provider ids; deprecated in favor of `setup.providers[].envVars`. |
| `contracts.tools` | Manifest-driven tool discovery without importing runtime. |

## `package.json` Setup Entry

For channel plugins that register HTTP routes or gateway methods at startup, consider a lightweight `setupEntry`:

```json
{
  "openclaw": {
    "extensions": ["./index.ts"],
    "setupEntry": "./setup-entry.ts",
    "startup": {
      "deferConfiguredChannelFullLoadUntilAfterListen": true
    }
  }
}
```

`setupEntry` loads instead of the full entry during startup/setup. Only enable deferred loading when `setupEntry` covers all pre-listen capabilities. Not needed for simple command plugins.

## TypeScript Build Requirements

OpenClaw plugins with TypeScript entry points require compiled JavaScript output. Without it, `openclaw plugins doctor` and config reload warn about missing compiled runtime output. This applies to local, npm, and ClawHub plugins.

Required baseline:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "allowJs": true,
    "strict": false
  },
  "include": ["src"]
}
```

Package shape:

```json
{
  "openclaw": {
    "extensions": ["./src/index.ts"],
    "runtimeExtensions": ["./dist/index.js"]
  },
  "scripts": {
    "build": "tsc"
  }
}
```

Compile before testing:

```bash
npx tsc
```

Then verify with the smallest available load/build command. `openclaw plugins doctor` should not warn about missing compiled runtime output.
