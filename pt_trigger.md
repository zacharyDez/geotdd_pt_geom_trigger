# GeoTDD: Automated Point Geometry Generation from Lat/Lon

## Introduction

### Description of tutorial

We will be implementing an automated and tested workflow for creating a point geometry following the OGC conventions with PostGIS. 

We often have given coordinates of a point of interest, for example a list of geocoded addresses. Converting them to Point Geometry enables easy integration with all software (web or on-premise) that oblige to the OGC standard.

This procedure is often available in many software packages. The benefit of our approach is having an infrastructure that will automatically execute the procedure, store and make the data instantly available for rendering... without a single click.

This tutorial can also serve as a demonstration on using a test-driven approach for a more advanced feature: implementing a SQL trigger with spatial data.

### Tutorial Requirements

This tutorial requires you have PostgreSQL with the PostGIS extension installed on your computer or on a remote server. 

You will also need Python3 for this tutorial. If you're still on Python2, it is not longer supported by the Python Software foundation and you should upgrade to Python3.

Other python dependencies will be installed during the tutorial.

Working knowledge of Python and SQL is highly recommended.

### A Quick Word on TDD

Test Driven Development is a software approach where a test is first written before any application code. 

Having tests defines when a feature is actually done. It serves as a living technical specification of your application code. 

At the end of an iteration of your application using TDD, you not only have a working application but a way to continually and automatically test if it is still behaving in the intented manner. 

There many other benefits to TDD if you would like a more gentle introduction you can sign up to receive my [**Introduction to GeoTDD with Python**](zacharydeziel.com).

The type of testing done is this tutorial is referred to as integration testing. Integration tests rely on an exterior system to be executed. In our case, we are relying on the PostGIS database. 

### What is PostGIS?

PostGIS is the spatial extension for the open source database management system (DBMS) PostgreSQL and is one of the most common tools for handling large amounts of data (spatial and non-spatial). PostGIS leads the way for production GIS tools. 

It can be used for answering specific questions (queries) using the Standard Query Language (SQL).

