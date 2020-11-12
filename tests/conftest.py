import pytest
from odyssey_db.db import postgres

@pytest.fixture(scope="module")
def postgres():
    from odyssey_db.db.postgres import pg
    pg_object = pg()
    return pg_object
