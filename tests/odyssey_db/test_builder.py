import pytest
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch, mock_open


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
def test_migration_file_name(builder):
    build_number = '0001'
    direction = 'up'
    migration_folder = 'src/migrations/'
    expected_result = Path('src/migrations/0001_up.sql')
    result = builder.migration_file_name(
        build_number=build_number, direction=direction, migration_folder=migration_folder)

    assert result == expected_result


@pytest.mark.builder
def test_migration_file_exists(mocker, builder):
    file = Path('src/migrations/0001_up.sql')
    mocker.patch('pathlib.Path.is_file', return_value=True)
    result_is_file = builder.migration_file_exists(file)
    mocker.patch("pathlib.Path.is_file", return_value=False)
    resuilt_not_file = builder.migration_file_exists(file)

    assert result_is_file == True
    assert resuilt_not_file == False


@pytest.mark.builder
def test_write_migration(mocker, tmpdir, builder):
    tf = tempfile.NamedTemporaryFile(mode='w+', dir=tmpdir, delete=False)
    file = Path(tf.name)
    spec = [
        '\n-- ODESSEY BEGIN |util|schema\nCREATE SCHEMA util;\n-- ODESSEY END |util|schema\n',
        '\n-- ODESSEY BEGIN |util.table1|table\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |util.table1|table\n',
        '\n-- ODESSEY BEGIN |util.table1|table\nDROP TABLE util.table1;\n-- ODESSEY END |util.table1|table\n',
        '\n-- ODESSEY BEGIN |util.function|function\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |util.function|function\n',
        '\n-- ODESSEY BEGIN |util.table3|ddl\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |util.table3|ddl\n',
        '\n-- ODESSEY BEGIN |data fix|dml\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |data fix|dml\n'
    ]

    with patch('builtins.open', write_data="") as mock_file:
        results = builder.write_migration(file, spec)

    assert results == True


