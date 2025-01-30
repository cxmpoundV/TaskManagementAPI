import psycopg2
from psycopg2.extras import RealDictCursor

con = psycopg2.connect(host = 'localhost',database = 'postgres',user = 'postgres',password = '6625099', cursor_factory=RealDictCursor)

cursor = con.cursor()
