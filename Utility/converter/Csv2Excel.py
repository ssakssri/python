'''
Created on 2017. 5. 22.

@author: ssakssri
'''
import logging
import time
import csv
from openpyxl import Workbook

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def main():
    
    source = 'C:/Users/ssakssri.DSG/Downloads/jobResponse234258.csv'
    xlsx = source.replace(".csv", ".xlsx")    

    logging.info("Start converting: From '" + source + "' to '" + xlsx + "'. ")
    start_time = time.time()

    wb = Workbook()
    worksheet = wb.active
    with open(source, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)

        for row in reader:
            worksheet.append([_convert_to_number(cell) for cell in row])
        
        wb.save(xlsx)

    logging.info("Finished in %s seconds", time.time() - start_time)


def _convert_to_number(cell):
    
    return cell
    
    if cell.isnumeric():
        return int(cell)
    try:
        return float(cell)
    except ValueError:
        return cell

main()