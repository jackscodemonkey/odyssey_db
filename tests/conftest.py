import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from odyssey_db.db import postgres
from odyssey_db.builder import Builder
from odyssey_db.migrate import Migrate
from types import SimpleNamespace, ModuleType


@pytest.fixture(scope="module")
def postgres():
    from odyssey_db.db.postgres import Engine
    pg_object = Engine()
    return pg_object


@pytest.fixture()
def builder(mocker, tmpdir):
    version_data = (
        f"__version__='1.0' \n"
        f"__release__='1.0.1' \n"
        ).encode(encoding='UTF-8', errors='strict')

    td = tmpdir.mkdir("module")
    path = Path(td.strpath, '__init__.py')
    modfile = open(path, mode='wb')
    modfile.write(version_data)
    modfile.flush()

    s = {'MIGRATION_FOLDER': td}
    settings = SimpleNamespace(**s)

    build = Builder(settings=settings)
    yield build
    modfile.close()


@pytest.fixture(scope="module")
def migrate():
    migrator = Migrate()
    return migrator


@pytest.fixture(scope="module")
def mocked_open_fixture():
    opener = mock_open()

    def mocked_open(self, *args, **kwargs):
        return opener(self, *args, **kwargs)
