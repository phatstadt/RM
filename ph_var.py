import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def single_asset_var(df, asset):

    #Sort Returns in Ascending Order
    sorted_rets = sorted(df[asset])
    sorted_rets = sorted_rets[1:]
    varg = np.percentile(sorted_rets, 5)

    #Output histogram
    binwidth = (max(sorted_rets)-min(sorted_rets))/100
    plt.hist(sorted_rets, bins=np.arange(min(sorted_rets), max(sorted_rets) + binwidth, binwidth))
    plt.xlabel('Returns')
    plt.ylabel('Frequency')
    plt.title('Histogram of Asset Returns: ' + str(asset), fontsize=18, fontweight='bold')
    plt.axvline(x=varg, color='r', linestyle='--', label='95% Confidence VaR: ' + "{0:.2f}%".format(varg * 100))
    plt.legend(loc='upper right', fontsize='x-small')
    plt.show()

    #VaR stats
    print("99.99% Confident the actual loss will not exceed: " + "{0:.2f}%".format(np.percentile(sorted_rets, .01) * 100))
    print("99% Confident the actual loss will not exceed: " + "{0:.2f}%".format(np.percentile(sorted_rets, 1) * 100))
    print("95% Confident the actual loss will not exceed: " + "{0:.2f}%".format(np.percentile(sorted_rets, 5) * 100))
    print("Losses expected to exceed " + "{0:.2f}%".format(np.percentile(sorted_rets, 5) * 100) + " " + str(.05*len(df)) + " out of " + str(len(df)) + " days")

    return 1


def var_all(final_df):
        for str_col in final_df:
            if str_col[:1] == 'x' and str_col[-1:] == 'r':
                single_asset_var(final_df, str_col)