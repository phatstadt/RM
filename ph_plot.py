from matplotlib import pyplot as plt

# plt.style.use('ggplot')
# plt.ion()


def plot_drawdown(df, df_field, str_axis, list, fname):

    df2 = df.dropna(subset=[df_field])
    '''truncate data set to test chart speed'''
    #df2 = df2.iloc[0:5000]
    plt.close()
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.plot(df2[str_axis], df2[df_field])
    if len(list) > 0:
        for tup in list.itertuples():
            plt.scatter(df2.iloc[tup.start_index, df2.columns.get_loc(str_axis)],
                        df2[df2.index == tup.start_index][df2_field], c='r')
            plt.scatter(df2.iloc[tup.end_index, df2.columns.get_loc(str_axis)],
                        df2[df2.index == tup.end_index][df_field], c='g')

    ax.set(title='Drawdown Analysis', xlabel='Date', ylabel=df_field)
    ax.xaxis.set_major_locator(plt.MaxNLocator(20))
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=45)
    plt.savefig('d:/Dropbox/Python/PHUtilsPy/pic/' + fname)
    plt.show()
    return
