# Author: Lee Yat Shun, Jasper
# Copyright (c) 2023 Lee Yat Shun, Jasper. All rights reserved.

import numpy as np
from scipy.optimize import minimize


def mle_fit(returns, model, quantile, caviar, VaR0, G):
    """
    :param: returns (array): a series of daily returns
    :param: model (str): Type of CAViaR model. Model must be one of {"adaptive", "symmetric", "asymmetric", "igarch"}.
    :param: quantile (float): a value between 0 and 1
    :param: caviar (callable function): a CAViaR function that returns VaR
    :param: VaR0 (float): initial estimate of VaR_0
    :returns: estimated beta
    """
    # compute the daily returns as 100 times the difference of the log of the prices.
    returns = np.array(returns)
    
    params, bounds = initiate_params(model)
    
    count = 0
    while True:
        # scipy optimize default for bounds: method=L-BFGS-B
        result = minimize(neg_log_likelihood, params,
                          args=(returns, quantile, caviar, VaR0), bounds=bounds)
        
        count += 1
        
        if np.isnan(result.fun):
            # generate new starting point again
            params, bounds = initiate_params(model)
            count = 0
            continue
            
        if result.success or count >= 5:
            break
        
        params = result.x
        
    
    params = result.x
    tau = params[0]
    beta = params[1:]
    return beta


def initiate_params(model):
    """
    Generate the initial estimate of tau and beta.
    All three are mean-reverting in the sense that the coefficient on the lagged VaR is not constrained to be 1.
    i.e.
    β ∈ Rp
    
    :param: model (str): Type of CAViaR model. Model must be one of {"adaptive", "symmetric", "asymmetric", "igarch"}.
    :returns: parameters, corresponding bounds for the parameters
    """
    if model == 'igarch':
        bounds = [(1e-10, None), (1e-10, None), (1e-10, 1), (1e-10, 1)] # for tau, b0, b1, b2
    elif model == 'symmetric':
        # b1 for lagged var, b2 for abs(lagged return)
        bounds = [(1e-10, None), (None, None), (-1, 1), (-1, 1)] # for tau, b0, b1, b2
    elif model == 'asymmetric':
        # b1 for lagged var, b2 for (lagged return)^+, b3 for (lagged return)^-
        bounds = [(1e-10, None), (None, None), (-1, 1), (-1, 1), (-1, 1)] # for tau, b0, b1, b2, b3
    elif model == 'adaptive':
        bounds = [(1e-10, None), (None, None)] # for tau, b0
    else:
        raise ValueError('Model must be one of {"adaptive", "symmetric", "asymmetric", "igarch"}')

    # number of parameters
    p = len(bounds)
    params = np.random.uniform(0, 1, p)

    return params, bounds


def neg_log_likelihood(params, returns, quantile, caviar, VaR0):
    """
    :param: params (array): a series of tau and coefficients
    :param: returns (array): a series of daily returns
    :param: quantile (float): a value between 0 and 1
    :param: caviar (callable function): a CAViaR function that returns VaR
    :returns: negative log likelihood
    """
    T = len(returns)

    tau = params[0]
    beta = params[1:]

    VaRs = caviar(returns, beta, quantile, VaR0)
    
    llh = (1 - T) * np.log(tau)
    for t in range(1, T):
        llh -= 1 / tau * max((quantile - 1) * (returns[t] - VaRs[t]),
                             quantile * (returns[t] - VaRs[t]))

    return -llh
