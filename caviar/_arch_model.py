# Author: Lee Yat Shun, Jasper
# Copyright (c) 2023 Lee Yat Shun, Jasper. All rights reserved.

import numpy as np
from scipy.optimize import minimize


class GarchModel:
    def __init__(self, p, q=0):
        if q != 0:
            raise Exception('Currently only support ARCH model. q must be equal to 0.')
        self.p = p
        self.q = q

    def arch(self, params, returns):
        """return a series of sigma2"""
        omega = params[0]
        alphas = params[1:]

        T = len(returns)

        return2s = returns ** 2

        sigma2s = np.zeros(T)
        sigma2s[0:self.p] = np.var(returns)
        for t in range(self.p, T):
            sigma2s[t] = omega + alphas @ return2s[t - self.p:t]

        if np.any(sigma2s <= 0):
            raise ValueError('sigma_2_t <= 0: insignificant p')

        return sigma2s

    def garch(self, params, returns):
        """return a series of sigma2"""
        omega = params[0]
        alphas = params[1:1 + self.p]
        betas = params[1 + self.p:]

        T = len(returns)

        return2s = returns ** 2

        sigma2s = np.zeros(T)
        sigma2s[0:self.p] = np.var(returns)
        for t in range(self.p, T):
            sigma2s[t] = omega + alphas @ return2s[t - self.p:t]

        if np.any(sigma2s <= 0):
            raise ValueError('sigma_2_t <= 0: insignificant p')

        return sigma2s

    def neg_log_likelihood(self, params, returns):
        """return negative log likelihood"""
        T = len(returns)

        sigma2s = self.arch(params, returns)

        llh = -(T - self.p + 1) / 2 * np.log(2 * np.pi)
        for t in range(self.p, T):
            llh -= 1 / 2 * returns[t] ** 2 / sigma2s[t]
            llh -= 1 / 2 * np.log(sigma2s[t])

        return -llh

    def fit(self, returns):
        """return scipy optimize result"""
        params = np.random.uniform(0, 1, self.p + 1)
        bounds = [(0, None)] + [(0, 1) for _ in range(self.p)]
        returns = np.array(returns)
        self.res = minimize(self.neg_log_likelihood, params, args=(returns), bounds=bounds)
        return self.res
