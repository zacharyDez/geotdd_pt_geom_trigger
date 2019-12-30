import os


def test_conn_env_vars() -> None:
    params = ("tut_user", "tut_password", "tut_port", "tut_dbname")
    for param in params:
        assert os.environ.get(param)
