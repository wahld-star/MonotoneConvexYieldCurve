"""
Montone Convex Methodolgy
-

Create a continuous zero curve condusive to option formula

Interpaltion Function shall achieve each of the following:
1) The discrete forward rate is recoeved by the curve
2) the forward curve is positive
3) The forward curve is continuous
4) If the yield curve is upward sloping then the forward curve is positive if the yield curve is convex then the forward curve is decreasing

"""



"""
Interpolation Method must satisfy the following 
1) The curve must pass exactly pass through the left boundry
2) The curve must pass exactly pass through the right boundry
3) The average value of the function over the interval must equal a prescribed f(d); the area under the curve is fixed 
"""


#Step 1
"""
Construction of discrete forward rates
- Rather than interpolating the interest rate curve itself we instead are going to interpolate a forward curve

Begin by creating a curve that is equal toa defined forward rate derived from our selected spine points
- Ensuring no-arbitrage (except under negative rate cases)
- This calculated forward rate is assgiend as the mid-point of the interval of the selected spine points 

"""

#Import Packages
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import datetime as dt

maturity_numerical = [1 / 12, 1.5 / 12, 2 / 12, 3 / 12, 4 / 12, 6 / 12, 1, 2, 3, 5, 7, 10, 20, 30]

#Import Treasury Yields from US Treasury Site
from UST_Prod import treasury_yields_import

#Store Rates once retireved
_Rates = None

