import statsmodels.api as sm
import statsmodels.formula.api as smf

def factor_analysis(wb, final_df):

    print('running factor analysis')
    reg_df = final_df[1:]
    endostr = 'e' + str(wb.sheets('static').range('ENDO_INTEGER').value) + 'r'
    regOLS = calcBetas(reg_df, endostr)
    print(regOLS.summary())
    wb.sheets('factor').range('PY_REG_OUT').value = regOLS.params
    wb.sheets('factor').range('PY_RSQ_OUT').value = regOLS.rsquared


def calcBetas(df, endostr):
    print('calc_betas')
    cols = df.columns.tolist()
    i = 0
    formula = endostr + 'minusrf ~ '
    for col in cols:
        if col[:1] == 'x' and col[-1:] == 'r':
            i += 1
            if i == 1:
                formula += ' ' + col
            else:
                formula += ' + ' + col
    df = sm.add_constant(df)
    regOLS = smf.ols(formula=formula, data=df).fit()
    return regOLS

