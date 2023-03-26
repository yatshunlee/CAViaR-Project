# Author: Lee Yat Shun, Jasper
# Copyright (c) 2023 Lee Yat Shun, Jasper. All rights reserved.

import numpy as np
import matplotlib.pyplot as plt

def plot_caviar(returns, VaR, quantile, model, x_axis=None):
    if x_axis is not None:
        x_lbl = 'date'
    else:
        x_axis = range(len(returns))
        x_lbl = 'time'
    
    fig, axes = plt.subplots(2, 1, figsize=(8, 6*2))
    
    axes[0].plot(x_axis, -VaR)
    axes[0].set_title(f'Estimated CAViaR Plot [{model.capitalize()}]')
    axes[0].set_xlabel(x_lbl)
    axes[0].set_ylabel('CAViaR')
    
    axes[1].plot(x_axis, returns, label='return', zorder=1)
    axes[1].plot(x_axis, VaR, label='negative VaR', zorder=2)
    violations_x = x_axis[returns < VaR]
    violations_y = VaR[returns < VaR]
    axes[1].scatter(violations_x, violations_y, s=20, c='k', marker='^', label='violation', zorder=3)
    hit = sum(returns < VaR) / len(returns)
    axes[1].set_title(f'Hit Rate: {hit:.4f}')
    axes[1].set_xlabel(x_lbl)
    axes[1].set_ylabel(f'Return (%)')
    axes[1].legend()
    
    plt.show()
    
def plot_news_impact_curve(beta, model, quantile, VaR, G):
    y = np.linspace(-10, 10, 100)
    
    if model == 'symmetric':
        X = np.c_[np.ones(100), np.ones(100) * VaR, abs(y)]
        impact = - X @ beta
    elif model == 'asymmetric':
        X = np.c_[np.ones(100), np.ones(100) * VaR, np.maximum(y, 0), np.minimum(y, 0)]
        impact = - X @ beta
    elif model == 'adaptive':
        b1 = beta[0]
        impact = -1 * (VaR + b1 * (
            1 / (1 + np.exp(G * (y - VaR))) - quantile
        ))
    elif model == 'igarch':
        X = np.c_[np.ones(100), np.ones(100) * VaR ** 2, y ** 2]
        impact = np.sqrt(X @ beta)
    else:
        raise ValueError('Wrong model')
    
    plt.figure(figsize=(8, 6))
    plt.plot(y, impact)
    plt.xlabel('y_t-1')
    plt.ylabel('VaR_t')
    plt.title(f'{int(quantile*100)}% CAViaR News Impact Curve')
    plt.ylim([0, 10])
    plt.show()