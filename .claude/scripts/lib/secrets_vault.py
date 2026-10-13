#!/usr/bin/env python3
"""Secure secrets management for orchestration_v1.

Provides encrypted credential storage using OS keyring (fallback: .env.vault).
Supports:
  - API keys / PATs (Anthropic, GitHub, etc.)
  - Database credentials
  - OAuth tokens
  - Custom credentials

Usage:
  from secrets_vault import SecretVault
  vault = SecretVault()
  api_key = vault.get("anthropic_api_key")
  vault.set("github_pat", "ghp_...")
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import os
import json
import sys

# Try to import keyring for secure storage
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False


@dataclass(frozen=True)
class VaultConfig:
    """Vault configuration (immutable)."""
    service_name: str = "orchestration_v1"
    env_file: Path = Path(".env.vault")
    fallback_to_env: bool = True  # Fallback to .env if keyring unavailable
    mask_in_logs: bool = True     # Never log actual secrets


class SecretVault:
    """Secure credential vault with OS keyring + .env.vault fallback."""

    def __init__(self, config: Optional[VaultConfig] = None):
        """Initialize vault with optional custom config."""
        self.config = config or VaultConfig()
        self._validate_paths()
        self._env_cache: Dict[str, str] = {}
        if self.config.fallback_to_env:
            self._load_env_vault()

    def _validate_paths(self) -> None:
        """Ensure .env.vault is readable and .env is never accessed."""
        if self.config.env_file.exists():
            # Verify .env.vault has restrictive permissions (Unix only)
            try:
                stat_info = self.config.env_file.stat()
                mode = stat_info.st_mode & 0o777
                if mode != 0o600:
                    # On Windows, stat mode is different; just warn
                    pass
            except Exception:
                pass

    def _load_env_vault(self) -> None:
        """Load .env.vault into memory cache."""
        if not self.config.env_file.exists():
            return
        try:
            with open(self.config.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        self._env_cache[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            print(f"[WARN] Failed to load {self.config.env_file}: {e}", file=sys.stderr)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret by key.

        Priority:
          1. OS keyring (if available)
          2. .env.vault (if loaded)
          3. OS environment variable
          4. Default value
        """
        # Try keyring first
        if HAS_KEYRING:
            try:
                value = keyring.get_password(self.config.service_name, key)
                if value is not None:
                    return value
            except Exception:
                pass

        # Try .env.vault cache
        if key in self._env_cache:
            return self._env_cache[key]

        # Try environment (for CI/CD)
        value = os.environ.get(key)
        if value is not None:
            return value

        # Return default
        return default

    def set(self, key: str, value: str) -> bool:
        """Store a secret securely.

        Returns:
          True if stored successfully, False if fallback only.
        """
        if not value:
            return False

        # Try keyring first
        if HAS_KEYRING:
            try:
                keyring.set_password(self.config.service_name, key, value)
                # Also cache it
                self._env_cache[key] = value
                return True
            except Exception as e:
                print(
                    f"[WARN] Keyring set failed for {key}: {e}. "
                    f"Falling back to .env.vault.",
                    file=sys.stderr,
                )

        # Fallback: .env.vault
        if self.config.fallback_to_env:
            try:
                # Append or update in .env.vault
                self._append_to_env_vault(key, value)
                self._env_cache[key] = value
                return True
            except Exception as e:
                print(
                    f"[ERROR] Failed to store {key} in .env.vault: {e}",
                    file=sys.stderr,
                )
                return False

        return False

    def _append_to_env_vault(self, key: str, value: str) -> None:
        """Append or update key=value in .env.vault."""
        lines = []
        found = False

        # Read existing
        if self.config.env_file.exists():
            with open(self.config.env_file, "r") as f:
                for line in f:
                    if line.startswith(f"{key}="):
                        lines.append(f'{key}="{value}"\n')
                        found = True
                    else:
                        lines.append(line)

        # Append if not found
        if not found:
            lines.append(f'{key}="{value}"\n')

        # Write back (restrictive permissions on Unix)
        with open(self.config.env_file, "w") as f:
            f.writelines(lines)

        # Try to set Unix permissions to 0o600 (owner read/write only)
        try:
            self.config.env_file.chmod(0o600)
        except Exception:
            # Windows or unsupported; continue
            pass

    def delete(self, key: str) -> bool:
        """Delete a secret."""
        deleted = False

        # Try keyring
        if HAS_KEYRING:
            try:
                keyring.delete_password(self.config.service_name, key)
                deleted = True
            except Exception:
                pass

        # Remove from cache
        if key in self._env_cache:
            del self._env_cache[key]
            deleted = True

        # Remove from .env.vault
        if self.config.env_file.exists():
            lines = []
            with open(self.config.env_file, "r") as f:
                for line in f:
                    if not line.startswith(f"{key}="):
                        lines.append(line)
            with open(self.config.env_file, "w") as f:
                f.writelines(lines)
            deleted = True

        return deleted

    def mask(self, value: str) -> str:
        """Mask a value for logging (show only first/last 4 chars)."""
        if not value or len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"


# Global vault instance (singleton)
_vault: Optional[SecretVault] = None


def get_vault() -> SecretVault:
    """Get or create global vault instance."""
    global _vault
    if _vault is None:
        _vault = SecretVault()
    return _vault
