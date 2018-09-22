import pyodbc
import pandas as pd
from pandas import DataFrame

def connect(db_file, strQuery):
    """ Connect to database server """
    conn = None
    try:

        # read connection parameters
        user = 'admin'
        password = ''
        odbc_conn_str = 'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;UID=%s;PWD=%s' % \
                        (db_file, user, password)

        conn = pyodbc.connect(odbc_conn_str)
        df = pd.read_sql(strQuery, conn)

        '''
        cur = conn.cursor()
        cur.execute(strQuery)        
        result = cur.fetchall()
        df = DataFrame(result)
        df.columns = cur.keys()
        hd = []
        for i in range(0, len(cur.description)):
            hd.append(cur.description[i][0])
        close the communication
        cur.close()
        '''

        return df

    except (Exception, pyodbc.DatabaseError) as error:
        print(error)

    finally:
        if conn is not None:
            conn.close()
#            print('Database connection closed.')


if __name__ == '__main__':
    connect('D:\Dropbox\PH\_Work\Access\MacroData.accdb','SELECT * from SecRefDB')

