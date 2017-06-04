'''
Created on 2017. 4. 22.

@author: ssakssri
'''
import logging
import time
import traceback
import xlrd
import csv
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


def csv_from_excel():
#    xls = sys.argv[1]
#    target = sys.argv[2]

    xls = 'C:/Users/ssakssri.DSG/Downloads/jobProfile3.xlsx'
    target = 'C:/Users/ssakssri.DSG/Desktop/jobProfile.csv'

    logging.info("Start converting: From '" + xls + "' to '" + target + "'. ")

    try:
        start_time = time.time()
        wb = xlrd.open_workbook(xls)
        sh = wb.sheet_by_index(0)

        csvFile = open(target, 'w', encoding='utf-8', newline='')
        wr = csv.writer(csvFile, quoting=csv.QUOTE_ALL)

        for row in range(sh.nrows):
            rowValues = sh.row_values(row)
            print(rowValues)

            newValues = []
            for s in rowValues:
                if isinstance(s, bool):
                    if (s==0):
                        strValue = "FALSE"
                    else:
                        strValue = "TRUE"
                else:
                    strValue = str(s)

                isInt = bool(re.match("^([0-9]+)\.0$", strValue))

                if isInt:
                    strValue = int(float(strValue))
                else:
                    isFloat = bool(re.match("^([0-9]+)\.([0-9]+)$", strValue))
                    isLong  = bool(re.match("^([0-9]+)\.([0-9]+)e\+([0-9]+)$", strValue))

                    if isFloat:
                        strValue = float(strValue)

                    if isLong:
                        strValue = int(float(strValue))

                newValues.append(strValue)

            wr.writerow(newValues)

        csvFile.close()

        logging.info("Finished in %s seconds", time.time() - start_time)

    except Exception as e:
        print (str(e) + " " +  traceback.format_exc())


csv_from_excel()
