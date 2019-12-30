import os
from unittest import TestCase

import psycopg2


def test_conn_env_vars():
    params = ("tut_user", "tut_password", "tut_port", "tut_dbname")
    for param in params:
        assert os.environ.get(param)


class TestDbConn(TestCase):
    def setUp(self):
        self.conn = psycopg2.connect(
            dbname=os.environ.get("tut_dbname"),
            user=os.environ.get("tut_user"),
            password=os.environ.get("tut_password"),
            port=os.environ.get("tut_port"),
        )

    def test_db_postgis(self):
        """
        Test that the PostGIS extension is installed
        """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM pg_extension")
        query = cur.fetchall()

        # fetchall returns list of tuples of every extension
        assert "postgis" in (x[0] for x in query)

        cur.close()

    def test_db_rel_comp(self):
        """
        Test the table exists with our defined fields
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'company';"
        )

        for field in ("id", "name", "latitude", "longitude", "geom"):
            assert field in cur.fetchone()

        cur.close()

    def test_insert_rel_comp(self):
        """
        Test table accepts data inserted
        """

        # first, insert data
        cur = self.conn.cursor()
        lat = 45.543
        lon = -74.456
        cur.execute(
            f"INSERT INTO company VALUES(10001, 'geosimple', {lat}, {lon}, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326));"
        )
        # close to save changes
        cur.close()

        # second, retrieve data
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Company WHERE id=10001")
        result = cur.fetchone()

        # show tuple of element retrieved for debugging
        print(result)

        # geometry excluded because it is serialized
        for field in (10001, "geosimple", lat, lon):
            assert field in result

        assert len(result) == 5

        # third, clean it up
        cur.execute("DELETE FROM Company where id=0001")
        cur.close()

    def test_trigger_insert_rel_comp(self):
        """
        Test table accepts data inserted without point geometry
        Trigger should automatically generate geometry
        """

        # first, insert data
        cur = self.conn.cursor()
        lat = 45.543
        lon = -74.456
        cur.execute(f"INSERT INTO company VALUES(10001, 'geosimple', {lat}, {lon});")
        # close to save changes
        cur.close()

        # second, retrieve data
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Company WHERE id=10001")
        result = cur.fetchone()

        # show tuple of element retrieved for debugging
        print(result)

        for field in (10001, "geosimple", lat, lon):
            assert field in result

        assert len(result) == 5

        # geometry last element of table
        assert result[-1] is not None

        # third, clean it up
        cur.execute("DELETE FROM Company where id=0001")
        cur.close()

    def tearDown(self):
        self.conn.close()
