from app.db.mongo import DEFAULT_DB_NAME, close_mongo, init_mongo


async def test_init_mongo_uses_default_database_when_uri_has_no_path(monkeypatch) -> None:
    monkeypatch.delenv("MONGO_DB", raising=False)
    db = init_mongo("mongodb://localhost:27017")
    assert db.name == DEFAULT_DB_NAME
    await close_mongo()


async def test_init_mongo_uses_env_database_when_uri_has_no_path(monkeypatch) -> None:
    monkeypatch.setenv("MONGO_DB", "railway_chat")
    db = init_mongo("mongodb://localhost:27017")
    assert db.name == "railway_chat"
    await close_mongo()


async def test_init_mongo_prefers_database_from_uri(monkeypatch) -> None:
    monkeypatch.setenv("MONGO_DB", "env_chat")
    db = init_mongo("mongodb://localhost:27017/uri_chat")
    assert db.name == "uri_chat"
    await close_mongo()


async def test_init_mongo_allows_explicit_database_override(monkeypatch) -> None:
    monkeypatch.setenv("MONGO_DB", "env_chat")
    db = init_mongo("mongodb://localhost:27017", database_name="explicit_chat")
    assert db.name == "explicit_chat"
    await close_mongo()
