import pandas as pd
import matplotlib.pyplot as plt
import math

def drawdown(df2, strField, liste, incremental, indice, run_down=True):

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

    if pct_chg > indice:
        return
    else:
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
        try:
            drawdown(df_before, strField, liste, incremental, indice)
        except:
            print('before')
            print(df_before)
        try:
            drawdown(df_after, strField, liste, incremental, indice)
        except:
            print('after')
            print(df_after)


