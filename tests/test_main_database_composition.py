import nexus.main as main_module


def test_build_application_composes_database_stack(monkeypatch):
    configured_settings = object()
    provider = object()
    database = object()
    application = object()
    calls = []

    monkeypatch.setattr(
        main_module,
        "settings",
        configured_settings,
    )

    def fake_build_database_provider(received_settings):
        calls.append(
            ("provider", received_settings)
        )
        return provider

    def fake_database(received_provider):
        calls.append(
            ("database", received_provider)
        )
        return database

    def fake_application(*, database):
        calls.append(
            ("application", database)
        )
        return application

    monkeypatch.setattr(
        main_module,
        "build_database_provider",
        fake_build_database_provider,
        raising=False,
    )
    monkeypatch.setattr(
        main_module,
        "Database",
        fake_database,
        raising=False,
    )
    monkeypatch.setattr(
        main_module,
        "NexusApplication",
        fake_application,
    )

    result = main_module.build_application()

    assert result is application
    assert calls == [
        ("provider", configured_settings),
        ("database", provider),
        ("application", database),
    ]
