import pytest
from odyssey_db.odyssey_db import Migrate, Fixture
from odyssey_db.db.postgres import pg

@pytest.fixture(scope="module")
def postgres():
    from odyssey_db.db.postgres import pg
    pg_object = pg()
    return pg_object
