from matplotlib import pyplot as plt
import pandas as pd
# plt.ion()

def plot_drawdown(df, df_field, str_axis, list, fname):

    df2 = df.dropna(subset=[df_field])
    '''truncate data set to test chart speed'''
    plt.close()
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.plot(df2[str_axis], df2[df_field])
    if len(list) > 0:
        for tup in list.itertuples():
            plt.scatter(df2.iloc[tup.start_index, df2.columns.get_loc(str_axis)],
                        df2[df2.index == tup.start_index][df_field], c='r')
            plt.scatter(df2.iloc[tup.end_index, df2.columns.get_loc(str_axis)],
                        df2[df2.index == tup.end_index][df_field], c='g')

    ax.set(title='Drawdown Analysis', xlabel='Date', ylabel=df_field)
    ax.xaxis.set_major_locator(plt.MaxNLocator(20))
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=45, ha='right')
    plt.savefig('d:/Dropbox/Python/PHUtilsPy/pic/' + fname)
    plt.show()
    return

def plot_one_variable(wb):
    '''analyze one variable'''
    var_id = wb.sheets('filters').range('INSPECTED_VAR_NUM').value
    if var_id > 0:
        fname = wb.sheets('main').range('CSV_PATH').value + 'raw_col_df.csv'
        df = pd.read_csv(fname, index_col=0)
        col_str = 'x' + str(int(var_id))
        df.sort_values(['TRADE_DATE'], ascending=True, inplace=True)
        lili = []
        plot_drawdown(df, col_str, 'TRADE_DATE', lili, 'inspect_var')
