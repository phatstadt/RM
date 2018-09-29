
def drawdown(df2, strField, liste, incremental, dthres, uthres, run_down=True):

    df = df2.copy()
    df = df.dropna(subset=[strField])
    if not run_down:
        df[strField] = -df[strField]
        mult = -1
    else:
        mult = 1

    prevmaxi = df.index.min()
    prevmini = df.index.min()
    maxi = df.index.min()

    for i in df.index.values:
        if df[strField][i] >= df[strField][maxi]:
            maxi = i
        else:
            # You can only determine the largest drawdown on a downward price!
            if (df[strField][maxi] - df[strField][i]) > (df[strField][prevmaxi] - df[strField][prevmini]):
                prevmaxi = maxi
                prevmini = i

    df_before = df[df.index < prevmaxi].copy()
    df_after = df[df.index > prevmini].copy()
    df_current = df[(df.index >= prevmaxi) & (df.index <= prevmini)].copy()
    pct_chg = (df[strField][prevmini] / df[strField][prevmaxi]) - 1

    if (pct_chg > dthres and run_down) or (pct_chg < uthres and not run_down):
        return
    else:
        # test for up reversal
        liste.append({
            'pct_chg': pct_chg,
            'maxi_index': prevmaxi,
            'mini_index': prevmini,
            'mini_date': df.loc[prevmini, 'TRADE_DATE'],
            'maxi_date': df.loc[prevmaxi, 'TRADE_DATE'],
            'mini_value': df.loc[prevmini, strField] * mult,
            'maxi_value': df.loc[prevmaxi, strField] * mult,
            'security': strField,
        })
        print("list size is: %s " % (len(liste), ))
        try:
            drawdown(df_before, strField, liste, incremental, dthres, uthres, run_down=True)
        except:
            print('before')
            print(df_before)
        try:
            drawdown(df_after, strField, liste, incremental, dthres, uthres, run_down=True)
        except:
            print('after')
            print(df_after)

import pandas as pd
import math

def drawdown2(df2, strField, liste, dthres, revthres, run_down, append, testReversal):


    '''return values are min_index, max_index and threshold test boolean'''
    print("dd called with sdate = %s ; edate = %s" % (df2['TRADE_DATE'].iloc[0], df2['TRADE_DATE'].iloc[-1]))
    df = df2.copy()
    df = df.dropna(subset=[strField])
    prevmaxi = df.index.min()
    prevmini = df.index.min()
    maxi = df.index.min()
    thres = -abs(dthres)
    revthres = -abs(revthres)

    if run_down:
        mult = 1
        strDraw = 'drawdown'
    else:
        df[strField] = -df[strField].abs()
        mult = -1
        strDraw = 'drawup'

    for i in df.index.values:
        if df[strField][i] >= df[strField][maxi]:
            maxi = i
        else:
            # You can only determine the largest drawdown on a downward price!
            if (df[strField][maxi] - df[strField][i]) > (df[strField][prevmaxi] - df[strField][prevmini]):
                prevmaxi = maxi
                prevmini = i

    df_before = df[df.index < prevmaxi].copy()
    df_after = df[df.index > prevmini].copy()
    df_current = df[(df.index >= prevmaxi) & (df.index <= prevmini)].copy()

    if run_down:
        pct_chg = (df[strField][prevmini] / df[strField][prevmaxi]) - 1
    else:
        pct_chg = 1 - (df[strField][prevmini] / df[strField][prevmaxi])

    if (pct_chg > thres):
        return (prevmini, prevmaxi, False)

    else:
        ''' run main level before and after '''
        try:
            print('running regular before df')
            drawdown2(df_before, strField, liste, abs(thres), revthres, True, True, True)
        except:
            print('before')
            print(df_before)
        try:
            print('running regular after df')
            drawdown2(df_after, strField, liste, abs(thres), revthres, True, True, True)
        except:
            print('after')
            print(df_after)

        if testReversal:
            print("reversal test with sdate = %s ; edate = %s" % (df_current['TRADE_DATE'].iloc[0], df_current['TRADE_DATE'].iloc[-1]))
            list_reversal = []
            (xmin, xmax, reversal) = drawdown2(df_current, strField, list_reversal, revthres, 10000, False, False, False)
            if not reversal:
                if append:
                    liste.append({
                        'pct_chg': pct_chg,
                        'maxi_index': prevmaxi,
                        'mini_index': prevmini,
                        'mini_date': df.loc[prevmini, 'TRADE_DATE'],
                        'maxi_date': df.loc[prevmaxi, 'TRADE_DATE'],
                        'mini_value': df.loc[prevmini, strField] * mult,
                        'maxi_value': df.loc[prevmaxi, strField] * mult,
                        'security': strField,
                    })
                    print("%s = %s found. start = %s end = %s. list size is: %s " % (strDraw, pct_chg,
                        prevmaxi, prevmini, len(liste)))

            else:
                print("Reversal. %s rejected." % strDraw)

                ''' next need to take left and right split df's '''
                if run_down:
                    df_split_before = df_current[df_current.index < xmin].copy()
                    df_split_after = df_current[df_current.index > xmax].copy()
                else:
                    df_split_before = df_current[df_current.index < xmax].copy()
                    df_split_after = df_current[df_current.index > xmin].copy()

                try:
                    print('running split before df')
                    drawdown2(df_split_before, strField, liste, abs(thres), revthres, True, True, True)
                except:
                    print('split - before')
                    print(df_split_before)
                try:
                    print('running split after df')
                    drawdown2(df_split_after, strField, liste, abs(thres), revthres, True, True, True)
                except:
                    print('split - after')
                    print(df_after)
                return(prevmini, prevmaxi, False)



        return (prevmini, prevmaxi, True)