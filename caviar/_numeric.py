# Author: Lee Yat Shun, Jasper
# Copyright (c) 2023 Lee Yat Shun, Jasper. All rights reserved.

import numpy as np
from scipy.optimize import minimize


def numeric_fit(returns, model, quantile, caviar, obj, tol):
    """
    following Engle & Manganelli (2004) approach
    :param: returns (np.array): a series of returns
    :param: model (str): a type of CAViaR models
    :param: caviar (callable): a CAViaR function
    :param: obj (callable): RQ criterion
    :param: quantile (float): a value between 0 and 1
    :param: tol (float): a very small positive number. Default is 1e-10
    """
    initial_betas = initialize_betas(returns, model, caviar, obj, quantile)
    result = []
    
    print('Optimizing by simplex method and quasi-newton method...')
    
    for m, initial_beta in enumerate(initial_betas):
        print(f'when m = {m+1}')
        beta, loss = optimize(initial_beta, returns, quantile, obj, caviar, tol)
        result.append(
            {
                'beta': beta,
                'loss': loss
            }
        )
        # delete later
        print('Alpha version: m = 1. Only run once. Break!')
        break

    result = sorted(result, key=lambda x: x['loss'])
    return result[0]['beta']


def initialize_betas(returns, model, caviar, obj, quantile):
    """
    :param: returns (np.array): a series of returns
    :param: model (str): a type of CAViaR models
    :param: caviar (callable): a CAViaR function
    :param: obj (callable): RQ criterion
    :param: quantile (float): a value between 0 and 1
    :returns: m betas that produced the lowest RQ criterion as initial values
              for the optimization routine
    """

    """
    For below parameters n, m, p:
    n (int): We generated n vectors using a uniform random number generator between 0 and 1.
    m (int): We computed the regression quantile (RQ) function for each of these vectors and
             selected the m vectors that produced the lowest RQ criterion as initial values
             for the optimization routine
    p (int): Number of betas in the vector
    """
    if model == 'adaptive':
        n = 10 ** 4
        m = 5
        p = 1
    elif model == 'symmetric':
        n = 10 ** 4
        m = 10
        p = 3
    elif model == 'asymmetric':
        n = 10 ** 5
        m = 15
        p = 4
    else:  # IGARCH
        n = 10 ** 4
        m = 10
        p = 3
    
    n = 1000
    print(f'Generating {m} best initial betas out of {n}...')
    random_betas = np.random.uniform(0, 1, (n, p))

    best_initial_betas = []

    # if have time, can try heap instead of sorted list
    for i in range(n):
        loss = obj(random_betas[i], returns, quantile, caviar)

        best_initial_betas.append(
            {'loss': loss, 'beta': random_betas[i]}
        )

        best_initial_betas = sorted(best_initial_betas, key=lambda x: x['loss'])

        if len(best_initial_betas) == m:
            best_initial_betas.pop()

    return best_initial_betas


def optimize(initial_beta, returns, quantile, obj, caviar, tol):
    current_beta = initial_beta['beta']
    current_loss = initial_beta['loss']
    
    count = 0
    print(f'Update {count}:', current_loss)
    while True:
        # Minimize the function using the Nelder-Mead algorithm
        res = minimize(obj, current_beta, args=(returns, quantile, caviar), method='Nelder-Mead')
        if not res.success:
            raise 
        current_beta = res.x

        loss = res.fun
        
        count += 1   
        print(f'Update {count}:', loss)
        
        if current_loss - loss < tol:
            break
        else:
            current_loss = loss

        # Minimize the function using the BFGS algorithm
        res = minimize(obj, current_beta, args=(returns, quantile, caviar), method='BFGS')
        current_beta = res.x

        loss = res.fun
        
        count += 1   
        print(f'Update {count}:',loss)
        
        if current_loss - loss < tol:
            break
        else:
            current_loss = loss
        
    return current_beta, loss