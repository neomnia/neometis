#!/usr/bin/env bash
# NéoMêtis installer entrypoint — delegates to scripts/install.sh
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts/install.sh" "$@"
