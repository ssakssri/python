'''
Created on 2017. 4. 22.

@author: ssakssri
'''
import xlrd
import csv

def csv_from_excel():

#    inFile = 'C:/Users/ssakssri.DSG/Desktop/jobrole_w1.xlsx'
    inFile = 'C:/Users/ssakssri.DSG/Downloads/jobFamily.xlsx'

    outFile = 'C:/Users/ssakssri.DSG/Desktop/jobProfile.csv'

    wb = xlrd.open_workbook(inFile)
    sh = wb.sheet_by_name('csv')
    
    your_csv_file = open(outFile, 'w', encoding='utf-8', newline='')
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

print('Start CSV Conversioin!!')
csv_from_excel()
print('Finish CSV Conversioin!!')

