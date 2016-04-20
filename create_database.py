"""This script creates the initial schema of the database

"""
import psycopg2

### Connect to the tucson database (already created)
conn = psycopg2.connect(database="tucson", user="alex", host="/var/run/postgresql/",
                        port="5432")
print "Opened database successfully"

cursor = conn.cursor()

### Create tables/relations and table columns/fields

# Order to create tables in:

# (1) events
#     pEvent_id    primary key, regular integer, not null will be order 10^6
#     event_name   name of event, could limit to 250 characters
#     description  description of event, could limit to 1000 characters
#     price        DECIMAL(3,2)
cursor.execute('''CREATE TABLE events
       (pEvent_id   SERIAL PRIMARY KEY NOT NULL,
        event_name  TEXT NOT NULL,
        description TEXT  NOT NULL,
        price       DECIMAL(6,2));''')
       

# (2) venues: 
#     pVenue_id      INT           PRIMARY KEY  NOT NULL
#     venue_name     TEXT          NOT NULL
#     street address TEXT          NOT NULL
#     city_state     TEXT          NOT NULL
#     zip            INT
#     longitude      DECIMAL(8,5)
#     latitude       DECIMAL(8,5)
#     description    TEXT
#     hours_id       INT
#     service_flag   INT
#     (has_beer, has_coffee, has_food, has_liquor, has_wine)

# (3) hours:
#     pHours_id INT  PRIMARY KEY  NOT NULL
#     mon   BIGINT  NOT NULL
#     tue   BIGINT  NOT NULL
#     wed   BIGINT  NOT NULL
#     thur  BIGINT  NOT NULL
#     fri   BIGINT  NOT NULL
#     sat   BIGINT  NOT NULL
#     sun   BIGINT  NOT NULL

# don't think join tables are actively created?
# (3a) event_to_venue: 
#     event_id
#     venue_id

# (4) event_occurances
#     pOccurance_id   INT           PRIMARY KEY  NOT NULL
#     date            DATE          NOT NULL
#     delta_time      BIGINT
#     event_id        INT           NOT NULL
#     street address  TEXT          NOT NULL
#     city_state      TEXT          NOT NULL
#     zip             INT
#     longitude       DECIMAL(8,5)
#     latitude        DECIMAL(8,5)

# don't think join tables are actively created?
# (4a) occurance_to_venue 
#     occurance_id
#     venue_id

conn.commit()
conn.close()
print "Closed database successfully"
