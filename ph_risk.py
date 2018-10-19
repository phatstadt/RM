import ph_math as phm
import numpy as np
import pandas as pd


def inv_cdf_array(df_final):

    bin_num = 1000
    df = pd.DataFrame(index=np.arange(0, bin_num+1, 1))
    i = 0
    func_array = []
    for col in df_final.columns:
        if col[:1] == 'x' and col[-1] == 'r':
            i = i+1
            cdf, bin_edges = phm.gen_cdf(df_final, col, bin_num)
            inv_cdf = phm.inverse_cdf(cdf, bin_edges)
            func_array.append([col, inv_cdf])
            df[col+'_bins'] = bin_edges
            df[col+'_cdf'] = cdf

    return func_array

def run_risk(df_final):

    i_cdf = inv_cdf_array(df_final)
    for i in range(0, len(i_cdf),1):
        print('%s: var: %s i_cdf: %s' %(i, i_cdf[i][0], i_cdf[i][1](.5)))