@pytest.mark.builder
def test_match_previous_definition(builder, tmpdir):
    # The spacing is imporant for the next two string variables to the outcome of the test.
    source_data = """
    -- ODESSEY BEGIN |util.function|function

        CREATE OR REPLACE FUNCTION util.function()
        RETURNS VOID AS
        $BODY$
            DECLARE v_sql = text();
            BEGIN;
                SELECT 1;
            END;
        $BODY$
        LANGUAGE plpgsql;

    -- ODESSEY END |util.function|function
    """

    expected_result = """

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
    o_name = "util.function"
    o_type = "function"
    tf = tempfile.NamedTemporaryFile(mode='w+', dir=tmpdir, delete=False)
    tf.write(source_data)
    tf.flush()
    ofile = Path(tf.name)

    result, contents = builder.match_previous_definition(
        filename=ofile, objname=o_name, objtype=o_type)

    assert result == True
    assert expected_result == contents


@pytest.mark.builder
def test_build_up_migration(mocker, builder):
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

    expected_result = [
        '\n-- ODESSEY BEGIN |util|schema\nCREATE SCHEMA util;\n-- ODESSEY END |util|schema\n',
        '\n-- ODESSEY BEGIN |util.table1|table\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |util.table1|table\n',
        '\n-- ODESSEY BEGIN |util.table1|table\nDROP TABLE util.table1;\n-- ODESSEY END |util.table1|table\n',
        '\n-- ODESSEY BEGIN |util.table2|table\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |util.table2|table\n',
        '\n-- ODESSEY BEGIN |util.function|function\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |util.function|function\n',
        '\n-- ODESSEY BEGIN |util.table.inital_load|ddl\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |util.table.inital_load|ddl\n',
        '\n-- ODESSEY BEGIN |data fix|dml\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT 1;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n    \n-- ODESSEY END |data fix|dml\n'
    ]

    source_file_dict = [{'file': '/home/functions/function.sql', 'name': 'util.function'},
                        {'file': '/home/tables/table1.sql', 'name': 'util.table1'},
                        {'file': '/home/tables/table2.sql', 'name': 'util.table2'},
                        {'file': 'migrations/0001/up/meh.sql', 'name': 'util.table.inital_load'},
                        {'file': 'migrations/0001/up/data_fix.sql', 'name': 'datafix'},
                        ]

    config_dict = {'0001': {'up': [
                                    {'name': 'util', 'type': 'schema', 'action': 'create'},
                                    {'name': 'util.table1', 'type': 'table', 'action': 'create'},
                                    {'name': 'util.table1', 'type': 'table', 'action': 'drop'},
                                    {'name': 'util.table2', 'type': 'table', 'action': 'create'},
                                    {'name': 'util.function', 'type': 'function', 'action': 'create'},
                                    {'name': 'util.table.inital_load', 'type': 'ddl', 'action': 'execute', 'location': 'migrations/0001/up/meh.sql'},
                                    {'name': 'data fix', 'type': 'dml', 'action': 'execute', 'location': 'migrations/0001/up/data_fix.sql'}
                                    ],
                            'down': [{'name': 'data fix', 'type': 'dml', 'action': 'execute', 'location': 'migrations/0001/down/data_fix.sql'}, {'name': 'util.table3', 'type': 'ddl', 'action': 'execute', 'location': 'migrations/0001/down/meh.sql'}, {'name': 'util.function', 'type': 'function', 'action': 'drop'}, {'name': 'util.table2', 'type': 'table', 'action': 'drop'}, {'name': 'util', 'type': 'schema', 'action': 'drop'}]}, '0002': {'up': [{'name': 'sandbox', 'type': 'schema', 'action': 'create'}], 'down': [{'name': 'sandbox', 'type': 'schema', 'action': 'drop'}]}}
    with patch('builtins.open', mock_open(read_data=sql_source)) as mock_file:
        result = builder.build_up_migration(
            '0001', config_dict, source_file_dict)
    assert len(result) == len(expected_result)
    assert result == expected_result


@pytest.mark.builder
def test_build_down_migration(mocker, builder, tmpdir):
    good_sql_source = """
    -- ODESSEY BEGIN |util.function|function

    CREATE OR REPLACE FUNCTION util.function()
    RETURNS VOID AS
    $BODY$
        DECLARE v_sql = text();
        BEGIN;
            SELECT ROLLED BACK VERSION;
        END;
    $BODY$
    LANGUAGE plpgsql;

    -- ODESSEY END |util.function|function
    """

    bad_sql_source = """
    CREATE TABLE util.table1
    (
        id SERIAL
    )
    DISTRIBUTED BY(id);
    """

    expected_result = [
                        '\n-- ODESSEY BEGIN |util.function|function\n\n\n    CREATE OR REPLACE FUNCTION util.function()\n    RETURNS VOID AS\n    $BODY$\n        DECLARE v_sql = text();\n        BEGIN;\n            SELECT ROLLED BACK VERSION;\n        END;\n    $BODY$\n    LANGUAGE plpgsql;\n\n    \n-- ODESSEY END |util.function|function\n',
                        '\n-- ODESSEY BEGIN |util.table1|table\n\n    CREATE TABLE util.table1\n    (\n        id SERIAL\n    )\n    DISTRIBUTED BY(id);\n    \n-- ODESSEY END |util.table1|table\n'
                        ]

    source_file_dict = [{'file': '/home/functions/function.sql', 'name': 'util.function'},
                        {'file': '/home/tables/table1.sql', 'name': 'util.table1'},
                        {'file': '/home/tables/table2.sql', 'name': 'util.table2'},
                        {'file': 'migrations/0001/up/meh.sql', 'name': 'util.table.inital_load'},
                        {'file': 'migrations/0001/up/data_fix.sql', 'name': 'datafix'},
                        ]

    gen_up_names = [f"{x:0>4}_up.sql" for x in list(range(1, 31))]
    gen_down_names = [f"{x:0>4}_down.sql" for x in list(range(1, 31))]

    #td = tmpdir.mkdir("migrations")
    td = builder.MIGRATION_FOLDER
    files = []
    for file in gen_up_names:
        f = Path(td) / file
        files.append(str(f))
        if f.name == '0001_up.sql':
            f.write_bytes(good_sql_source.encode())
        elif f.name == '0002_up.sql':
            f.write_bytes(good_sql_source.encode())
        elif f.name == '0006_up.sql':
            f.write_bytes(bad_sql_source.encode())
        else:
            f.write_bytes("Filler Text".encode())

    config_dict = {'0001': {'up': [
                                   {'name': 'util', 'type': 'schema', 'action': 'create'},
                                   {'name': 'util.table1', 'type': 'table', 'action': 'create'},
                                   {'name': 'util.table1', 'type': 'table', 'action': 'drop'},
                                   {'name': 'util.table2', 'type': 'table', 'action': 'create'},
                                   {'name': 'util.function', 'type': 'function', 'action': 'create'},
                                   {'name': 'util.table3', 'type': 'ddl', 'action': 'execute', 'location': 'migrations/0001/up/meh.sql'},
                                   {'name': 'data fix', 'type': 'dml', 'action': 'execute', 'location': 'migrations/0001/up/data_fix.sql'}
                                   ],
                                'down': [
                                    {'name': 'data fix', 'type': 'dml', 'action': 'execute', 'location': 'migrations/0001/down/data_fix.sql'},
                                     {'name': 'util.table3', 'type': 'ddl', 'action': 'execute', 'location': 'migrations/0001/down/meh.sql'},
                                     {'name': 'util.function', 'type': 'function', 'action': 'drop'},
                                     {'name': 'util.table2', 'type': 'table', 'action': 'drop'},
                                     {'name': 'util', 'type': 'schema', 'action': 'drop'}
                                     ]
                    }, '0002':
                            {'up': [
                                    {'name': 'sandbox', 'type': 'schema', 'action': 'create'}
                                    ],
                            'down': [
                                    {'name': 'sandbox', 'type': 'schema', 'action': 'drop'}
                                    ]
                    }, '0003': {'up': [
                                    {'name': 'util.function', 'type': 'function', 'action': 'create'}
                                    ],
                                'down': [
                                    {'name': 'util.function', 'type': 'function', 'action': 'rollback'},
                                    {'name': 'util.table1', 'type':'table', 'action': 'create'}
                                    ]
                                }
                    }

    with patch('builtins.open', mock_open(read_data=bad_sql_source)) as mock_file:
        result = builder.build_down_migration(build_number='0003', config=config_dict, source_file_info=source_file_dict)

    assert result == expected_result