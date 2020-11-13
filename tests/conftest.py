import pytest
from odyssey_db.db import postgres
from odyssey_db.builder import Builder
from odyssey_db.migrate import Migrate

@pytest.fixture(scope="module")
def postgres():
    from odyssey_db.db.postgres import Engine
    pg_object = Engine()
    return pg_object

@pytest.fixture(scope="module")
def builder():
    build = Builder()
    return build

@pytest.fixture(scope="module")
def migrate():
    migrator = Migrate()
    return migrator