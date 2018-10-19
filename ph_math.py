import pandas as pd
import numpy as np
import scipy.interpolate as interpolate


def gen_cdf(df2, field, bin_num):
    df = df2.copy()
    df = df[field][1:]
    ser = pd.Series(df)
    bin_range = np.arange(min(df), max(df), (max(df)-min(df))/(bin_num+1))
    freq, bin_edges = np.histogram(ser, density=True, bins=bin_range)
    cdf = np.cumsum(freq * np.diff(bin_edges))
    cdf = np.concatenate((cdf, [np.NaN]))
    return cdf, bin_edges


def inverse_cdf(cdf, bin_edges):
    inv_cdf = interpolate.interp1d(cdf[:len(cdf)-1], bin_edges[:len(bin_edges)-1])
    return inv_cdf



