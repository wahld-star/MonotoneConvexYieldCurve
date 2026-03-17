"""
The following program interpolates the current yield curve
The program only interpolates based on cubicspline
"""

#Import Packages
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

#Import Treasury Yields from US Treasury Site
from UST_Prod import treasury_yields_import


def yield_curve(start_date = None, tolerance = 1.0e-15):

    #Define maturiy points ot be graphed
    maturities = ["1M", "1.5M", "2M", "3M", "4M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    maturity_numerical = [1/12, 1.5/12, 2/12, 3/12, 4/12, 6/12, 1, 2, 3, 5, 7, 10, 20, 30]


    #Import spine points
    curve_points = treasury_yields_import(date=start_date)
    #Unpack dictionary within dictionary
    yields = next(iter(curve_points.values()))
    rates = [yields[m] for m in maturities]

    #Fit curve using cubicspline
    cs_fit = CubicSpline(maturity_numerical, rates)

    #Create smoothed Yield Curve
    x_smoothed = np.linspace(maturity_numerical[0], maturity_numerical[-1],300)
    y_smoothed = cs_fit(x_smoothed)

    #Plot Yield Curve
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(x_smoothed, y_smoothed, label='Yield Curve')
    ax.scatter(maturity_numerical, rates, zorder=5, label='Observed Rates')
    ax.set_xticks(maturity_numerical)
    ax.set_xticklabels([m if maturity_numerical[i] >= 1 else '' for i, m in enumerate(maturities)], rotation=45)
    ax.set_xlabel("Maturity")
    ax.set_ylabel("Yield (%)")
    ax.set_title(f"US Treasury Yield Curve - {start_date}")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.show()

yield_curve(start_date = '03-01-2026')
