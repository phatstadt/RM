import pandas as pd
import matplotlib.pyplot as plt
import math

def drawdown2(df2, strField, liste, dthres, uthres, run_down, append):


    df = df2.copy()
    df = df.dropna(subset=[strField])
    prevmaxi = df.index.min()
    prevmini = df.index.min()
    maxi = df.index.min()


    if not run_down:
        df[strField] = -df[strField]
        mult = -1
        strDraw = 'drawup'
    else:
        mult = 1
        strDraw = 'drawdown'


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

    if run_down:
        if (pct_chg > dthres):
            return (prevmini, prevmaxi, False)
        else:
            # test for up reversal
            list_up = []
            (xmin, xmax, upTest) = drawdown2(df_current, strField, list_up, dthres, uthres, False, False)
            if not upTest:
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
                print("%s rejected. Number of bull reversals: %s " % (strDraw, len(list_up)))
                ''' next need to take left and right split df's '''
                df_split_before = df_current[df_current.index < xmin].copy()
                df_split_after = df_current[df_current.index > xmax].copy()
                try:
                    print('split - running before df')
                    drawdown2(df_split_before, strField, liste, dthres, uthres, True, True)
                except:
                    print('split - before')
                    print(df_split_before)
                try:
                    print('split - running after df')
                    drawdown2(df_split_after, strField, liste, dthres, uthres, True, True)
                except:
                    print('split - after')
                    print(df_after)
                return(prevmini, prevmaxi, True)

            ''' run main level before and after '''
            try:
                print('running before df')
                drawdown2(df_before, strField, liste, dthres, uthres, True, True)
            except:
                print('before')
                print(df_before)
            try:
                print('running after df')
                drawdown2(df_after, strField, liste, dthres, uthres, True, True)
            except:
                print('after')
                print(df_after)

            return (prevmini, prevmaxi, False)

    else:  # run_up
        if (pct_chg < uthres):
            return (prevmini, prevmaxi, False)
        else:
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
                print("%s found. list size is: %s " % (strDraw, len(liste)))
                try:
                    drawdown2(df_before, strField, liste, dthres, uthres, run_down, append)
                except:
                    print('before')
                    print(df_before)
                try:
                    drawdown2(df_after, strField, liste, dthres, uthres, run_down, append)
                except:
                    print('after')
                    print(df_after)

            return (prevmini, prevmaxi, True)


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

