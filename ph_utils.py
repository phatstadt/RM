import xlwings as xw
import ph_accessconnect as phconn
import pandas as pd
import ast
import statsmodels.api as sm
import statsmodels.formula.api as smf
# from matplotlib import style
import ph_var as var
import ph_drawdown as phd
import ph_plot as phplot

@xw.func
def double_sum(x, y):
    """Returns twice the sum of the two arguments"""
    return 3 * (x + y)

@xw.sub
def subTest():
    """Writes the name of the Workbook into Range("A1") of Sheet 1"""
    wb = xw.Book.caller()
    wb.sheets[0].range('A3').value = wb.name

@xw.sub
def getSecRefDB():
    """Reads SecRefDB from Access"""
    secRefDF = phconn.connect(db_name, 'SELECT * from SecRefDB')
    if __name__ != '__main__':
        wb = xw.Book.caller()
        if wb.sheets('main').range('LOAD_SEC_REF_DB').value:
            dbSummary = genDBSummary(secRefDF)
            del dbSummary['START_DATE'], dbSummary['END_DATE'], dbSummary['PROCESSED'], dbSummary['PX_LAST_min'], \
                dbSummary['TF_x'], dbSummary['PX_LAST_max'], dbSummary['TF_y']
            wb.sheets('secrefdb').range(1, 1).value = dbSummary
            wb.sheets('main').range('N_SEC_REF_ROWS').value = dbSummary.shape[0]
            wb.sheets('main').range('N_SEC_REF_COLS').value = dbSummary.shape[1]
            print()

    return secRefDF

@xw.sub
def genDBSummary(sRefDF):
    secDF = sRefDF.copy()
    strSQL = """SELECT DISTINCT PH_SEC_ID, TRADE_DATE, PX_LAST
                FROM SecHistDB AS T1
                INNER JOIN (SELECT PH_SEC_ID AS PHID, MAX(TRADE_DATE) AS MAX_DATE, MIN(TRADE_DATE) AS MIN_DATE
                FROM SecHistDB
                GROUP BY PH_SEC_ID) AS T2
                ON T1.PH_SEC_ID = T2.PHID
                AND (T1.TRADE_DATE = T2.MAX_DATE OR T1.TRADE_DATE = T2.MIN_DATE)
                ORDER BY PH_SEC_ID, TRADE_DATE;"""
    secDF = phconn.connect(db_name, strSQL)
    secDF.drop_duplicates(inplace=True)
    secDF.sort_values(['PH_SEC_ID', 'TRADE_DATE'], ascending=[True,True], inplace=True)
    TrueFalse = []
    for t in range(0, len(secDF.PH_SEC_ID.unique())):
        TrueFalse.extend([True, False])

    if (len(secDF) != len(TrueFalse)):
        print('Error in genDBSummary. One data point has only one value')
        return

    secDF['TF'] = TrueFalse
    DF_min = secDF[secDF.TF == True].rename(columns={'TRADE_DATE': 'DATE_MIN', 'PX_LAST': 'PX_LAST_min'})
    DF_max = secDF[secDF.TF == False].rename(columns={'TRADE_DATE': 'DATE_MAX', 'PX_LAST': 'PX_LAST_max'})
    df2 = DF_min.merge(DF_max, on='PH_SEC_ID', how='left')
    DF_merger = sRefDF.merge(df2, on='PH_SEC_ID', how='outer')
    DF_merger = DF_merger[DF_merger['PH Type'].notnull()]
    print(DF_merger)
    return DF_merger


