import requests
from helpers import BadRequest, EmptyReturn, match_input, check_dir
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

import datetime as dt

import pmdarima as pm
from pmdarima.model_selection import train_test_split
from pmdarima.preprocessing import LogEndogTransformer, BoxCoxEndogTransformer
from pmdarima.pipeline import Pipeline
from sklearn.metrics import mean_squared_error as mse
from scipy.stats import normaltest

class StockTool:

    """
    Custom exception class

    Args:

        - db_code (str): database code to parse in payload
        - dt_code (str): stock to lookup 
        - start_date (str): start date (date when stock was purchsaed)
        - end_date (str): end date (date when stock was sold)
        - cred (str): api key

    """
    def __init__(self, db_code: str, dt_code : str, 
        start_date: str, end_date: str, cred: str) -> object:

        self.db_code = db_code
        self.dt_code = dt_code
        self.start_date = start_date
        self.end_date = end_date
        self.cred = cred

        #  global identifier to be used for saving plots and tables 
        self.identifier = "StockToolOut_" + self.dt_code + "_start_" + self.start_date + "_end_"+ self.end_date

    def make_request(self):
        
        url = "https://data.nasdaq.com/api/v3/datasets/" + self.db_code + "/" + self.dt_code + ".json?column_index=4&start_date=" + self.start_date + "&end_date="+ self.end_date +"&collapse=daily&api_key="+self.cred
        resp = requests.get(url)
        code = resp.status_code

        if code != 200:
            raise BadRequest(code) 

        length_resp = len(resp.json()["dataset"]["data"])
        if length_resp < 1:
            raise EmptyReturn(length_resp)

        self.df = pd.DataFrame(resp.json()["dataset"]["data"]).rename(columns={0: "date",
             1:"value"}).sort_values(by="date", 
                ascending=True)

        self.last_day = self.df.iloc[-1, 0]  #get last day and store globally for ARIMA later
        # We transform dates into the right format and convert to index:
        self.df.index = pd.to_datetime(self.df["date"])
        self.df.drop("date", axis=1, inplace=True)
        print("API response data: \n", self.df)

        returns = input("Would you like to save the retrieved data? (Y/N)")
        match = match_input(returns)
        if match == "Y":
            folder = check_dir("data")
            self.df.to_csv(folder + "/" + self.identifier+ "_data.csv")
            print(f"data saved in {folder} folder")

        return self.df


    def calc_return(self) -> int:
        """
        Trivial function to return simple rate of return and uses global scope df

        Returns:
            - Rate of return
        """

        self.net_diff = self.df["value"].iat[-1] - self.df["value"].iat[0]
        self.rr = round(self.net_diff/self.df["value"].iat[0]*100)

        if self.net_diff < 0:
            print("Oh no! You have made a loss of: {}%".format(self.rr))
        elif self.net_diff > 0:
            print("Congrats, you have made a profit of {}%!".format(self.rr))

        return self.rr



    def calc_mdm(self) -> int:
        """
        Calculates the maximum drawdown using rolling window average. Solution taken from:
            https://medium.com/cloudcraftz/measuring-maximum-drawdown-and-its-python-implementation-99a3963e158f

        """
        start = dt.datetime.strptime(self.start_date, "%Y-%M-%d")
        end = dt.datetime.strptime(self.end_date, "%Y-%M-%d")

        win = int(str(end-start)[0:2])  #retrieve only window from unsubscriptable dt object

        # print(window)

        rolling_max = self.df["value"].rolling(win, min_periods=1).max()
        dd = self.df["value"]/rolling_max - 1.0
        max_dd = dd.rolling(win, min_periods=1).min()

        plot = input("Would you like to save the max drawdown plot? (Y/N)")
        match = match_input(plot)
        
        fig, ax = plt.subplots()
        ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))
        max_dd.plot()
        plt.title(f"Maximum daily drawdown computed over a period window of {win} days on {len(self.df['value'])} closing values")
        ax.set_xlabel("Trading Days")
        ax.set_ylabel("Drawdawn in $\%$")

        if match == "Y":
            folder = check_dir("plots")
            plt.savefig(folder + "/" + self.identifier+ "_drawdown.png")
            print(f"plot saved in {folder} folder")
        plt.show()
        print(f"Average Max Drawdawn is then {round(max_dd.mean()*100)} %")
        
        return max_dd


    def arima(self, days=7)-> object:
        
        """

        Arima used for the forecasts

        Args:
            - days (int) : default value of 7 as per assignment criteria
        Returns:
            - object containing best model fit
        """
        # First, the data is split into appropriate train/test splits:

        train_len = round(len(self.df) * 0.8)  #we follow the ts recommendations of a size of 0.8 
        y_train, y_test = train_test_split(self.df, train_size=train_len)
        bench = pm.auto_arima(y_train, trace=False, 
            suppress_warnings=True)


        # we evaluate:
            # using rmse

        pred = pd.DataFrame({"value":bench.predict(n_periods=len(y_test))}, index=y_test.index)
        print("Benchmark MSE is: {}".format(mse(y_test, pred)))

        # Now we attempt transofrmations 

        # Log:
        y_train_log, _ = LogEndogTransformer(lmbda=1e-6).fit_transform(y_train)
        norm_log = normaltest(y_train_log)[1]

        # Box Cox:
        y_train_bc, _ = BoxCoxEndogTransformer(lmbda2=1e-6).fit_transform(y_train)
        norm_bc = normaltest(y_train_bc)[1]

        # Depending on which transformation has the lowest level of significance, we transform the data with it:

        if norm_bc <= norm_log:

            fit_best = Pipeline([
                ("boxcox", BoxCoxEndogTransformer(lmbda2=1e-6)),
                ("arima", pm.AutoARIMA(trace=False,
                                    suppress_warnings=True
                                    ))
            ])

        elif norm_bc > norm_log:
            
            #Commented the below due to library bug keeping from using the pipeline, will therefore be done manually by using y_train_log

            # fit_best = Pipeline([
            #     ('log', LogEndogTransformer(lmbda2=1e-6)),
            #     ('arima', pm.AutoARIMA(trace=False,
            #                         suppress_warnings=True
            #                         ))
            # ])

            fit_best = pm.auto_arima(y_train_log, 
                trace=False, 
                suppress_warnings=True)

        fit_best.fit(y_train)

        pred = pd.DataFrame({"value":fit_best.predict(n_periods=len(y_test))}, index=y_test.index)
        print("best MSE is: {}".format(mse(y_test, pred)))

        print("Predictions for the {} test days are: \n {}".format(len(y_test), pred))

        fore = input("Would you like to save the test forecast? (Y/N)")
        match = match_input(fore)

        if match == "Y":
            folder = check_dir("preds")
            pred.to_csv(folder + "/" + self.identifier+ "_test_preds.csv")
            print(f"data saved in {folder} folder")
        
        plot = input("Would you like to save the test plot? (Y/N)")
        match = match_input(plot)

        y_train["value"].plot(figsize=(15,8), title= f"Forecasted {self.dt_code} Stock Price on test data for {len(y_test)} days", label="Historic closing prices")
        pred["value"].plot(figsize=(15,8), title=f"Forecasted {self.dt_code} Stock Price on test days for {len(y_test)} days", label="Forecasted closing prices")
        plt.legend()

        if match == "Y":
            folder = check_dir("plots")
            plt.savefig(folder + "/" + self.identifier+ "_test_preds.png")
            print(f"plot saved in {folder} folder")

        plt.show()

        # exit()
        pred_idx = pd.date_range(start=self.last_day, periods=days+1, inclusive="neither")  #added +1 as date generation is exclusive


        pred = pd.DataFrame({"value":bench.predict(n_periods=days)}, index=pred_idx)
        print("Predictions for the 7 days are: ", pred)

        fore = input("Would you like to save the 7 day forecast? (Y/N)")
        match = match_input(fore)

        if match == "Y":
            folder = check_dir("preds")
            pred.to_csv(folder + "/" + self.identifier+ "_7day_forecast.csv")
            print(f"data saved in {folder} folder")

        plot = input("Would you like to save the 7 day forecast plot? (Y/N)")
        match = match_input(plot)

        self.df["value"].plot(figsize=(15,8), title= f"Forecasted {self.dt_code} Stock Price for 7 days", label="Historic closing prices")
        pred["value"].plot(figsize=(15,8), title=f"Forecasted {self.dt_code} Stock Price for 7 days", label="Forecasted closing prices")
        plt.legend()

        if match == "Y":
            folder = check_dir("plots")
            plt.savefig(folder + "/" + self.identifier+ "_7day_preds.png")
            print(f"plot saved in {folder} folder")
        
        plt.show()


        print("Printing model summary... \n", fit_best.summary())


        return fit_best.summary()