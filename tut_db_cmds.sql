-- You must first create the database with
-- CREATE DATABASE pt_tut;

-- Must change database
-- In PSQL:
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