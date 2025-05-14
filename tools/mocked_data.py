import pandas as pd
from pandas.tseries.offsets import BMonthEnd
import datetime
import random
import string



## This function generates Random String of four words
def generate_random_four_word_string():
    word_list = [
        "Short", "Master", "Class", "valuable", "Equity", "Ideal", "Fund", "hedge", "growth"
    ]
    return ' '.join(random.sample(word_list, 4))


## This function is to generate random integer between 7 to 9 digits
def generate_random_integer():
    # Choose a random length between 7 and 9
    length = random.randint(7, 9)
    # Generate a number with the chosen length
    lower_bound = 10**(length - 1)
    upper_bound = 10**length - 1
    return random.randint(lower_bound, upper_bound)



## This also generates integer between 4 to 6 numbers
def generate_quantity():
    # Choose a random length between 4 and 6
    length = random.randint(4, 6)
    # Generate a number with the chosen length
    lower_bound = 10**(length - 1)
    upper_bound = 10**length - 1
    return random.randint(lower_bound, upper_bound)



### Gives the list of last business day from the current report date over a time period
def last_business_days(date, time_period):
    last_business_days = []
    date = pd.to_datetime(date)
    
    for i in range(time_period):
        last_business_day = (date - pd.DateOffset(months=i)).to_period('M').to_timestamp() + BMonthEnd()
        last_business_days.append(last_business_day.date())
    
    return last_business_days



## This generates ALphanumeric number of 8 size
def generate_random_uppercase_alphanumeric():
    length = 8
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))



## THis is for generating the number having fixed prefix
def generate_alphanumeric_code(prefix):
    
    remaining_length = 6  # Total length should be 8, and "BL" takes 2 characters
    alphanumeric_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=remaining_length))
    return prefix + alphanumeric_part




def get_trades_data(port: str, report_date: datetime.date, time_period: int) -> pd.DataFrame:

    trade_data = pd.DataFrame(columns = ['Trade Date','CUSIP','ISIN','Bloomberg','Net Money'
                                         ,'Ticker',	'Tran Type'	,'Sec Desc','Quantity'	,'Trade Type',	'Td Num'])

    #generating the date list for the trades date column
    date_list =  last_business_days(report_date, time_period)
    trade_data['Trade Date'] = date_list

    ## Populating the CUSIP column ##

    trade_data['CUSIP'] = [generate_random_uppercase_alphanumeric() for i in range(trade_data.shape[0])]


    ##populating the Bloomberg column

    trade_data['Bloomberg'] = [generate_alphanumeric_code("BL") for i in range(trade_data.shape[0])]

    ## Populating the ISIN column 
    
    trade_data['ISIN'] = [generate_alphanumeric_code("ISI") for i in range(trade_data.shape[0])]

    ## populating NET Money column ##

    trade_data['Net Money'] = [generate_random_integer() for i in range(trade_data.shape[0])] 

    ## populating ticker column ##

    trade_data['Ticker'] = [port for i in range(trade_data.shape[0])]

    ## poupulating the Tran Type Column

    trade_data['Tran Type'] = [random.choice(["BUY", "SELL"]) for i in range(trade_data.shape[0])]

    ## Trade Number column
    trade_data['Td Num'] = [random.randint(1000, 9999) for i in range(trade_data.shape[0])]

    ## Quantity
    trade_data['Quantity'] = [generate_quantity() for i in range(trade_data.shape[0])]

    ## Trade type - Long Term/ Short Term

    trade_data['Trade Type'] = [random.choice(["LONG TERM", "SHORT TERM"]) for i in range(trade_data.shape[0])]

    ## Security Description
    
    trade_data['Sec Desc'] = [generate_random_four_word_string() for i in range(trade_data.shape[0])]
    
    return trade_data

    


