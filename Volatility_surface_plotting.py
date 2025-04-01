import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from yahoo_fin import options as op
from scipy.interpolate import Rbf
import yfinance as yf
from datetime import datetime
from scipy.interpolate import griddata
import os

# Function to get the call option data for a given stock ticker symbol
def get_call_options(ticker='AAPL'):
    # Check if call option data already exists as a csv file, if yes, return it
    if os.path.exists('Volatility_surface/'+ticker+'.csv'):
        return pd.read_csv('Volatility_surface/'+ticker+'.csv')
    # If the call option data does not exist, retrieve it and save it as a csv file
    else:
        # Get the expiration dates for the stock options
        expirationDates = op.get_expiration_dates(ticker)
        # Initialize an empty dataframe to store the call option data
        calldata = pd.DataFrame()
        # Loop over the expiration dates and retrieve call option data for each date
        for idx, i in enumerate(expirationDates):
            calldata1 = op.get_calls(ticker, date = i)
            # Add a column to store the expiration date index
            calldata1["Expiration Date"] = idx + 1
            # Concatenate the new call option data with the existing data
            calldata = pd.concat([calldata, calldata1])
        # Get the latest stock price (Spot Price) and add it to the call option data
        today = datetime.now()
        calldata['Spot'] = yf.download(ticker, end=today)['Adj Close'][-1]
        # Save the call option data as a csv file for future use
        calldata.to_csv('Volatility_surface/'+ticker+'.csv', index=False)
        return calldata

# Function to plot the implied volatility surface for a given stock
def plot_volatility_surface(ticker='AAPL', resolution=10, epsilon=1, smooth=2):
    # 'ticker': symbol of the stock for which to plot the volatility surface
    # 'resolution': the number of points to add to the grid for more resolution (if too high it can be very long to display the plot)
    # 'epsilon': a parameter for the Rbf function, specifying the shape parameter for the radial basis function
    # 'smooth': a parameter for the Rbf function, specifying the smoothing factor for the interpolation

    # Get the call option data for the stock
    call_data = get_call_options(ticker)
    
    # Extract the expiration date, strike price, spot price, and implied volatilities from the dataframe
    expiration_date = call_data['Expiration Date']
    strike_price = call_data['Strike']
    spot_price = call_data['Spot']
    # Calculate the moneyness of each option
    moneyness = strike_price / spot_price
    # Convert the implied volatilities from strings to floats and divide by 100 to get the volatilities in decimal form
    volatilities = call_data['Implied Volatility'].str[:-1].astype(float) / 100
    
    # Replace inf and NaN values in moneyness with the mean value
    mean_moneyness = np.mean(moneyness[~np.isinf(moneyness) & ~np.isnan(moneyness)])
    moneyness[np.isinf(moneyness) | np.isnan(moneyness)] = mean_moneyness

    # Add more resolution to the grid by adding points
    min_moneyness = np.min(moneyness)
    max_moneyness = min(np.max(moneyness), 4)
    min_expiration = np.min(expiration_date)
    max_expiration = np.max(expiration_date)
    new_expiration_date = np.linspace(min_expiration, max_expiration, int((max_expiration-min_expiration)*resolution))
    new_moneyness = np.linspace(min_moneyness, max_moneyness , int((max_moneyness-min_moneyness)*resolution))
    xi, yi = np.meshgrid(new_expiration_date, new_moneyness)
    
    # Use griddata to perform 2D interpolation on the finer grid
    points = np.array([expiration_date, moneyness]).T
    zi = griddata(points, volatilities, (xi, yi), method='nearest') 

    # Interpolate the option price to create a surface
    rbf = Rbf(xi, yi, zi, function='multiquadric', smooth=smooth, epsilon=epsilon)

    # Evaluate the rbf on the grid
    zi_smooth = rbf(xi, yi)

    # Plot the implied volatility surface
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(xi, yi, zi_smooth, cmap='viridis')
    #ax.plot_surface(xi, yi, zi, cmap='nipy_spectral')
    #plasma
    ax.set_xlabel('Expiration Date (in weeks)')
    ax.set_ylabel('Moneyness')
    ax.set_zlabel('Implied volatility')
    ax.set_title("Volatility surface of "+ ticker)
    
    #Display the 3D Plot
    plt.show()

plot_volatility_surface()
#plot_volatility_surface('TSLA', resolution=5, epsilon=4, smooth=4)