#Retrieve spine rates for which to construct
def unpack_rate():
    global _Rates
    if _Rates is None:

        #Import rates from treasury xml feed
        spine_points = treasury_yields_import(date='03-12-2026')
        # Define maturiy points ot be graphed
        maturities = ["1M", "1.5M", "2M", "3M", "4M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
        # Unpack dictionary within dictionary
        yields = next(iter(spine_points.values()))
        _Rates = [yields[m] for m in maturities]
    return _Rates

unpack_rate()


#Begin by creating discrete forwards rates based on no-arb forward rate formula
def discrete_fwd():

    #Set numerical distance
    maturity_numerical = [1 / 12, 1.5 / 12, 2 / 12, 3 / 12, 4 / 12, 6 / 12, 1, 2, 3, 5, 7, 10, 20, 30]
    #Retrieve rates
    no_arb_fwd = {}
    rates = unpack_rate()
    for i, rate in enumerate(rates[:-1]):
        no_arb_fwd[maturity_numerical[i]] = (rates[i+1] * maturity_numerical[i+1] - rates[i] * maturity_numerical[i]) / (maturity_numerical[i+1] - maturity_numerical[i])
    return no_arb_fwd

discrete_fwd()


#Setup foward continuously differentiable foward (equation 30)
def continous_fwd():

    fwd_values = list(discrete_fwd().values())
    cc_fwds = {}

    for i in range (1, len(maturity_numerical) - 1):
        #Set variables
        tau_prev = maturity_numerical[i-1]
        tau_current = maturity_numerical[i]
        tau_next = maturity_numerical[i+1]

        #set forward bounds
        left = fwd_values[i-1]
        right = fwd_values[i]

        #set interval weightings based on start and end intervals
        wt_start = (tau_current - tau_prev) / (tau_next - tau_prev)
        wt_end = (tau_next - tau_current) / (tau_next - tau_prev)

        cc_fwds[tau_current] = wt_start * right + wt_end * left
    return(cc_fwds)

continous_fwd()


def boundry_conditions():
    #Retrieve discrete fwds to which are attributed to the mid-point of spine points - f^d values
    discrete_fwds = list(discrete_fwd().values())
    #Retrieve CC_fwds as boundry points
    cc_fwds =  continous_fwd()

    #Left boundry f0 = f^d_1 - .5(f1-f^d_1)
    f0 = discrete_fwds[0] - .5 * (list(cc_fwds.values())[0] - discrete_fwds[0])

    #Right boundry fn = f^d_n -.5(f_{n-1} - f^d_1)
    fn = discrete_fwds[-1] - .5 * (list(cc_fwds.values())[-1] - discrete_fwds[-1])

    all_boundry_fwds = {}
    #Check for curve equal to left boundry (equation 31)
    all_boundry_fwds[maturity_numerical[0]] = f0
    #Unpack all known forwards within respective boundry intervals
    for tau, f in cc_fwds.items():
        all_boundry_fwds[tau] = f
    #Check for curve equal to right boundry (equation 32)
    all_boundry_fwds[maturity_numerical[-1]] = fn
    return all_boundry_fwds

boundry_conditions()

def interpolater(t):
    """
    interpolation method that satisfies
    1) curve prices selected spine points correctly *equation 31 and 32*
    2) Continuous rates described by the curve can be integrated to derive forward rate described by forward curve construction

    Satisfy in the form of the quadratic:
    K + Lx(tau) + Mx(tau)^2

    Which solves as:
    f(tau) = fi-1 - (4fi-1 + 2fi - f^d_i)x(tau) + (3fi-1 + 3fi-6f^d_i)x(tau)^2
    Further as:
    (1-4x(tau)+3x(tau)^2)f_i-1 + (-2x(tau)+3x(tau)^2)f_i + (6x(tau)-6x(tau)^2)f^d_i *Equation 35*

    Beyond tau(n) we use flat extrapolation:
    f(tau) = f(tau_n) for all tau > tau_n

    Properties of the basic interpolater:
    1) Accuracy is O(delta_tau)^2 as delta_tau approaches zero
    * Basically the accuracy is the change from the distance from the spine point of the interval squared
    2) fi is between the average values of f(tau) on the adjacent intervals:
        min(fd_i, fd_i+1) <= fi <= max(fd_i, fd_i+1)
    * The average knot fwd point is between its adjacent discrete points
    * Monotonicity constraint
    """

    #Retrieve discrete and cc rates
    discrete_fwds = list(discrete_fwd().values())
    knot_fwds = list(boundry_conditions().values())

    #First find where t(time) falls in for a given interval
    for i in range (1, len(maturity_numerical)):
        if t <= maturity_numerical[i]:

            #Retrieve interval boundries
            tau_prv = maturity_numerical[i-1]
            tau_curr = maturity_numerical[i]

            #retrieve knot fwds for the given interval boundries
            f_prv = knot_fwds[i-1] #f_{i-1}
            f_curr = knot_fwds[i]  #f_i

            #Retrieve discrete fwd for the given interval the average value that is the mid-point
            fd = discrete_fwds[i-1] #f^d_i

            #Calculate x(t), the normilized position within the interval
            x = (t - tau_prv) / (tau_curr - tau_prv)

            #Apply weighting based on equation 35
            f_t = (f_prv * (1-4*x + 3*x**2) + f_curr * (-2*x + 3*x**2)) + fd * (6*x - 6*x**2)


            return f_t

        #If f_t is > fn
    return knot_fwds[-1]

"""
Interpolater still broken, need ot work on 30 year, currently discrete rate is being out put. 
Need to understand the test_marturities better
- Currently is a linear interpolation

Next step is to enforce monotonicity and convexity 
"""
test_maturities = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 29]
for t in test_maturities:
    print(f"f({t}) = {interpolater(t):.4f}")


def monotonicity(t):
    """
    param t = tau

    We enforce montonicity constraint by defining g as the deviation between the interpolated continuous forward cuvre and discrete forward cuvre.
    Define g as g(tau) = f(tau) - fd_i

    """
    #Define g
    f_t = interpolater(t).values
    discrete_fwds = list(discrete_fwd().values())
    for i in range(1, len(f_t)):
        g_tau = f_t[i] - discrete_fwds[i]

    print(f"f({t}) = {g_tau}")
    return g_tau


test_maturities = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 29]
for t in test_maturities:
    print(f"f({t}) = {monotonicity(t):.4f}")