For example, from the [docs](https://postgis.net/docs/manual-1.4/ch04.html), *What is the length of roads fully contained within each municipality?*

```sql
SELECT 
  m.name, 
  sum(ST_Length(r.the_geom))/1000 as roads_km 
FROM 
  bc_roads AS r,  
  bc_municipality AS m 
WHERE
  ST_Contains(m.the_geom,r.the_geom) 
GROUP BY m.name 
ORDER BY roads_km; 

name                        | roads_km
----------------------------+------------------ 
SURREY                      | 1539.47553551242 
VANCOUVER                   | 1450.33093486576 
LANGLEY DISTRICT            | 833.793392535662 
BURNABY                     | 773.769091404338 
PRINCE GEORGE               | 694.37554369147 
...
```

## Tutorial

## Testing our Setup

### Pytest Setup

TDD works in the following three steps:

1. Make a failing test (RED)
2. Make the test pass (GREEN)
3. Refactor your code (REFACTOR)

Before even creating our database, we are going to create a test that checks if the database exists. 

The testing infrastructure that we will be using is *pytest*. 

In your virtual environment, execute:

*terminal*
```bash
pip install pytest
```

To verify the installation:

*terminal*
```bash
pytest
```

The *pytest* framework will collect and execute all python files starting or ending with *test* in the filename. We will create a directory for our tests to keep them separate from application code.

Best practice conventions can be found in the [pytest docs](https://docs.pytest.org/en/latest/goodpractices.html).

```bash
.
├── pt_trigger.md
└── tests

1 directory, 1 file
```

### Environment variables

To avoid having a file containing our credentials, we are going to define environment variables that we will use to connect to our future database. That's right, we are deciding preemtively what those should be. 

But... hold that urge to directly export your environment variables! Obey the testing goat.

*tests/test_conn_vars.py*
```python
import os


def test_conn_env_vars() -> None:
    params = ('user', 'password', 'port', 'dbname')
    for param in params:
        assert os.environ.get(param)
```

When executing our tests with the command *pytest*, we hope to get a big **RED** error message because we haven't set our environment variables yet.

*terminal*
```bash
============================================================================ test session starts =============================================================================
collected 1 item                                                                                                                                                             

tests/test_conn_vars.py F                                                                                                                                              [100%]

================================================================================== FAILURES ==================================================================================
_____________________________________________________________________________ test_conn_env_vars _____________________________________________________________________________

    def test_conn_env_vars() -> None:
        params = ('user', 'password', 'port', 'dbname')
        for param in params:
>           assert os.environ.get(param)
E           AssertionError: assert None

```

Great! Exactly what we expected.

We can now set our envrionment variables (most likely different command if you are on a windows machine...):

*terminal*
```bash
export tut_user=postgres;
export tut_password=postgres;
export tut_dbname=pt_tut;
export tut_port=5430;
```

Now if we rerun our tests (again with the *pytest* command in the root directory), our single test should pass.

```bash
============================================================================ test session starts =============================================================================
platform darwin -- Python 3.7.1, pytest-4.0.2, py-1.7.0, pluggy-0.8.0
rootdir: /Volumes/dez_drive/business/content_marketing/geotdd/pt_trigger, inifile:
plugins: remotedata-0.3.1, openfiles-0.3.1, cov-2.6.1
collected 1 item                                                                                                                                                             

tests/test_conn_vars.py .                                                                                                                                              [100%]

========================================================================== 1 passed in 0.13 seconds ==========================================================================
```

Our tests passed as expected! 

### Why write test before any application code

The main reason we are writing our tests before and not after application code is to be certain that our tests are actually testing the intented behavior of the code.

If we would write our tests after that application code, they could be passing but we could not guarantee (in 100% of cases) that they are passing because our code is behaving as expected or that our tests are not actually testing the intented behavior.

### Database connection

Income *psycopg* the most popular postgres binding in Python. Psycopg is used to pass SQL commands to a PostgreSQL database. *Psycopg* is actually used in Django's Object Relational Mapper (ORM) when using a PostgreSQL database.

We can install the dependency with:

*terminal*
```bash
pip install psycopg2-binary
```

*Always look up pypi repositories before throwing them into your project dependencies blindly.*

If you've ever spent a lot of time writing SQL insertions to test the integrity of your database, you know that it is quite redundant, simple and boring. We can automate this constraint testing with psycopg.

But first, we must test that we can connect to a database given our environmental variables.

*tests/test_db_conn.py*
```python
import os
from unittest import TestCase

import psycopg2


class TestDbConn(TestCase):

    def test_db_conn(self):
        """
        Test that the user can connect given the connection parameters set as environment variables
        """
        conn = psycopg2.connect(dbname=os.environ.get('tut_dbname'), user=os.environ.get('tut_user'),
                                password=os.environ.get('tut_password'), port=os.environ.get('tut_port'))
        assert conn

    def tearDown(self):
        self.conn.close()
```

In this example, we introduce the TestCase class from the unittest module of Python standard library.

The TestCase gives us some basic fonctionnality such as the *tearDown* method used. The *tearDown* method is executed when all the tests of the class have been executed.

If we run our tests again, we get a failure and an error for our TestDbConn class. Sparing the verbose and clear message from pytest for length concerns, the failure is due to our test_db_conn() method being unable to connect to the database because it does not yet exist. The error is caused by our tearDown method being unable to close the non-existant connection.

Following TDD's rules (red, green, refactor), we can now create our database.

Using the *psql* to enter SQL command in the command line is the way I prefer to work. 

*terminal*
```bash
postgres=# CREATE DATABASE pt_tut;
CREATE DATABASE
```

Let's rerun our tests.

*terminal*
```bash
(pt_trigger) (base) Zacharys-MacBook-Pro:pt_trigger zac$ pytest
============================================================================ test session starts =============================================================================
platform darwin -- Python 3.7.2, pytest-5.3.2, py-1.8.1, pluggy-0.13.1
rootdir: /Volumes/dez_drive/business/content_marketing/geotdd/pt_trigger
collected 2 items                                                                                                                                                            

tests/test_conn_vars.py .                                                                                                                                              [ 50%]
tests/test_db_conn.py .                                                                                                                                                [100%]

============================================================================= 2 passed in 0.17s ==============================================================================
```

Success! We our able to connect to the database.

### Adding PostGIS to our database

We can list the extensions of a databases with the shortcut command:

```bash
postgres=# \dx

                 List of installed extensions
  Name   | Version |   Schema   |         Description          
---------+---------+------------+------------------------------
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
(1 row)
```

As you can see, PostGIS is not installed.

Let's once again go around the TDD wheel:

tests/test_db_postgis.py
```python
import os
from unittest import TestCase

import psycopg2


class TestDbPostGIS(TestCase):

    def setUp(self):
        self.conn = psycopg2.connect(dbname=os.environ.get('tut_dbname'), user=os.environ.get('tut_user'),
                                     password=os.environ.get('tut_password'), port=os.environ.get('tut_port'))

    def test_db_ext_postgis(self):
        """
        Test that the PostGIS extension is installed
        """
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM pg_extension')
        query = cur.fetchall()
        
        # fetchall returns list of tuples of every extension
        assert 'postgis' in [x[0] for x in query]
        
        cur.close()
        
    def tearDown(self):
        self.conn.close()
```

This time we bring in the *setUp* method to initiate our connection before executing any tests. 

If we execute our tests, an error is raised because PostGIS is not found.

We can add the extension to our database with:

*terminal*
```bash
pt_tut=#CREATE EXTENSION postgis;
CREATE EXTENSION
```

Let's rerun our tests.

*terminal*
```bash
(pt_trigger) (base) Zacharys-MacBook-Pro:pt_trigger zac$ pytest
============================================================================ test session starts =============================================================================
platform darwin -- Python 3.7.2, pytest-5.3.2, py-1.8.1, pluggy-0.13.1
rootdir: /Volumes/dez_drive/business/content_marketing/geotdd/pt_trigger
collected 3 items                                                                                                                                                            

tests/test_conn_vars.py .                                                                                                                                              [ 33%]
tests/test_db_conn.py .                                                                                                                                                [ 66%]
tests/test_db_postgis.py .                                                                                                                                             [100%]

============================================================================= 3 passed in 0.10s ==============================================================================
```

Passed! Alright a small refactor we could do is change our list comprehension with the extension names to a tuple to make it non-mutable:

tests/test_db_postgis.py
```python
[...]

assert 'postgis' in (x[0] for x in query)

[...]
```

We must rerun our tests to verify our refactor did not break anything. The tests passed on my setup but don't take my word for it, test it out!

### Create SQL Company Table

Alright, we should be getting the hang of this.

*tests/test_db_rel_comp.py*
```python
import os
from unittest import TestCase

import psycopg2


class TestDbRel(TestCase):

    def setUp(self):
        self.conn = psycopg2.connect(dbname=os.environ.get('tut_dbname'), user=os.environ.get('tut_user'),
                                     password=os.environ.get('tut_password'), port=os.environ.get('tut_port'))

    def test_db_rel_company(self):
        """
        Test that the PostGIS extension is installed
        """
        cur = self.conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'company';")
            
        for field in ['id', 'name', 'latitude', 'longitude', 'geom']:    
            assert field in cur.fetchone()

        cur.close()

    def tearDown(self):
        self.conn.close()
```

Let's make a simple company table that includes an *id*, a *name*, a *latitude* and a *longitude*.

*terminal*
```bash
pt_tut=# CREATE TABLE company(id serial, name varchar, latitude float, longitude float);
CREATE TABLE
```

Again, we run our tests... And yes they are passing!

You probably notice we are starting to repeat ourselves quite often with our setUp and tearDown method for every TestCase. There are different philosophies out there but to simplify the maintenance (thinking of the do not repeat yourself (DRY) principle), we should probably make a single TestCase from a multiple TestCase classes.

Here is our file structure of the tests directory:

tests
├── test_conn_vars.py
├── test_db_conn.py
├── test_db_postgis.py
└── test_db_rel_company.py


Let's move them to the same file and run our tests. 

*Best practice is commiting our previous changes in a source code management system (SCM) so we can rapidly revert back to our previous version if something goes wrong.*

tests
├── test_conn_vars.py
└── test_db.py

*tests/test_db.py*
```bash
import os
from unittest import TestCase

import psycopg2


class TestDbConn(TestCase):

    def setUp(self):
        self.conn = psycopg2.connect(dbname=os.environ.get('tut_dbname'), user=os.environ.get('tut_user'),
                                     password=os.environ.get('tut_password'), port=os.environ.get('tut_port'))

    def test_db_postgis(self):
        """
        Test that the PostGIS extension is installed
        """
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM pg_extension')
        query = cur.fetchall()

        # fetchall returns list of tuples of every extension
        assert 'postgis' in (x[0] for x in query)

        cur.close()

    def test_db_rel_comp(self):
        """
        Test the table exists with our defined fields
        """
        cur = self.conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'company';")

        for field in ('id', 'name', 'latitude', 'longitude', 'geom'):
            assert field in cur.fetchone()

        cur.close()

    def tearDown(self):
        self.conn.close()

```

Now that's cleaner and easier to maintain.

However, it would be nice to test out if we can properly insert data into this table. To make our tests initially fail, we can drop the company table:

*terminal*
```bash
pt_tut=# DROP TABLE Company;
DROP TABLE
```

For our test, we want to insert some data, see if we can retrieve if and finally clean up our test by deleting the data.

*tests/test_db.py Only new test method showed*
```python
    def test_insert_rel_comp(self):
        """
        Test table accepts data inserted
        """

        # first, insert data
        cur = self.conn.cursor()
        lat = 45.543
        lon = -74.456
        cur.execute(
            f"INSERT INTO company VALUES(10001, 'geosimple', {lat}, {lon}, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326));")
        # close to save changes
        cur.close()

        # second, retrieve data
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Company WHERE id=10001")
        result = cur.fetchone()

        # show tuple of element retrieved for debugging
        print(result)

        # geometry excluded because it is serialized
        for field in (1, 'geosimple', lat, lon):
            assert field in result

        assert len(result) == 5

        # third, clean it up
        cur.execute("DELETE FROM Company where id=10001")
        cur.close()
```

If we dropped our table, the tests fail with the following error:

*terminal*
```bash
psycopg2.errors.UndefinedTable: relation "company" does not exist
```

When executed with the table already existing, our new test passes.

### Trigger 

A trigger is an awesome tool to automate processes in a database. 

For our example, we will be creating a trigger that creates a point geometry automatically from a rows latitude and longitude. This will render us the possibility of inserting on the company table without specifying the longer method to create a poitn geometry.

Our tests to verify if the trigger work is similar to our last test on inserting data to the table.

*tests/test_db.py*
```python
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

        for field in (1, 'geosimple', lat, lon):
            assert field in result

        assert len(result) == 5

        # geometry last element of table
        assert result[-1] is not None

        # third, clean it up
        cur.execute("DELETE FROM Company where id=10001")
        cur.close()
```

If our tests accurately checks the Null (or None) value of the geometry column, or test will fail. The other assertions of the tests are useful in the sense that they check that the insertion is accepted even if a geometry column is not specified.

Time to get our hands dirty with some plpgsql!

```sql
CREATE OR REPLACE FUNCTION geom_from_lat_lon()
RETURNS TRIGGER AS
$$
   BEGIN
      NEW.geom = ST_SRID(ST_MakePoint(longitude, latitude), 4326);
      RETURN NEW;
   END;
$$
LANGUAGE plpgsql;

CREATE  TRIGGER add_company_geom
BEFORE INSERT ON Company
FOR EACH ROW EXECUTE PROCEDURE geom_from_lat_lon();
```

This may seem a little complicated at a first glance. Don't think you need to remember this syntax by heart. The Postgres [documentation](https://www.postgresql.org/about/news/1994/) covers most topics fairly well and there are tone of examples online.

Let's rerun our tests and see if we are able to generate a point geometry automatically!

Oups, a few errors popped up!The values latitude and longitude are not recognized. Let's fix that by specifying the latitude and longitude values are those of the NEW variable (Where NEW is the new row being inserted):

```sql
CREATE OR REPLACE FUNCTION geom_from_lat_lon()
RETURNS TRIGGER AS
$$
   BEGIN
      NEW.geom = ST_SRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
      RETURN NEW;
   END;
$$
LANGUAGE plpgsql;
```

We get another error after fixing the last one. This time it is a simple typo, we miscalled the ST_SetSRID function!

*final*
```sql
CREATE OR REPLACE FUNCTION geom_from_lat_lon()
RETURNS TRIGGER AS
$$
   BEGIN
      NEW.geom = ST_SRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
      RETURN NEW;
   END;
$$
LANGUAGE plpgsql;
```

All tests passed! 

## Grand Finally

I have been slowly adding all of our database commands to an SQL file. The ultimate test to see how easy it would to build our application on a clean system would to DROP our database and reexecute our commands.

*db_setup.sql*
```sql
-- changed working db
-- You must first create the database with
-- CREATE DATABASE pt_tut;

-- Must change database
-- With PSQL, if executing straight from CREATE DATABASE statement:
-- \c pt_tut;

CREATE EXTENSION postgis;

CREATE TABLE company(id serial PRIMARY KEY, name varchar, latitude float, longitude float, geom geometry);

CREATE OR REPLACE FUNCTION geom_from_lat_lon()
RETURNS TRIGGER AS
$$
   BEGIN
      NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
      RETURN NEW;
   END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER add_company_geom
BEFORE INSERT ON Company
FOR EACH ROW EXECUTE PROCEDURE geom_from_lat_lon();
```

And rerun the tests one last time!

## Conclusion

This tutorial was meant to present a cleaner way for building up your applications. The difficulty in TDD is breaking our hacky habits of piling one iteration over another of writing application code until it simply works (without knowing why it works). 

For those used to writing pseudo-code, the process might seem more intuitive. It is similar in the preemtive way we go about the craft of writing a program. The main difference with TDD is that we do not simply rely on plain text as specification of our program, we write automated tests to guarantee are code is behaving in the expected behavior.

You might of found this tutorial on the heavier side if you did not have any previous experience with PostGIS. Hopefully, it opened your eyes to the incredible features PostGIS has to offer.

*The final version of this tutorial is available on [github](https://github.com/zacharyDez/geotdd_pt_geom_trigger)

How did you find this tutorial? What are your first impressions of TDD? Any anger or ressentment?

If you feel like getting a little more background on TDD you can check out my post on the [Whys of TDD](https://github.com/zacharyDez/whys_of_testing).

Any comments or questions? Do not hesitate to reach out.