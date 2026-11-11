"""Phase 1 settings and per-run configuration tests."""

from site_dna.core.config import ScanConfig, Settings


def test_scan_defaults_are_available(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("PSI_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.storage_dir == "storage"
    assert settings.allow_private_hosts is False
    assert settings.scan_max_pages == 20
    assert settings.scan_max_depth == 2
    assert settings.scan_max_broken_link_checks == 200
    assert settings.scan_request_timeout_seconds == 20.0
    assert settings.scan_page_timeout_seconds == 45.0
    assert settings.scan_psi_timeout_seconds == 90.0
    assert settings.scan_per_host_rps == 2.0
    assert settings.scan_max_total_seconds == 300.0
    assert settings.psi_api_key is None


def test_psi_key_and_storage_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("PSI_API_KEY", "super-secret-psi-key")
    monkeypatch.setenv("STORAGE_DIR", "custom-storage")

    settings = Settings(_env_file=None)

    assert settings.get_effective_psi_api_key() == "super-secret-psi-key"
    assert settings.storage_dir == "custom-storage"
    assert "super-secret-psi-key" not in repr(settings)


def test_allow_private_hosts_requires_test_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOW_PRIVATE_HOSTS", "true")

    settings = Settings(_env_file=None)

    assert settings.private_hosts_allowed() is False


def test_allow_private_hosts_honored_in_test_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ALLOW_PRIVATE_HOSTS", "true")

    settings = Settings(_env_file=None)

    assert settings.private_hosts_allowed() is True


def test_scan_config_builds_from_settings_with_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    settings = Settings(_env_file=None)

    config = ScanConfig.from_settings(
        settings,
        input_url="https://example.com",
        max_pages=5,
        max_depth=1,
        embed_images=True,
        verbose=True,
    )

    assert config.input_url == "https://example.com"
    assert config.max_pages == 5
    assert config.max_depth == 1
    assert config.max_broken_link_checks == 200
    assert config.request_timeout == 20.0
    assert config.page_timeout == 45.0
    assert config.psi_timeout == 90.0
    assert config.per_host_rps == 2.0
    assert config.max_total_seconds == 300.0
    assert config.embed_images is True
    assert config.verbose is True
    assert config.permission_attested is False


def test_scan_config_defaults_use_settings_values(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("SCAN_MAX_PAGES", "7")
    settings = Settings(_env_file=None)

    config = ScanConfig.from_settings(settings, input_url="https://example.com")

    assert config.max_pages == 7
