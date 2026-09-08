"""Deployment configuration loader for Stage-G.

Loads and validates runtime configurations from environment variables, profiles, or dictionaries.
"""

import os
from typing import Mapping, Union

from medicalplab.stage_b.models import require
from .models import AppConfig, Environment


DEFAULT_CONFIGS: dict[Environment, AppConfig] = {
    Environment.DEVELOPMENT: AppConfig(
        env=Environment.DEVELOPMENT,
        api_version="v1",
        db_uri="sqlite:///:memory:",
        rate_limit_per_minute=60,
        log_level="INFO",
    ),
    Environment.STAGING: AppConfig(
        env=Environment.STAGING,
        api_version="v1",
        db_uri="postgresql://staging_user:secret@localhost:5432/staging_db",
        rate_limit_per_minute=120,
        log_level="INFO",
    ),
    Environment.PRODUCTION: AppConfig(
        env=Environment.PRODUCTION,
        api_version="v1",
        db_uri="postgresql://prod_user:secret@prod-db.internal:5432/medplab",
        rate_limit_per_minute=300,
        log_level="WARNING",
    ),
}


def load_config(
    env_or_map: Union[str, Mapping[str, str], None] = None,
) -> AppConfig:
    """Load application configuration from environment name, dictionary, or system env."""
    raw_env = None
    source = os.environ

    if isinstance(env_or_map, str):
        raw_env = env_or_map.strip().upper()
    elif isinstance(env_or_map, Mapping):
        source = env_or_map
        raw_env = source.get("STAGE_G_ENV", source.get("MEDICALPLAB_ENV"))
    else:
        raw_env = source.get("STAGE_G_ENV", source.get("MEDICALPLAB_ENV"))

    if not raw_env:
        raw_env = "DEVELOPMENT"
    else:
        raw_env = raw_env.strip().upper()

    # Map to Environment enum
    valid_map = {
        "DEVELOPMENT": Environment.DEVELOPMENT,
        "STAGING": Environment.STAGING,
        "PRODUCTION": Environment.PRODUCTION,
    }
    env = valid_map.get(raw_env, Environment.DEVELOPMENT)
    base_config = DEFAULT_CONFIGS[env]

    # Check for individual overrides
    db_uri = source.get("STAGE_G_DB_URI", source.get("MEDICALPLAB_DB_URI", base_config.db_uri))
    api_version = source.get("STAGE_G_API_VERSION", source.get("MEDICALPLAB_API_VERSION", base_config.api_version))

    raw_rate = source.get("STAGE_G_RATE_LIMIT", source.get("MEDICALPLAB_RATE_LIMIT"))
    if raw_rate is not None:
        try:
            rate_limit = int(raw_rate)
        except ValueError:
            rate_limit = base_config.rate_limit_per_minute
    else:
        rate_limit = base_config.rate_limit_per_minute

    log_level = source.get("STAGE_G_LOG_LEVEL", source.get("MEDICALPLAB_LOG_LEVEL", base_config.log_level))

    return AppConfig(
        env=env,
        api_version=api_version,
        db_uri=db_uri,
        rate_limit_per_minute=rate_limit,
        log_level=log_level,
    )
