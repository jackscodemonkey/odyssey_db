import pytest
import io
import tempfile
from odyssey_db.odyssey_db import Migrate, Fixture


@pytest.mark.migrate
def test_get_sql_files(mocker):
    mocker.patch('pathlib.Path.rglob', return_value=iter(
        ['/home/functions/function.sql', '/home/tables/table.sql', '/home/views/view.sql']))
    m = Migrate()
    files = m.get_sql_files(srcpath='/')
    assert files


@pytest.mark.migrate
def test_get_sql_object_name_postgres(mocker, tmpdir, postgres):
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
    """
    }

    m = Migrate()
    object_name = {}
    for k, v in file_strings.items():
        tf = tempfile.NamedTemporaryFile(mode='w+', dir=tmpdir, delete=False)
        tf.write(v)
        tf.flush()
        oname = m.get_name_from_file(
            file=tf.name, str_regex=postgres.sql_object_name)
        object_name.update({k: oname})
        tf.close()

    assert object_name['file_function'] == 'util.sanity_regression_fn'
    assert object_name['file_table'] == 'util.table'
    assert object_name['file_view'] == 'util.view'
