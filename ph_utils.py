import xlwings as xw
import ph_accessconnect as ph_conn
import pandas as pd
import ast
import ph_var as var
import ph_drawdown as phd
import ph_factor_analysis as phf
import ph_risk as phr


@xw.sub
def get_sec_ref_db(db_name, dump):
    """Reads SecRefDB from Access"""
    sec_ref_df = ph_conn.connect(db_name, 'SELECT * from SecRefDB')
    if __name__ != '__main__':
        wb = xw.Book.caller()
        if dump:
            db_summary = calc_sec_ref_db_dates(sec_ref_df, db_name)
            del db_summary['START_DATE'], db_summary['END_DATE'], db_summary['PROCESSED'], db_summary['PX_LAST_min'], \
                db_summary['TF_x'], db_summary['PX_LAST_max'], db_summary['TF_y']
            wb.sheets('secrefdb').range(3, 1).value = db_summary
            wb.sheets('static').range('N_SEC_REF_ROWS').value = db_summary.shape[0]
            wb.sheets('static').range('N_SEC_REF_COLS').value = db_summary.shape[1]
            print()

    return sec_ref_df


@xw.sub
def get_sec_ref_db_wrapper():
    wb = xw.Book.caller()
    db_name = wb.sheets('main').range('DB_NAME').value
    get_sec_ref_db(db_name, True)
    return 1

@xw.sub
def calc_sec_ref_db_dates(sRefDF, db_name):
    strSQL = """SELECT DISTINCT PH_SEC_ID, TRADE_DATE, PX_LAST
                FROM SecHistDB AS T1
                INNER JOIN (SELECT PH_SEC_ID AS PHID, MAX(TRADE_DATE) AS MAX_DATE, MIN(TRADE_DATE) AS MIN_DATE
                FROM SecHistDB
                GROUP BY PH_SEC_ID) AS T2
                ON T1.PH_SEC_ID = T2.PHID
                AND (T1.TRADE_DATE = T2.MAX_DATE OR T1.TRADE_DATE = T2.MIN_DATE)
                ORDER BY PH_SEC_ID, TRADE_DATE;"""
    sec_df = ph_conn.connect(db_name, strSQL)
    sec_df.drop_duplicates(inplace=True)
    sec_df.sort_values(['PH_SEC_ID', 'TRADE_DATE'], ascending=[True,True], inplace=True)
    TrueFalse = []
    for t in range(0, len(sec_df.PH_SEC_ID.unique())):
        TrueFalse.extend([True, False])

    if (len(sec_df) != len(TrueFalse)):
        print('Error in calc_sec_ref_db_dates. One data point has only one value')
        return

    sec_df['TF'] = TrueFalse
    DF_min = sec_df[sec_df.TF == True].rename(columns={'TRADE_DATE': 'DATE_MIN', 'PX_LAST': 'PX_LAST_min'})
    DF_max = sec_df[sec_df.TF == False].rename(columns={'TRADE_DATE': 'DATE_MAX', 'PX_LAST': 'PX_LAST_max'})
    df2 = DF_min.merge(DF_max, on='PH_SEC_ID', how='left')
    DF_merger = sRefDF.merge(df2, on='PH_SEC_ID', how='outer')
    DF_merger = DF_merger[DF_merger['PH Type'].notnull()]
    print(DF_merger)
    return DF_merger


@xw.sub
def remove_non_numeric(df, field):
    num_df = (df.drop(field, axis=1)
             .join(df[field].apply(pd.to_numeric, errors='coerce')))
    num_df = num_df[num_df[field].notnull().all(axis=1)]
    return num_df


