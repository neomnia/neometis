from src.core.hermes.stubs.hermes_cli import (
    _greedy_literal_match,
    _split_key_path,
    is_managed,
    load_config,
    load_config_readonly,
    read_raw_config,
    require_readable_config_before_write,
)

def cfg_get(config: dict, key: str, default=None):
    return config.get(key, default)


__all__ = [
    "_greedy_literal_match",
    "_split_key_path",
    "cfg_get",
    "is_managed",
    "load_config",
    "load_config_readonly",
    "read_raw_config",
    "require_readable_config_before_write",
]
