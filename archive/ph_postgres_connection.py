import psycopg2
import sys

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = "host='localhost' dbname='mktdata' user='postgres' password='hotshot'"

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(params)
        cur = conn.cursor()
        cur.execute('SELECT * from Public."SecHistDB"')
        result=cur.fetchall()
        for row in result:
            print("{} | {} | {} | {} | {} ".format(row[0],row[1],row[2],row[3],row[4]))

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


if __name__ == '__main__':
    connect()