@xw.sub
def build_combined_df(db_name, sec_ref_df):
    wb = xw.Book.caller()
    tk_exo = wb.sheets('filters').range('EXO_LIST').value
    tk_endo = wb.sheets('filters').range('ENDO_LIST').value
    startdate = wb.sheets('filters').range('START_DATE').value
    sdate = str(startdate.strftime("%Y-%m-%d"))
    enddate = wb.sheets('filters').range('END_DATE').value
    edate = str(enddate.strftime("%Y-%m-%d"))
    ltk_exo = ast.literal_eval(tk_exo)
    ltk_endo = ast.literal_eval(tk_endo)
    ltk = ltk_endo + ltk_exo
    ltksql = str(ltk)
    ltksql = ltksql.replace("[", "(")
    ltksql = ltksql.replace("]", ")")
    strSQL = 'SELECT PH_SEC_ID, TRADE_DATE, PX_LAST FROM SecHistDB WHERE PH_SEC_ID IN ' + ltksql +' AND TRADE_DATE >= #'  + sdate + '# AND TRADE_DATE < #' + edate + '# ORDER BY TRADE_DATE ASC;'
    df = ph_conn.connect(db_name, strSQL)
    df = clean_and_rescale_data_by_ph_scaling_factor(df, sec_ref_df)
    df1 = None
    df2 = None
    if len(df) > 0:
        df.sort_values(['TRADE_DATE'], ascending=True, inplace=True)
        df2 = one_col_to_many(df)
        df1 = alignDatesinDF(df, ltk_endo, ltk_exo)
    return (df, df1, df2)


@xw.sub
def alignDatesinDF(df, ltk_endo, ltk_exo):
    df_endo = df[df['PH_SEC_ID'] == ltk_endo[0]].reset_index(drop=True)
    s = 'e' + str(ltk_endo[0])
    df_endo = df_endo.rename(columns={'PX_LAST': s})
    df_endo.drop(['PH_SEC_ID'], axis=1, inplace=True)
    dataframe_collection = {}
    i = 0
    for tk in ltk_exo:
        i += 1
        df1 = df[df['PH_SEC_ID'] == tk].reset_index(drop=True)
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
def clean_and_rescale_data_by_ph_scaling_factor(df, sec_ref_df):
    df2 = df.copy()
    df2 = df2[df2['PX_LAST'] != '#N/A N/A']
    df2['PX_LAST'] = df2['PX_LAST'].astype('float')
    sec_list = df2['PH_SEC_ID'].unique()
    for sec in sec_list:
        rec = sec_ref_df[sec_ref_df['PH_SEC_ID'] == float(sec)]
        scalar = rec.iloc[0, rec.columns.get_loc('PH_SCALING_FACTOR')]
        df2.loc[df2['PH_SEC_ID'] == sec, 'PX_LAST'] = df2.loc[df2['PH_SEC_ID'] == sec, 'PX_LAST'] * scalar

    return df2


@xw.sub
def one_col_to_many(df):
    df2 = df.copy()
    sec_list = df2['PH_SEC_ID'].unique()
    i = 0
    df_col = None
    for one_sec in sec_list:
        if i == 0:
            df_col = df2[df2['PH_SEC_ID'] == one_sec]
        else:
            dftmp = df2[df2['PH_SEC_ID'] == one_sec]
            df_col = df_col.merge(dftmp, how='outer', left_on='TRADE_DATE', right_on='TRADE_DATE')
        df_col.rename(columns={'PX_LAST': 'x' + str(one_sec)}, inplace=True)
        del df_col['PH_SEC_ID']
        i += 1

    df_col.sort_values(['TRADE_DATE'], ascending=True, inplace=True)
    return df_col


