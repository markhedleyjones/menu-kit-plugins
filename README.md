# menu-kit-plugins

Official plugin repository for [menu-kit](https://github.com/markhedleyjones/menu-kit).

## Available Plugins

| Plugin | Description | Status |
|--------|-------------|--------|
| apps | Application launcher from .desktop files | Available |

## Installation

Plugins are installed via menu-kit's built-in plugin manager:

```bash
menu-kit -p plugins
```

Or manually:

```bash
menu-kit plugin install apps
```

## Plugin Development

See the [menu-kit documentation](https://github.com/markhedleyjones/menu-kit) for plugin development guidelines.

### Plugin Structure

Each plugin is a directory under `plugins/`:

```
plugins/
└── apps/
    ├── manifest.toml
    └── __init__.py
```

### manifest.toml

```toml
[plugin]
name = "apps"
version = "0.1.0"
description = "Application launcher from .desktop files"
api_version = "1"

[plugin.dependencies]
python = []
system.apt = []
```

## License

MIT
