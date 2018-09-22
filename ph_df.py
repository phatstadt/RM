import xlwings as xw
import pandas as pd

@xw.sub
def addColTo2DFSameDates(df1, df2):

#    add a value column from df2 and perform INNER on dates
#    df1,2 must be of form [date,close]

    print()
    print('******addColToDFSameDates***')
    print()
    df_out = df1.merge(df2, how='inner', left_on='TRADE_DATE', right_on='TRADE_DATE')
    return df_out


@xw.sub
def corr12(df):
    col1 = df.columns[1]
    col2 = df.columns[2]
    df[[col1, col2]] = df[[col1, col2]].apply(pd.to_numeric)
    print()
    print(df.corr())
    return df[col1].corr(df[col2])

if __name__ == '__main__':
    # To run this with the debug server, set UDF_DEBUG_SERVER = True in the xlwings VBA module or in Dropdown menu
    xw.serve()