def adjReturn(dx, sec_ref_df, run_factor):
    print('adj_returns')
    global endostr
    df = dx.copy()
    cols = df.columns.tolist()
    for col in cols:
        if col[:1] == 'e' or col[:1] == 'x':
            if col[:1] == 'e':
                endostr = col + 'r'
            phid = col[1:]
            rec = sec_ref_df[sec_ref_df['PH_SEC_ID'] == float(phid)]
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
def gen_data():
    ''' init '''
    print('gen_data()')
    wb = xw.Book.caller()
    pd.options.display.large_repr = 'info'
    pd.options.display.max_rows = 100
    db_name = wb.sheets('main').range('DB_NAME').value
    sec_ref_df = get_sec_ref_db(db_name, False)
    '''generate all data frames'''
    (raw_df, aligned_df, raw_col_df) = build_combined_df(db_name, sec_ref_df)
    if len(raw_df) > 0:
        raw_df.to_csv(wb.sheets('main').range('CSV_PATH').value + 'raw_df.csv')
        raw_col_df.to_csv(wb.sheets('main').range('CSV_PATH').value + 'raw_col_df.csv')
        aligned_df.to_csv(wb.sheets('main').range('CSV_PATH').value + 'aligned_df.csv')
        if wb.sheets('main').range('GET_RAW_DATA').value:
            wb.sheets('raw_df').range(1, 1).value = raw_df
            wb.sheets('raw_col_df').range(1, 1).value = raw_col_df
            wb.sheets('aligned_df').range(1, 1).value = aligned_df
        if wb.sheets('main').range('CALC_RETURNS').value:
            ret_df = adjReturn(aligned_df, sec_ref_df, wb.sheets('filters').range('RUN_FACTOR').value)
            ret_df.to_csv(wb.sheets('main').range('CSV_PATH').value + 'ret_df.csv')
            if wb.sheets('main').range('GET_RAW_DATA').value:
                wb.sheets('ret_df').range(1, 1).value = ret_df


def inspect_data_wrapper():
    '''load df'''
    wb = xw.Book.caller()
    fname = wb.sheets('main').range('DF_CSV_NAME').value
    df = pd.read_csv(fname, index_col=0)
    fname = wb.sheets('main').range('INSPECT_CSV_NAME').value
    check_static_data(df, fname)


def check_static_data(df2, fname):
    df = df2.copy()
    wb = xw.Book.caller()
    n = int(wb.sheets('main').range('BAD_DATA_DAY_COUNT_THRESHOLD').value)
    f = open(fname, 'a')
    for col_str in df.columns:
        if col_str[0] == 'x':
            df['block'] = (df[col_str].shift(1) != df[col_str]).astype(int).cumsum()
            df_temp = df.block.value_counts()
            df_temp = df_temp[df_temp >= n]
            df.loc[df['block'].isin(df_temp.index.unique()) ,'plus_que_%s' % str(n)] = True
            df.loc[~df['block'].isin(df_temp.index.unique()) ,'plus_que_%s' % str(n)] = False
            for x in df_temp.index:
                df_rec = df[df['block'] == x]
                f.write("%s %s %s %s %s\n" % (col_str, df_rec.iloc[0][col_str], df_temp[x],
                                              df_rec.iloc[0]['TRADE_DATE'], df_rec.iloc[-1]['TRADE_DATE']))
    f.close()


@xw.sub
def analysis_menu():

    '''load df'''
    wb = xw.Book.caller()
    if wb.sheets('main').range('REGEN_DATA_BEFORE_RUN_ANALYSIS').value:
        gen_data()
    f_name = wb.sheets('main').range('CSV_PATH').value + 'ret_df.csv'
    final_df = pd.read_csv(f_name, index_col=0)
    print('loading %s' % f_name)

    '''Factor analysis'''
    if wb.sheets('filters').range('RUN_FACTOR').value:
        phf.factor_analysis(wb, final_df)

    '''VaR analysis'''
    if wb.sheets('filters').range('RUN_VAR').value:
        print('running VaR analysis')
        var.var_all(final_df)

    '''Risk analysis'''
    if wb.sheets('filters').range('RUN_RISK').value:
        print('running Risk analysis')
        wb.sheets('risk').range(1, 1).value = phr.run_risk(final_df)

    '''Draw down analysis'''
    if wb.sheets('filters').range('RUN_DRAWDOWN').value:
        phd.run_drawndown(wb, final_df)

    print('RUN FINISHED')

if __name__ == '__main__':
    # To run this with the debug server, set UDF_DEBUG_SERVER = True in the xlwings VBA module or in Dropdown menu
    xw.serve()
