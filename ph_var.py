import numpy as np
import matplotlib.pyplot as plt

def single_asset_var(df, asset):

    #Sort Returns in Ascending Order
    sorted_rets = sorted(df[asset])
    sorted_rets = sorted_rets[1:]
    varg = np.percentile(sorted_rets, 5)

    #Output histogram
    plt.hist(sorted_rets,normed=True)
    plt.xlabel('Returns')
    plt.ylabel('Frequency')
    plt.title(r'Histogram of Asset Returns', fontsize=18, fontweight='bold')
    plt.axvline(x=varg, color='r', linestyle='--', label='95% Confidence VaR: ' + "{0:.2f}%".format(varg * 100))
    plt.legend(loc='upper right', fontsize = 'x-small')
    plt.show()

    #VaR stats
    print("99.99% Confident the actual loss will not exceed: " + "{0:.2f}%".format(np.percentile(sorted_rets, .01) * 100))
    print("99% Confident the actual loss will not exceed: " + "{0:.2f}%".format(np.percentile(sorted_rets, 1) * 100))
    print("95% Confident the actual loss will not exceed: " + "{0:.2f}%".format(np.percentile(sorted_rets, 5) * 100))
    print("Losses expected to exceed " + "{0:.2f}%".format(np.percentile(sorted_rets, 5) * 100) + " " + str(.05*len(df)) + " out of " + str(len(df)) + " days")
    return 1