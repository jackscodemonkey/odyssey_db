import pytest
from unittest.mock import patch, mock_open
import io
from io import StringIO
import tempfile
from odyssey_db.migrate import Migrate
from odyssey_db.fixture import Fixture
from odyssey_db.builder import Builder


@pytest.mark.migrate
def test_get_sql_files(mocker):
    mocker.patch('pathlib.Path.rglob', return_value=iter(
        ['/home/functions/function.sql', '/home/tables/table.sql', '/home/views/view.sql']))
    m = Migrate()
    files = m.get_sql_files(srcpath='/')
    assert files


@pytest.mark.postgres
def test_get_sql_object_name_postgres(tmpdir, postgres):

    file_strings = {
        'file_function': """
        --
        -- PostgreSQL database dump
        --

        -- Dumped from database version 9.4.24
        -- Dumped by pg_dump version 13.0

        SET statement_timeout = 0;

        CREATE FUNCTION util.sanity_regression_fn(p_batch_key bigint, p_sanity_key bigint, p_table_schema text, p_table_name text, v_query_arr text[]) RETURNS VOID
        AS $$
        DECLARE
        v_stuff text;
        BEGIN
            SELECT stuff from table.stuff;
        END;
        LANGUAGE plpgsql;
    """,
        'file_table': """
     CREATE TABLE util.table (id INT);
    """,
        'file_view': """
     CREATE OR REPLACE VIEW util.view AS BEGIN SELECT 1 FROM dual; END;
    """,
        'file_object_not_found': """
        CREATE OR REPLACE NO OBJECT NAME HERE ;
        """
    }

    m = Migrate()
    object_name = {}
    for k, v in file_strings.items():
        tf = tempfile.NamedTemporaryFile(mode='w+', dir=tmpdir, delete=False)
        tf.write(v)
        tf.flush()
        oname = m.get_name_from_file(
            file_name=tf.name, str_regex=postgres.sql_object_name)
        object_name.update({k: oname[0]})
        tf.close()

    assert object_name['file_function'][2] == 'util.sanity_regression_fn'
    assert object_name['file_table'][2] == 'util.table'
    assert object_name['file_view'][2] == 'util.view'
    assert str(object_name['file_object_not_found'][1]).upper() != 'SCHEMA'


@pytest.mark.postgres
def test_read_files(mocker, postgres, migrate):

    mocker.patch('pathlib.Path.rglob', return_value=[
                 '/home/functions/function.sql', '/home/tables/table.sql', '/home/views/view.sql', '/home/schemata/schema.sql'])

    regex_compile = postgres.sql_object_name

    with patch('builtins.open', mock_open(read_data='CREATE EXTERNAL TABLE util.external_table')) as mock_file:
        results_table = migrate.read_sql_files(srcpath='/', str_regex=regex_compile)

    with patch('builtins.open', mock_open(read_data='CREATE SCHEMA util;')) as mock_file:
        results_schema = migrate.read_sql_files(srcpath='/', str_regex=regex_compile)

    assert results_table['EXTERNAL TABLE'][0]['file'] == '/home/functions/function.sql'
    assert results_table['EXTERNAL TABLE'][0]['name'] == 'util.external_table'
    assert results_schema['SCHEMA'][0]['file'] == '/home/functions/function.sql'
    assert results_schema['SCHEMA'][0]['name'] == 'util'


@pytest.mark.builder
def test_read_manifest(builder):
    toml_data = """
    ###########################
    # Migration Configuration
    ##########################

    [0001]
    up = [
        {name = "util.table1", type = "table", action = "drop"},
        {name = "util.table2", type = "table", action = "create"},
        {name = "util.table3", type = "table", action = "create"},
        {name = "util.table4", type = "ddl", action = "execute", location="migrations/0001/up/meh.sql"},
        {name = "data fix", type="dml", action="execute", location="migrations/0001/up/data_fix.sql"}
    ]
    down = [
        {name = "data fix", type="dml", action="execute", location="migrations/0001/down/data_fix.sql"},
        {name = "util.table4", type = "ddl", action = "execute", location="migrations/0001/down/meh.sql"},
        {name = "util.table3", type = "table", action = "drop"},
        {name = "util.table2", type = "table", action = "drop"},
        {name = "util.table1", type = "table", action = "drop"},
    ]
    """

    file = StringIO(toml_data)
    results_toml = builder.read_manifest(file)

    assert type(results_toml) is dict
    assert len(results_toml['0001']['up']) == 5
    assert len(results_toml['0001']['down']) == 5


@pytest.mark.builder
def test_generate_file_hash(mocker, builder):
    hash_data = "Random Data For the file"
    with patch('builtins.open', mock_open(read_data=hash_data)) as mock_file:
        result_hash = builder.generate_file_hash('/dev/null')

    assert result_hash == 'fcfff2c82865ae5d292dc4240816f8969980faac5007c8eb874c92ef2570a765'


@pytest.mark.builder
def test_write_migration_files(mocker, builder):
    sql_source = """
    CREATE OR REPLACE FUNCTION util.function()
    RETURNS VOID AS
    $BODY$
        DECLARE v_sql = text();
        BEGIN;
            SELECT 1;
        END;
    $BODY$
    LANGUAGE plpgsql;
    """

    source_file_dict = [{'file': '/home/functions/function.sql', 'name': 'util.function'}, {'file': '/home/tables/table.sql', 'name': 'util.table'}]

    config_dict = {'0001': {'up': [{'name': 'util', 'type': 'schema', 'action': 'create'}, {'name': 'util.table1', 'type': 'table', 'action': 'create'}, {'name': 'util.table1', 'type': 'table', 'action': 'drop'}, {'name': 'util.table2', 'type': 'table', 'action': 'create'}, {'name': 'util.function', 'type': 'function', 'action': 'create'}, {'name': 'util.table3', 'type': 'ddl', 'action': 'execute', 'location': 'migrations/0001/up/meh.sql'}, {'name': 'data fix', 'type': 'dml', 'action': 'execute', 'location': 'migrations/0001/up/data_fix.sql'}],
                            'down': [{'name': 'data fix', 'type': 'dml', 'action': 'execute', 'location': 'migrations/0001/down/data_fix.sql'}, {'name': 'util.table3', 'type': 'ddl', 'action': 'execute', 'location': 'migrations/0001/down/meh.sql'}, {'name': 'util.function', 'type': 'function', 'action': 'drop'}, {'name': 'util.table2', 'type': 'table', 'action': 'drop'}, {'name': 'util', 'type': 'schema', 'action': 'drop'}]}, '0002': {'up': [{'name': 'sandbox', 'type': 'schema', 'action': 'create'}], 'down': [{'name': 'sandbox', 'type': 'schema', 'action': 'drop'}]}}
    with patch('builtins.open', mock_open(read_data=sql_source)) as mock_file:
        result = builder.write_migration_files('0001', config_dict, source_file_dict)

    assert result
