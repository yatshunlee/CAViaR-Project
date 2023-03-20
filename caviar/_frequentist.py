# Author: Lee Yat Shun, Jasper
# Copyright (c) 2023 Lee Yat Shun, Jasper. All rights reserved.

import numpy as np
from scipy.optimize import minimize


def mle_fit(returns, model, quantile, caviar):
    """
    :param: returns (array): a series of daily returns
    :param: model (str): Type of CAViaR model. Model must be one of {"adaptive", "symmetric", "asymmetric", "igarch"}.
    :param: quantile (float): a value between 0 and 1
    :param: caviar (callable function): a CAViaR function that returns VaR
    :returns: optimized beta
    """
    params, bounds = initiate_params(model)
    
    while True:
        result = minimize(neg_log_likelihood, params,
                          args=(returns, quantile, caviar), bounds=bounds)
        if result.success:
            break
    
    print(result)
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
    # bounds for tau, intercept
    bounds = [(1e-10, None), (None, None)] # for tau, b0
    if model == 'igarch':
        bounds += [(-1, 1), (-1, 1)] # for b1, b2
    elif model == 'symmetric':
        # b1 for lagged var, b2 for abs(lagged return)
        bounds += [(-1, 1), (-1, 1)] # for b1, b2
    elif model == 'asymmetric':
        # notice that the boundaries are required to keep in 0, 1. Any reason?
        # b1 for lagged var, b2 for (lagged return)^+, b3 for (lagged return)^-
        bounds += [(0, 1), (0, 1), (0, 1)] # for b1, b2, b3
    else:  # adaptive
        pass

    # number of parameters
    p = len(bounds)
    params = np.random.uniform(0, 1, p)

    return params, bounds


def neg_log_likelihood(params, returns, quantile, caviar):
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

    sigmas = caviar(returns, beta, quantile)

    llh = (1 - T) * np.log(tau)
    for t in range(1, T):
        llh -= 1 / tau * max((quantile - 1) * (returns[t] - sigmas[t]),
                             quantile * (returns[t] - sigmas[t]))

    return -llh