import re 
import argparse
import datetime as dt 
import dotenv
from dotenv import dotenv_values
import os


def match_input(pattern: str) -> str:
    """
    Small trivial helper function to catch user input by using regex and returning true or false value
    Args:
        - pattern (str) : string inputted by user
    Returns:
        - Undeclared var (str) : first upper cased char in user-inputted string that matches Y | N constraints
    """

    matcher = re.search(r"y|Y|n|N", pattern)

    while matcher == None:
        matcher = input("Please respond with either Y or N!")
        matcher = re.search(r"y|Y|n|N", matcher)  #too many copies here

    return matcher.group()[0].upper() #Using index 0 to retrieve only first val of char array to catch edge case where user inputs both y and n. .upper method is used to only return Y or N



def get_cred(dir: str) -> str:

    """
    Args:
        - dir (str) : path to directory containing .env file
    Returns:
        - login(str) : name of .env containing credentials 
    """

    creds = []  #extending with list for potentially accomodating multiple api keys

    for item in os.listdir(dir):
        if item.endswith(".env"):
            creds.append(dir + "/" + item)  
    print("Logging in with...{}".format(creds[0]))
    login = dotenv_values(creds[0])  #TODO: More flexible solution instead of just pointing to credentials with index
    return login["PW"]


def type_checker(value: str, pattern=re.compile(r"^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$")) -> str:
    """
    Simple function using regex to check if CLI input matches expected formatting, error raised otherwise
    
    Args:
        - value (str) : Input string from the terminal
        - pattern (object) : re object with default val yyyy - mm - dd checking the validity of the inputed string
    Returns:
        - value, error raised and interpreted CLI mini-app stropped otherwise
    """
    if not pattern.match(value):  #Check if input matches the re object response  
        raise argparse.ArgumentTypeError("Please format the date as: yyyy - mm - dd and run the script again")
    return value


def check_order(start: str, end: str) -> bool:

    """
    Simple function checking if values entered for start and end were made in the right order, raises an exception otherwise
    Args:
        - start (str) : string-formated start date 
        - end (str) : string-formated end date   
    """

    # Creation of 2 local vars for exception handling

    start = dt.datetime.strptime(start, "%Y-%M-%d")
    end = dt.datetime.strptime(end, "%Y-%M-%d")
    
    if start > end:  # Simple exception handling method to check if inputted values are correct
        raise ValueError("Start date after end date!")
    

class BadRequest(Exception):
    """
    Custom exception class to catch server error codes

    Args:

        -code : error code returned by API
    """

    def __init__(self, code):
        self.code = code
        self.msg = "Error code {} has been raised by Nasdaq API, check your passed args and try again or read the documentation in the link below: \n https://docs.data.nasdaq.com/docs/in-depth-usage".format(self.code)
        super().__init__(self.msg)


class EmptyReturn(Exception):
    """
    Custom exception class to catch empty lists 

    Args:

        -code : size of returned data
    """

    def __init__(self, size):
        self.code = size
        self.msg = "Nasdaq API has returned a response object of length {}, perhaps your start and end date are the same day and/or on a day off? \n please check your passed args and try again or read the documentation in the link below: \n https://docs.data.nasdaq.com/docs/in-depth-usage".format(self.code)
        super().__init__(self.msg)

def check_dir(path: str) -> str:
    """
    Small trivial helper to make folders for tidy output parsing 

    Args:
        - path (str) : name of output path
    Returns:
        - path (str) : name of output path (checks created)
    """

    exists = os.path.isdir(path)  #Check if dir exists

    if exists == True:
        return path

    else:
        os.mkdir(path)
        return path 
    