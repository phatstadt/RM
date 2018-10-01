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
    print(secRefDF.info())
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
    secDF.sort_values(['PH_SEC_ID','TRADE_DATE'], ascending=[True,True], inplace=True)
    TrueFalse = []
    for t in range(0, len(secDF.PH_SEC_ID.unique())):
        TrueFalse.extend([True, False])

    secDF['TF'] = TrueFalse
    DF_min = secDF[secDF.TF == True].rename(columns={'TRADE_DATE': 'DATE_MIN', 'PX_LAST': 'PX_LAST_min'})
    DF_max = secDF[secDF.TF == False].rename(columns={'TRADE_DATE': 'DATE_MAX', 'PX_LAST': 'PX_LAST_max'})
    df2 = DF_min.merge(DF_max, on='PH_SEC_ID', how='left')
    DF_merger = sRefDF.merge(df2, on='PH_SEC_ID', how='outer')
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
    df1 = alignDatesinDF(df, ltk_endo, ltk_exo)
    return df1


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
    i=0
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
def adjReturn(dx):
    global endostr
    df = dx.copy()
    cols = df.columns.tolist()
    for col in cols:
        if col[:1] == 'e' or col[:1] == 'x':
            if col[:1] == 'e':
                endostr = col + 'r'
            phid = col[1:]
            rec = secRefDF[secRefDF['PH_SEC_ID'] == float(phid)]
            retlev = rec.iloc[0,rec.columns.get_loc('LEV_RET')]
            df[col + 'r'] = df[col].astype('float')
            if str(retlev) == 'LEVEL':
                df[col + 'r']= df[col].pct_change()
 #               df.loc[:,col +'r'] *= 100.0

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
def PHReg():
    ''' init '''
    wb = xw.Book.caller()
    pd.options.display.large_repr = 'info'
    pd.options.display.max_rows = 100
    global db_name
    global secRefDF
    datatail = int(wb.sheets('main').range('TAIL_SIZE').value)
    db_name = 'D:\Dropbox\PH\_Work\Access\MacroData.accdb'


    '''generate return dataframe'''
    secRefDF = getSecRefDB()
    x = buildCombinedDF()
    xret = adjReturn(x)
    if datatail != -1:
        xtail = xret.tail(datatail)
    else:
        xtail = xret.copy()


    '''factor analysis'''
    if wb.sheets('main').range('RUN_FACTOR').value:
        regOLS = calcBetas(xtail)
        print(regOLS.summary())
        wb.sheets('factor').range(2, 1).value = xtail
        wb.sheets('main').range('PY_REG_OUT').value = regOLS.params
        wb.sheets('main').range('PY_RSQ_OUT').value = regOLS.rsquared


    '''VaR analysis'''
    if wb.sheets('main').range('RUN_VAR').value:
        print(xret.tail(10))
        var.single_asset_var(xret, strEndoBase)


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

        for strCol in xret:
            if strCol[:1] == 'x' and strCol[-1:] != 'r':
                print()
                print(strCol)
                lili = []

                '''main call - return values unused'''
                x = phd.drawdown(xret, strCol, lili, thres, revthres, bool_draw, True, True, revthres_type)
                lili2.extend(lili)
                print()
                df_ddthreshold = pd.DataFrame(lili,columns=['security', 'start_index', 'end_index', 'start_date',
                                                        'end_date', 'start_value', 'end_value', 'pct_chg'])
                df_ddthreshold = df_ddthreshold[['security', 'start_index', 'end_index', 'start_date',
                                                 'end_date', 'start_value', 'end_value', 'pct_chg']]
                df_ddthreshold.sort_values(by='pct_chg', inplace=True)
                fname = strCol + '_down_'+ str(thres) + '_up_' + str(revthres) + '.png'
                phplot.plot_drawdown(xret, strCol, 'TRADE_DATE', df_ddthreshold, fname)

        '''create aggregate output'''
        df_ddthreshold2 = pd.DataFrame(lili2, columns=['security', 'start_index', 'end_index', 'start_date',
                                                 'end_date', 'start_value', 'end_value', 'pct_chg'])
        df_ddthreshold2 = df_ddthreshold2[['security', 'start_index', 'end_index', 'start_date',
                                            'end_date', 'start_value', 'end_value', 'pct_chg']]
        df_ddthreshold2.sort_values(by=['security', 'pct_chg'], inplace=True, ascending=[True, True])
        wb.sheets(sumsheet).range(1, 1).value = df_ddthreshold2

        print()
        print('RUN FINISHED')
        return 1


if __name__ == '__main__':
    # To run this with the debug server, set UDF_DEBUG_SERVER = True in the xlwings VBA module or in Dropdown menu
    xw.serve()
