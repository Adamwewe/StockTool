import argparse
from tool import StockTool
import pandas as pd 
import re
from helpers import type_checker, check_order, get_cred, match_input
import warnings

# Args used for testing:

# python main.py -start 2015-01-01 -end 2015-02-28 -database WIKI -dataset FB
# python main.py -start 2010-01-01 -end 2020-01-01 -database WIKI -dataset FB
# python main.py -start 2015-01-01 -end 2015-02-28 -database WIKI -dataset TSLA
# python main.py -start 2010-01-01 -end 2020-01-01 -database WIKI -dataset TSLA

def get_args(parser: object) -> object:

        parser.add_argument("-start", type=type_checker, nargs=1,
                     help="start date of stock fo format: yyyy - mm - dd")

        parser.add_argument("-end", type=type_checker, nargs=1,
                        help="end date of stock fo format: yyyy - mm - dd")

        parser.add_argument("-database", type=str, nargs=1, default="EOD",
                        help="The code for the database this time-series belongs to")

        parser.add_argument("-dataset", type=str, nargs=1, default="FB",
                        help="The code for this time-series (stock)")

        return parser 


parser = get_args(argparse.ArgumentParser(description="Small stock pricing CLI app"))

start_date = parser.parse_args().start[0]
end_date = parser.parse_args().end[0]
# Problem: default values cannot be used because of the indexing below. This also could not be fixed for the final version
db_code = parser.parse_args().database[0]
dt_code = parser.parse_args().dataset[0]

print("Looking into the {} stock inside the {} database".format(dt_code, db_code))

check_order(start_date, end_date)  # To raise an exception in case of reversed input

# Getting API credentials below:

path = "creds"
key = get_cred(path)
print(key)

# instantiating the StockTool object 

s = StockTool(db_code=db_code, dt_code=dt_code, 
        start_date=start_date, end_date=end_date, cred=key)


# Turn off all warnings for better user experience

warnings.filterwarnings("ignore")

# out = s.make_request()

s.make_request()

returns = input("Would you like to calculate the return? (Y/N)")
match = match_input(returns)
if match == "Y":
        s.calc_return()

dd = input("Would you like to calculate the drawdown? (Y/N)")
match = match_input(dd)
if match == "Y":
        s.calc_mdm()

ari = input("Would you like to make a seven day forecast? (Y/N)")
match = match_input(ari)
if match == "Y":
        s.arima(days=7)


print("Thank you for using StockTool!")