@xw.sub
def buildCombinedDF():
    wb = xw.Book.caller()
    tk_exo = wb.sheets('main').range('EXO_LIST').value
    tk_endo = wb.sheets('main').range('ENDO_LIST').value
    startdate = wb.sheets('main').range('START_DATE').value
    sdate = str(startdate.strftime("%Y-%m-%d"))
    enddate = wb.sheets('main').range('END_DATE').value
    edate = str(enddate.strftime("%Y-%m-%d"))
    ltk_exo = ast.literal_eval(tk_exo)
    ltk_endo = ast.literal_eval(tk_endo)
    ltk = ltk_endo + ltk_exo
    n_exo = len(ltk_exo)
    n_endo = len(ltk_endo)
    n = len(ltk)
    ltksql = str(ltk)
    ltksql = ltksql.replace("[", "(")
    ltksql = ltksql.replace("]", ")")
    strSQL = 'SELECT PH_SEC_ID, TRADE_DATE, PX_LAST FROM SecHistDB WHERE PH_SEC_ID IN ' + ltksql +' AND TRADE_DATE >= #'  + sdate + '# AND TRADE_DATE < #' + edate + '# ORDER BY TRADE_DATE ASC;'
    df = phconn.connect(db_name, strSQL)
    df2 = one_col_to_many(df)
    df1 = alignDatesinDF(df, ltk_endo, ltk_exo)
    return (df, df1, df2)

@xw.sub
def one_col_to_many(df):

    df2 = df.copy()
    sec_list = df2['PH_SEC_ID'].unique()
    print(sec_list)
    i = 0
    for one_sec in sec_list:
        if i == 0:
            df_col = df2[df2['PH_SEC_ID'] == one_sec]
        else:
            dftmp = df2[df2['PH_SEC_ID'] == one_sec]
            df_col = df_col.merge(dftmp, how='outer', left_on='TRADE_DATE', right_on='TRADE_DATE')
        df_col.rename(columns={'PX_LAST': 'x' + str(one_sec)}, inplace=True)
        del df_col['PH_SEC_ID']
        i += 1

    return df_col

@xw.sub
def alignDatesinDF(df, ltk_endo, ltk_exo):
    df_endo = df[df['PH_SEC_ID'] == ltk_endo[0]].reset_index(drop=True)
    df_endo = df_endo[df_endo['PX_LAST'] != '#N/A N/A']
    df_endo['PX_LAST'] = df_endo['PX_LAST'].astype('float')
    s = 'e' + str(ltk_endo[0])
    global strEndoBase
    strEndoBase = s
    df_endo = df_endo.rename(columns={'PX_LAST': s})
    df_endo.drop(['PH_SEC_ID'], axis=1, inplace=True)
    dataframe_collection = {}
    i = 0
    for tk in ltk_exo:
        i += 1
        df1 = df[df['PH_SEC_ID'] == tk].reset_index(drop=True)
        df1 = df1[df1['PX_LAST'] != '#N/A N/A']
        df1['PX_LAST'] = df1['PX_LAST'].astype('float')
        if tk == 601:
            df1 = df1.rename(columns={'PX_LAST': 'rf'})
        else:
            df1 = df1.rename(columns={'PX_LAST': 'x' + str(tk)})

        df1.drop(['PH_SEC_ID'], axis=1, inplace=True)
        dataframe_collection[tk] = df1
        if i == 1:
            df_out = df_endo.merge(df1, how='inner', left_on='TRADE_DATE', right_on='TRADE_DATE')
        else:
            df_out = df_out.merge(df1, how='inner', left_on='TRADE_DATE', right_on='TRADE_DATE')

    return(df_out)

@xw.sub
def adjReturn(dx, run_factor):
    global endostr
    df = dx.copy()
    cols = df.columns.tolist()
    for col in cols:
        if col[:1] == 'e' or col[:1] == 'x':
            if col[:1] == 'e':
                endostr = col + 'r'
            phid = col[1:]
            rec = secRefDF[secRefDF['PH_SEC_ID'] == float(phid)]
            ret_lev = rec.iloc[0,rec.columns.get_loc('LEV_RET')]
            yield_flag = rec.iloc[0,rec.columns.get_loc('PH_YIELD_FLAG')]
            df[col + 'r'] = df[col].astype('float')
            if str(ret_lev) == 'LEVEL':
                if yield_flag:
                    df[col + 'r'] = df[col].diff()
                else:
                    df[col + 'r'] = df[col].pct_change()

    if run_factor:
        df[endostr + 'minusrf'] = df[endostr] - df['rf']

    return df


