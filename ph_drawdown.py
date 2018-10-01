import pandas as pd

def ddbase(df2, str_field, thres):
    df = df2.copy()
    prev_first = df.index.min()
    prev_last = df.index.min()
    maxi = df.index.min()

    for i in df.index.values:
        if df[str_field][i] >= df[str_field][maxi]:
            maxi = i
        else:
            # You can only determine the largest drawdown on a downward price!
            if (df[str_field][maxi] - df[str_field][i]) > (df[str_field][prev_first] - df[str_field][prev_last]):
                prev_first = maxi
                prev_last = i

    pct_chg = (df[str_field][prev_last] / df[str_field][prev_first]) - 1
    pass_thres = False
    if pct_chg <= thres:
        pass_thres = True

    return(prev_first, prev_last, pct_chg, pass_thres)

def dubase(df2, str_field, thres):
    df = df2.copy()
    df[str_field] = -df[str_field]
    (prev_first, prev_last, pct_chg, pass_thres) = ddbase(df, str_field, 1.0)
    pct_chg = (df[str_field][prev_last] / df[str_field][prev_first]) - 1
    pass_thres = False
    if pct_chg >= thres:
        pass_thres = True
    return (prev_first, prev_last, pct_chg, pass_thres)

def dbase(df2, str_field, run_down, thres):

    if run_down:
        x = ddbase(df2, str_field, thres)
    else:
        x = dubase(df2, str_field, thres)

    return x


def drawdown(df2, str_field, liste, thres, revthres, run_down, append, testReversal, rev_threshold_type):

    '''return values are min_index, max_index and threshold pass test boolean'''

    df = df2.copy()
    df = df.dropna(subset=[str_field])

    if run_down:
        str_draw = 'drawdown'
    else:
        str_draw = 'drawup'

    print("%s called with sdate = %s ; edate = %s" % (str_draw, df2['TRADE_DATE'].iloc[0], df2['TRADE_DATE'].iloc[-1]))

    (prev_first, prev_last, pct_chg, pass_thres) = dbase(df2, str_field, run_down, thres)
    df_before = df[df.index < prev_first].copy()
    df_after = df[df.index > prev_last].copy()
    df_current = df[(df.index >= prev_first) & (df.index <= prev_last)].copy()

    if not pass_thres:
        return (prev_first, prev_last, False)
    else:
        ''' run main level before and after '''
        try:
            # print('running regular before df')
            if len(df_before) > 0:
                drawdown(df_before, str_field, liste, thres, revthres, run_down, True, True, rev_threshold_type)
        except:
            print('exception in base level before df')
            print(df_before)
        try:
            # print('running regular after df')
            if len(df_after) >0:
                drawdown(df_after, str_field, liste, thres, revthres, run_down, True, True, rev_threshold_type)
        except:
            print('exception in base level after df')
            print(df_after)

        if testReversal:
            print("reversal %s test with sdate = %s ; edate = %s" % (not(run_down), df_current['TRADE_DATE'].iloc[0], df_current['TRADE_DATE'].iloc[-1]))
            list_reversal = []
            if rev_threshold_type == 'REL':
                revthres2 = abs(revthres) * -pct_chg
            else:
                revthres2 = revthres

            (xmin, xmax, reversal) = drawdown(df_current, str_field, list_reversal, revthres2, 10000, not(run_down), False, False, rev_threshold_type)
            if not reversal:
                if append:
                    liste.append({
                        'pct_chg': pct_chg,
                        'start_index': prev_first,
                        'end_index': prev_last,
                        'end_date': df.loc[prev_last, 'TRADE_DATE'],
                        'start_date': df.loc[prev_first, 'TRADE_DATE'],
                        'end_value': df.loc[prev_last, str_field],
                        'start_value': df.loc[prev_first, str_field],
                        'security': str_field,
                    })
                    print("draw_down: %s = %s found. start = %s end = %s. list size is: %s " % (not(run_down), pct_chg,
                        df_current['TRADE_DATE'].loc[prev_first], df_current['TRADE_DATE'].loc[prev_last], len(liste)))

            else:
                print("*** Reversal. %s rejected; threshold = %s " % (not(run_down), revthres2))

                ''' next need to take left and right split df's '''
                df_split_before = df_current[df_current.index < xmin].copy()
                df_split_after = df_current[df_current.index > xmax].copy()

                try:
                    # print('running split before df')
                    if len(df_split_before) > 0:
                        drawdown(df_split_before, str_field, liste, thres, revthres, run_down, True, True, rev_threshold_type)
                except:
                    print('exception split - before')
                    print(df_split_before)
                try:
                    # print('running split after df')
                    if len(df_split_after) > 0:
                        drawdown(df_split_after, str_field, liste, thres, revthres, run_down, True, True, rev_threshold_type)
                except:
                    print('exception split - after')
                    print(df_after)
                return(prev_last, prev_first, False)


        return (prev_last, prev_first, True)