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
#Import Treasury Yields from US Treasury Site
from UST_Prod import treasury_yields_import
import numpy as np
import matplotlib.pyplot as plt


#Set global Variables
maturity_numerical = [1 / 12, 1.5 / 12, 2 / 12, 3 / 12, 4 / 12, 6 / 12, 1, 2, 3, 5, 7, 10, 20, 30]

#Store Rates once retireved
_Rates = None

#Retrieve spine rates for which to construct
def unpack_rate():
    global _Rates
    if _Rates is None:

        #Import rates from treasury xml feed
        spine_points = treasury_yields_import(date='03-23-2026')
        # Define maturiy points ot be graphed
        maturities = ["1M", "1.5M", "2M", "3M", "4M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
        # Unpack dictionary within dictionary
        yields = next(iter(spine_points.values()))
        _Rates = [yields[m] for m in maturities]
    return _Rates

#Begin by creating discrete forwards rates based on no-arb forward rate formula
def discrete_fwd():

    #Retrieve rates
    no_arb_fwd = {}
    rates = unpack_rate()
    for i, rate in enumerate(rates[:-1]):
        no_arb_fwd[maturity_numerical[i]] = (rates[i+1] * maturity_numerical[i+1] - rates[i] * maturity_numerical[i]) / (maturity_numerical[i+1] - maturity_numerical[i])
    return no_arb_fwd

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

def monotonicity(t):
    """
    param t = tau

    We enforce montonicity constraint by defining g as the deviation between the interpolated continuous forward cuvre and discrete forward cuvre.
    Define g as g(tau) = f(tau) - fd_i

    """
    discrete_fwds = list(discrete_fwd().values())

    #Find which interval t falls into to retrieve fd_i
    for i in range(1, len(maturity_numerical)):
        if t <= maturity_numerical[i]:
            tau_prv = maturity_numerical[i-1]
            tau_curr = maturity_numerical[i]
            fd_i = discrete_fwds[i-1]
            break

    #Find g at  the interval boundries
    g_prev = interpolater(tau_prv) - fd_i #g_{i-1}
    g_curr = interpolater(tau_curr) - fd_i #g_i

    #Normalized Position within interval
    x = (t - tau_prv) / (tau_curr - tau_prv)

    #Input g_tau into equation 35 (equation 47)
    g_x  = g_prev * (1-4*x + 3*x**2) + g_curr * (-2*x + 3*x**2)

    #Deriving with respect to x we get
    delta_gx = g_prev * (-4 + 6*x) + g_curr * (-2 + 6*x)

    #Create our four regions
    #Region 1:
    if (g_prev > 0 and -.5*g_prev >= g_curr >= -2 * g_prev) or (g_prev < 0 and -.5*g_prev <= g_curr <= -2 * g_prev):
        pass
    #region 2:
    elif (g_prev > 0 and g_curr < -2 * g_prev) or (g_prev < 0 and g_curr > -2 * g_prev):
        eta = (g_curr + 2*g_prev) / (g_curr - g_prev)
        if x <= eta:
            g_x = g_prev
        else:
            g_x = g_prev + (g_curr - g_prev) * ((x-eta)/(1-eta))**2
    #Region 3:
    elif (g_prev > 0 and 0 > g_curr > -.5* g_prev) or (g_prev < 0 and 0 < g_curr < -.5* g_prev):
        eta = 3 * (g_curr / (g_curr - g_prev))
        if x >= eta:
            g_x = g_curr
        else:
            g_x = g_curr + (g_prev - g_curr) * ((eta-x)/eta)**2
    #Region 4: *We must also enforce positivity within region 4*
    elif (g_prev >= 0 and g_curr >= 0) or (g_prev <= 0 and g_curr <= 0):

        #bound the knot forwards above zero
        f_prev_bound = max(0, min(interpolater(tau_prv), 2 * fd_i))
        f_curr_bound = max(0, min(interpolater(tau_curr), 2 * min(fd_i, discrete_fwds[i])))

        g_prev_bound = f_prev_bound - fd_i
        g_curr_bound = f_curr_bound - fd_i

        eta = (g_curr_bound / (g_curr_bound + g_prev_bound))
        A = -(g_prev_bound * g_curr_bound) / (g_prev_bound + g_curr_bound)
        if x == eta:
            g_x = A
        elif x < eta:
            g_x = A + (g_prev_bound - A) * ((eta-x)/eta)**2
        elif x > eta:
            g_x = A + (g_curr_bound - A) * ((x-eta)/(1-eta))**2
    #Recover f_t from g_x
    f_t = g_x + fd_i
    return f_t

def amelioration(amelioration, t, LAMDA='0.2'):
    if not amelioration:
        return monotonicity(t)

    discrete_fwds = list(discrete_fwd().values())

    #Retrieve tau
    tau_0 = maturity_numerical[0]
    tau_1 = maturity_numerical[1]
    tau_2 = maturity_numerical[2]
    tau_n = maturity_numerical[-1]
    tau_n1 = maturity_numerical[-2]
    tau_n2 = maturity_numerical[-3]

    fd_1 = discrete_fwds[0]
    fd_2 = discrete_fwds[1]
    fd_n = discrete_fwds[-1]
    fd_n1 = discrete_fwds[-2]

    #a) Add additional false intervals adjacent to t
    #Equation 72 (Previous interval)
    tau_minus = tau_0 - (tau_1 - tau_0)
    fd_0 = fd_1 - ((tau_1 - tau_0)/(tau_2 - tau_0)) * (fd_2 - fd_1)
    #Equation 73 (Next interval)
    tau_plus = tau_n + (tau_n - tau_n1)
    fd_plus = fd_n + ((tau_n - tau_n1)/(tau_n - tau_n2)) * (fd_n - fd_n1)

    #Add new intervals into maturity and forward lists
    ext_tau = [tau_minus] + maturity_numerical + [tau_plus]
    ext_fd = [fd_0] + discrete_fwds + [fd_plus]

    #b) select f_i through linear interpolation, recreate our mid-point anchors
    knot_fwds = []
    for i in range (1, len(ext_tau)-1):
        tau_prev = ext_tau[i-1]
        tau_curr = ext_tau[i]
        tau_next = ext_tau[i+1]
        fd_i = ext_fd[i-1] # left interval
        fd_next = ext_fd[i] # right interval

        wt_left = (tau_curr-tau_prev)/(tau_next-tau_prev)
        wt_right = (tau_next-tau_curr)/(tau_next-tau_prev)

        fi = wt_left * fd_next + wt_right * fd_i
        knot_fwds.append(fi)

    #c) adjust fi to fall within target ranges
    #set lambda parameter (using .2 because thats what the paper suggests) LAMDA determines smoothness, trades locality for smoothing
    LAMBDA = LAMDA
    adj_fwds = knot_fwds.copy()
    for i in range (1, len(maturity_numerical)-1):
        #retrieve interval tau
        tau_prev = ext_tau[i-1]
        tau_curr = ext_tau[i]
        tau_next = ext_tau[i+1]
        tau_next2 = ext_tau[i+2]

        fd_i = ext_fd[i]
        fd_prev = ext_fd[i-1]
        fd_next = ext_fd[i+1]
        fd_next2 = ext_fd[i+2]
        fi = knot_fwds[i]

        #Compute theta
        theta_minus = ((tau_curr - tau_prev)/(tau_curr - tau_next2)) * (fd_i - fd_prev)
        theta_plus = ((tau_next - tau_curr)/(tau_next2-tau_curr)) * (fd_next - fd_i)

        #Determine target range based on discrete fwd
        if fd_prev < fd_i <= fd_next:                               #Increasing
            f_min1 = min(fd_i + 0.5 * theta_minus, fd_next)
            f_max1 = min(fd_i + 2 * theta_minus, fd_next)
        elif fd_prev < fd_i and fd_i > fd_next:                     #local max
            f_min1 = max(fd_i - 0.5 * LAMDA * theta_minus, fd_next)
            f_max1 = fd_i
        elif fd_prev >= fd_i and fd_i <= fd_next:                   #local min
            f_min1 = fd_i
            f_max1 = max(fd_i - 0.5 * LAMDA * theta_minus, fd_next)
        elif fd_prev >= fd_i >= fd_next:                            #Decreasing
            f_min1 = max(fd_i + 2 * theta_minus, fd_next)
            f_max1 = max(fd_i + 0.5 * theta_minus, fd_next)

        #Repeat previous step determining following interval range
        if fd_i < fd_next < fd_next2:                               #Increasing
            f_min2 = max(fd_next - 2 * theta_plus, fd_i)
            f_max2 = max(fd_next - 0.5 * theta_plus, fd_i)
        elif fd_i < fd_next and fd_next > fd_next2:                 #local max
            f_min2 = max(fd_next + 0.5 * LAMDA * theta_plus, fd_i)
            f_max2 = fd_next
        elif fd_i >= fd_next and fd_next <= fd_next2:               #local min
            f_min2 = fd_next
            f_max2 = min(fd_next + 0.5 * LAMDA * theta_plus, fd_i)
        elif fd_i >= fd_next >= fd_next2:                           #Decreasing
            f_min2 = min(fd_next - 0.5 * theta_plus, fd_i)
            f_max2 = min(fd_next - 2 * theta_plus, fd_i)


        #Intersect both ranges
        f_min_combined = max(f_min1, f_min2)
        f_max_combined = min(f_max1, f_max2)

        if f_min_combined <= f_max_combined:
            #Ranges intersect so we implement equation 76
            adj_fwds[i] = max(f_min_combined, min(fi, f_max_combined))
        else:
            #Ranges don't intersect so we implement equation 77 to clamp to our knots to the edges
            if fi < min(f_max1, f_max2):
                adj_fwds[i] = min(f_max1, f_max2)
            elif fi > max(f_min1, f_min2):
                adj_fwds[i] = max(f_min1, f_min2)

def recover_zero_rates(t):
    """
    param t = tau

    """
    discrete_fwds = list(discrete_fwd().values())
    input_rates = unpack_rate()

    #Find which interval t falls into to retrieve fd_i
    for i in range(1, len(maturity_numerical)):
        if t <= maturity_numerical[i]:
            tau_prv = maturity_numerical[i-1]
            tau_curr = maturity_numerical[i]
            fd_i = discrete_fwds[i-1]
            break

    #Find g at  the interval boundries
    g_prev = monotonicity(tau_prv) - fd_i #g_{i-1}
    g_curr = monotonicity(tau_curr) - fd_i #g_i
    delta_tau = (tau_curr - tau_prv)

    #Normalize x position
    x = (t - tau_prv) / (tau_curr - tau_prv)



    #Setup our four regions again:
    #Region i
    if (g_prev > 0 and -.5 * g_prev >= g_curr >= -2 * g_prev) or (g_prev < 0 and -.5 * g_prev <= g_curr <= -2 * g_prev):
        #Define I_tau
        I_tau = delta_tau * (g_prev*(x-2*x**2+x**3)+g_curr*(-x**2+x**3))
    #Region ii
    elif (g_prev > 0 and g_curr < -2 * g_prev) or (g_prev < 0 and g_curr > -2 * g_prev):
        #Define eta
        eta = (g_curr + 2*g_prev) / (g_curr - g_prev)
        if 0 <= x <= eta: #Case 1
            I_tau = delta_tau * (g_prev*x)
        elif eta < x <= 1: # Case 2
            I_tau = delta_tau * (g_prev*x + ((g_curr - g_prev) * (x-eta)**3) / (3*(1-eta)**2))
    #Region iii
    elif (g_prev > 0 and 0 > g_curr > -.5* g_prev) or (g_prev < 0 and 0 < g_curr < -.5* g_prev):
        #define eta
        eta = 3 * (g_curr / (g_curr - g_prev))
        if 0 <= x <= eta:
            I_tau = delta_tau * ((g_curr * x + ((g_prev - g_curr) * (eta**3 - (eta - x)**3) / (3*eta**2))))
        elif eta < x <= 1:
            I_tau = delta_tau * ((g_curr*x + (g_prev - g_curr) * eta / 3))
    #Region iv
    elif (g_prev >= 0 and g_curr >= 0) or (g_prev <= 0 and g_curr <= 0):
        #define eta
        #bound the knot forwards above zero
        f_prev_bound = max(0, min(interpolater(tau_prv), 2 * fd_i))
        f_curr_bound = max(0, min(interpolater(tau_curr), 2 * min(fd_i, discrete_fwds[i])))

        g_prev_bound = f_prev_bound - fd_i
        g_curr_bound = f_curr_bound - fd_i

        eta = (g_curr_bound / (g_curr_bound + g_prev_bound))
        A = -(g_prev_bound * g_curr_bound) / (g_prev_bound + g_curr_bound)
        if 0 <= x <= eta: #Case 1
            I_tau = delta_tau * (A*x + ((g_prev_bound- A) * ((eta**3 - (eta -x)**3) / (3*eta**2))))
        elif eta < x <= 1: # Case 2
            I_tau = delta_tau * (A*x + ((g_prev_bound - A)*eta)/3 + (g_curr_bound - A)*((x-eta)**3/(3*(1-eta)**2)))

    else:
        print("error region not found")
        I_tau = 0.0

    # Anchor accumulation to first known zero rate
    # r(tau_0) * tau_0 is the starting point
    r_prev_tau_prev = input_rates[0] * maturity_numerical[0]  # Fix: anchor to first rate
    #Accumulate r_i-1 * tau_i-1 by summing all prior intervals
    for j in range(1, i):
        tau_j_prv = maturity_numerical[j-1]
        tau_j_curr = maturity_numerical[j]
        fd_j = discrete_fwds[j-1]
        delta_tau_j = tau_j_curr - tau_j_prv

        #G at interval boundries for this prior period
        g_j_prv = monotonicity(tau_j_prv) - fd_j
        g_j_curr = monotonicity(tau_j_curr) - fd_j

        # Determine region and compute I_j at x=1 (full interval)
        if (g_j_prv > 0 and -0.5*g_j_prv >= g_j_curr >= -2*g_j_prv) or \
           (g_j_prv < 0 and -0.5*g_j_prv <= g_j_curr <= -2*g_j_prv):
            I_j = delta_tau_j * (
                g_j_prv * (1 - 2 + 1) +
                g_j_curr * (-1 + 1)
            )  # = 0 by no-arbitrage

        elif (g_j_prv > 0 and g_j_curr < -2*g_j_prv) or \
             (g_j_prv < 0 and g_j_curr > -2*g_j_prv):
            eta_j = (g_j_curr + 2*g_j_prv) / (g_j_curr - g_j_prv)
            I_j = delta_tau_j * (
                g_j_prv * 1 +
                (g_j_curr - g_j_prv) * (1 - eta_j)**3 / (3 * (1 - eta_j)**2)
            )  # x=1 so always in Case 2

        elif (g_j_prv > 0 and 0 > g_j_curr > -0.5*g_j_prv) or \
             (g_j_prv < 0 and 0 < g_j_curr < -0.5*g_j_prv):
            eta_j = 3 * (g_j_curr / (g_j_curr - g_j_prv))
            I_j = delta_tau_j * (
                g_j_curr * 1 +
                (g_j_prv - g_j_curr) * eta_j / 3
            )  # x=1 so always in Case 2

        elif (g_j_prv >= 0 and g_j_curr >= 0) or \
             (g_j_prv <= 0 and g_j_curr <= 0):
            f_j_prv_bound = max(0, min(interpolater(tau_j_prv), 2 * fd_j))
            f_j_curr_bound = max(0, min(interpolater(tau_j_curr), 2 * min(fd_j, discrete_fwds[j])))
            g_j_prv_bound = f_j_prv_bound - fd_j
            g_j_curr_bound = f_j_curr_bound - fd_j
            eta_j = g_j_curr_bound / (g_j_curr_bound + g_j_prv_bound)
            A_j = -(g_j_prv_bound * g_j_curr_bound) / (g_j_prv_bound + g_j_curr_bound)
            I_j = delta_tau_j * (
                A_j * 1 +
                (g_j_prv_bound - A_j) * eta_j / 3 +
                (g_j_curr_bound - A_j) * (1 - eta_j)**3 / (3 * (1 - eta_j)**2)
            )  # x=1 so always in Case 2


        r_prev_tau_prev += fd_j * delta_tau_j + I_j

    #Equation 81
    r_t = (1/t) * (r_prev_tau_prev + fd_i * (t - tau_prv) + I_tau)

    return r_t

#Plot
t_grid = np.linspace(maturity_numerical[0], maturity_numerical[-1], 1000)
zero_curve = [recover_zero_rates(t) for t in t_grid]

plt.figure(figsize=(12, 6))
plt.plot(t_grid, zero_curve, label='Zero Curve', color='red')
plt.scatter(maturity_numerical, unpack_rate(), color='black', zorder=5, label='Input Rates')
plt.xlabel('Maturity (Years)')
plt.ylabel('Rate (%)')
plt.title('Monotone Convex Forward and Zero Curves')
plt.legend()
plt.grid(True)
plt.show()