@xw.sub
def calcBetas(df):
    formula = ''
    cols = df.columns.tolist()
    i = 0
    formula = endostr + 'minusrf ~ '
    for col in cols:
        if col[:1] == 'x' and col[-1:] == 'r':
            i += 1
            if i == 1:
                formula += ' ' + col
            else:
                formula += ' + ' + col
    df = sm.add_constant(df)
    regOLS = smf.ols(formula=formula, data=df).fit()
    return regOLS


@xw.sub
def gen_data():
    ''' init '''
    wb = xw.Book.caller()
    pd.options.display.large_repr = 'info'
    pd.options.display.max_rows = 100
    global db_name
    global secRefDF
    db_name = 'D:\Dropbox\PH\_Work\Access\MacroData.accdb'

    '''generate return dataframe'''
    secRefDF = getSecRefDB()
    (raw_df, aligned_df, raw_col_df) = buildCombinedDF()
    ret_df = adjReturn(aligned_df, wb.sheets('main').range('RUN_FACTOR').value)
    if wb.sheets('main').range('GET_RAW_DATA').value:
        wb.sheets('raw_df').range(1,1).value = raw_col_df
        wb.sheets('aligned_df').range(1, 1).value = aligned_df
        wb.sheets('ret_df').range(1, 1).value = ret_df
#    datatail = int(wb.sheets('main').range('TAIL_SIZE').value)
#    if datatail != -1:
#        final_df = ret_df.tail(datatail)
#    else:
#        final_df = ret_df.copy()


    csv_ret_val = wb.sheets('main').range('CSV_RETURN_VAL').value
    if csv_ret_val == 'RAW':
        csv_df = raw_col_df
    elif csv_ret_val == 'ALIGNED':
        csv_df = aligned_df
    else:
        csv_df = ret_df

    fname = wb.sheets('main').range('DATAFRAME_CSV_PATH').value + 'df.csv'
    csv_df.to_csv(fname)


@xw.sub
def inspect_data():

    '''load df'''
    wb = xw.Book.caller()
    fname = wb.sheets('main').range('DATAFRAME_CSV_PATH').value + 'df.csv'
    df = pd.read_csv(fname, index_col=0)

    '''run full data quality analysis'''
    if wb.sheets('main').range('INSPECT_CHECK_BAD_DATA').value:
        check_static_data(df)

    '''analyze one variable'''
    var_id = wb.sheets('main').range('INSPECTED_VAR_NUM').value
    lili = []
    col_str = 'x' + str(int(var_id))
    phplot.plot_drawdown(df, col_str, 'TRADE_DATE', lili, 'inspect_var')


@xw.sub
def check_static_data(df2):
    df = df2.copy()
    wb = xw.Book.caller()
    n = int(wb.sheets('main').range('BAD_DATA_DAY_COUNT_THRESHOLD').value)
    fname = wb.sheets('main').range('DATAFRAME_CSV_PATH').value + 'check_data.csv'
    f = open(fname, 'w')

    for col_str in df.columns:
        if col_str[0] == 'x':
            df['block'] = (df[col_str].shift(1) != df[col_str]).astype(int).cumsum()
            df_temp = df.block.value_counts()
            df_temp = df_temp[df_temp >= n]
            df.loc[df['block'].isin(df_temp.index.unique()) ,'plus_que_%s' % str(n)] = True
            df.loc[~df['block'].isin(df_temp.index.unique()) ,'plus_que_%s' % str(n)] = False
            f.write("----------------------------------------------------\n")
            f.write("Var: %s\n" % col_str)
            for x in df_temp.index:
                df_rec = df[df['block'] == x]
                f.write("   Value: %s found %s times\n" % (df_rec.iloc[0][col_str], df_temp[x]))
                f.write("   start date: %s ; end date: %s\n" % (df_rec.iloc[0]['TRADE_DATE'],df_rec.iloc[-1]['TRADE_DATE']))

    f.close()

