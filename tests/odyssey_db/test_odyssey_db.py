import pytest
from unittest.mock import patch, mock_open
import io
from io import StringIO
import tempfile
from pathlib import Path
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
        results_table = migrate.read_sql_files(
            srcpath='/', str_regex=regex_compile)

    with patch('builtins.open', mock_open(read_data='CREATE SCHEMA util;')) as mock_file:
        results_schema = migrate.read_sql_files(
            srcpath='/', str_regex=regex_compile)

    assert results_table['EXTERNAL TABLE'][0]['file'] == '/home/functions/function.sql'
    assert results_table['EXTERNAL TABLE'][0]['name'] == 'util.external_table'
    assert results_schema['SCHEMA'][0]['file'] == '/home/functions/function.sql'
    assert results_schema['SCHEMA'][0]['name'] == 'util'


