'''
Created on 2017. 4. 22.

@author: ssakssri
'''
import xlrd
import csv

def csv_from_excel():

    wb = xlrd.open_workbook('/Users/ssakssri/Downloads/picklist.xlsx')
    sh = wb.sheet_by_name('csv')
    
    your_csv_file = open('/Users/ssakssri/Downloads/picklist.csv', 'w', encoding='utf-8')
    wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

    for rownum in range(sh.nrows):
        wr.writerow(localize_floats(sh.row_values(rownum)))

    your_csv_file.close()

# replace float value to string
def localize_floats(row):
    return [
        str(el).replace('.0', '') if isinstance(el, float) else el 
        for el in row
    ]


csv_from_excel()