@xw.sub
def analysis_menu():

    '''load df'''
    wb = xw.Book.caller()
    fname = wb.sheets('main').range('DATAFRAME_CSV_PATH').value + 'df.csv'
    final_df = pd.read_csv(fname, index_col=0)

    '''factor analysis'''
    if wb.sheets('main').range('RUN_FACTOR').value:
        regOLS = calcBetas(final_df)
        print(regOLS.summary())
        wb.sheets('factor').range(2, 1).value = final_df
        wb.sheets('main').range('PY_REG_OUT').value = regOLS.params
        wb.sheets('main').range('PY_RSQ_OUT').value = regOLS.rsquared

    '''VaR analysis'''
    if wb.sheets('main').range('RUN_VAR').value:
        for str_col in final_df:
            if str_col[:1] == 'x' and str_col[-1:] != 'r':
                print(str_col)
                var.single_asset_var(final_df, str_col)

    '''drawdown analysis'''
    if wb.sheets('main').range('RUN_DRAWDOWN').value:
        if wb.sheets('main').range('DRAW_TYPE').value == 'DRAWDOWN':
            bool_draw = True
            thres = -abs(wb.sheets('main').range('DRAWDOWN_THRESHOLD').value)
            revthres = abs(wb.sheets('main').range('DRAWUP_THRESHOLD').value)
        else:
            bool_draw = False
            thres = abs(wb.sheets('main').range('DRAWDOWN_THRESHOLD').value)
            revthres = -abs(wb.sheets('main').range('DRAWUP_THRESHOLD').value)

        revthres_type = wb.sheets('main').range('RETRACE_THRESHOLD_TYPE').value
        sumsheet = 'ddsum'
        lili2 = []

        for strCol in final_df:
            if strCol[:1] == 'x' and strCol[-1:] != 'r':
                print()
                print(strCol)
                lili = []

                '''main call - return values unused'''
                x = phd.drawdown(final_df, strCol, lili, thres, revthres, bool_draw, True, True, revthres_type)
                lili2.extend(lili)
                print()
                df_ddthreshold = pd.DataFrame(lili,columns=['security', 'start_index', 'end_index', 'start_date',
                                                        'end_date', 'start_value', 'end_value', 'pct_chg'])
                df_ddthreshold = df_ddthreshold[['security', 'start_index', 'end_index', 'start_date',
                                                 'end_date', 'start_value', 'end_value', 'pct_chg']]
                df_ddthreshold.drop_duplicates(inplace=True)
                df_ddthreshold.sort_values(by='pct_chg', inplace=True)
                fname = strCol + '_down_'+ str(thres) + '_up_' + str(revthres) + '.png'
                phplot.plot_drawdown(final_df, strCol, 'TRADE_DATE', df_ddthreshold, fname)

        '''create aggregate output'''
        df_ddthreshold2 = pd.DataFrame(lili2, columns=['security', 'start_index', 'end_index', 'start_date',
                                                 'end_date', 'start_value', 'end_value', 'pct_chg'])
        df_ddthreshold2 = df_ddthreshold2[['security', 'start_index', 'end_index', 'start_date',
                                            'end_date', 'start_value', 'end_value', 'pct_chg']]
        df_ddthreshold2.drop_duplicates(inplace=True)
        df_ddthreshold2.sort_values(by=['security', 'pct_chg'], inplace=True, ascending=[True, True])
        wb.sheets(sumsheet).range(1, 1).value = df_ddthreshold2

        print()
        print('RUN FINISHED')
        return 1


if __name__ == '__main__':
    # To run this with the debug server, set UDF_DEBUG_SERVER = True in the xlwings VBA module or in Dropdown menu
    xw.serve()
