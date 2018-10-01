from matplotlib import pyplot as plt

plt.style.use('ggplot')
plt.ion()


def plot_drawdown(df, df_field, str_axis, list, fname):
    plt.close()
    plt.figure(figsize=(11, 8.5))
    plt.plot(df[str_axis], df[df_field])
    for tup in list.itertuples():
        plt.scatter(df.iloc[tup.start_index, df.columns.get_loc(str_axis)],
                    df[df.index == tup.start_index][df_field], c='r')
        plt.scatter(df.iloc[tup.end_index, df.columns.get_loc(str_axis)],
                    df[df.index == tup.end_index][df_field], c='g')
    plt.title('Drawdown Analysis')
    plt.ylabel(df_field)
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=45)
    plt.savefig('d:/Dropbox/Python/PHUtilsPy/pic/' + fname)
    plt.show()
    return
