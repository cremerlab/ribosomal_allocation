#%%
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt 
import seaborn as sns
import scipy.integrate
import growth.model 
import growth.viz
colors, palette = growth.viz.matplotlib_style()
const = growth.model.load_constants()

data = pd.read_csv('../../data/Bren2013_FigS4.csv')

#%%
# Define constants
gamma_max = const['gamma_max']
Kd_TAA = 1E-5 #const['Kd_TAA']
Kd_TAA_star = 1E-5 #const['Kd_TAA_star']
kappa_max = const['kappa_max']
Kd_cnt = 5E-5
Y =  5E19 #const['Y']
tau = const['tau']
phi_O = 0.55
nu_max = 4.2
dt = 0.0001
c_nt = [0.00022, 0.0044, 0.0011]

# Equilibrate to set beginning of integration in steady state
M0 =  0.0008 * const['OD_conv']
phiRb = growth.model.phiRb_optimal_allocation(gamma_max, nu_max, const['Kd_cpc'], phi_O)
M_Rb= phiRb * M0
M_Mb = (1 - phiRb - phi_O) * M0
TAA = 0.0002
TAA_star = 0.0002
init_params = [M0, M_Rb, M_Mb, TAA, TAA_star]
init_args = (gamma_max, nu_max, tau, Kd_TAA, Kd_TAA_star, kappa_max, phi_O)
out = scipy.integrate.odeint(growth.model.self_replicator_ppGpp, 
            init_params, np.arange(0, 100, dt), args=init_args)
out = out[-1]

phiRb = out[1] / out[0]
M_Rb = phiRb * M0
M_Mb = (1 - phi_O - phiRb) * M0
TAA = out[-2]
TAA_star = out[-1]
init_args = (gamma_max, nu_max, tau, Kd_TAA, Kd_TAA_star, kappa_max, phi_O, True, False, True, True, 0, Kd_cnt, Y)
growth_time = np.arange(0, 12, dt)
dfs = []
for i, c in enumerate(c_nt):
    init_params = [M0, M_Rb, M_Mb, c, TAA, TAA_star]
    growth_cycle = scipy.integrate.odeint(growth.model.self_replicator_ppGpp,
                                          init_params, growth_time, args=init_args)
    df = pd.DataFrame(growth_cycle, columns=['M', 'M_Rb', 'M_Mb', 'c_nt', 'TAA', 'TAA_star'])
    df['balance'] = df['TAA_star'].values / df['TAA'].values
    df['phiRb'] = df['balance'].values / (df['balance'].values + tau)
    df['MMb_M'] = df['M_Mb'].values / df['M']
    df['MRb_M'] = df['M_Rb'].values / df['M']
    df['phiMb'] = 1 - df['phiRb'].values - phi_O
    df['gamma'] = gamma_max * (df['TAA_star'].values / (df['TAA_star'].values + Kd_TAA_star))
    df['c_nt_max'] = c
    df['nu'] =  nu_max * (df['TAA'].values / (df['TAA'].values + Kd_TAA)) * (df['c_nt'].values / (df['c_nt'].values + Kd_cnt))
    df['time'] = growth_time
    dfs.append(df)
df = pd.concat(dfs, sort=False)
df['OD'] = df['M'].values / const['OD_conv']
min_time = 1
df = df[df['time'] >= min_time]
df['time'] -= min_time


fig, ax = plt.subplots(2, 1, figsize=(4, 7))
ax[1].set_xlabel('time [hr]')
# ax[0].set_ylabel('$d\phi_{Mb} / dt$')
ax[1].set_ylabel('approximate OD$_{600}$ [a.u.]')
ax[1].set_yscale('log')
ax[0].set_xlabel('time [hr]')
# cmap = sns.color_palette('mako', n_colors=len(c_nt) + 2)
# counter = 0
ax2 = ax[0].twinx()
ax[0].set_ylabel('change in fluorescence signal')
ax2.set_ylabel('change in metabolic expression', color=colors['primary_red'])
ax2.yaxis.grid(False)
cmap = sns.color_palette('Greys_r', n_colors=4)
counter = 0 
for g, d in data.groupby(['medium']):
    if g != '11 mM Glucose':
        ax[0].plot(d['time_hr'], d['promoter_activity'], '-', lw=1.5, color=cmap[counter],
        alpha=0.75, label=g)

    counter += 1
cmap = [colors['dark_red'], colors['red'], colors['primary_red']]
counter = 0
# ax[0].set_yticks([])
# ax2.set_yticks([])
for g, d in df.groupby(['c_nt_max']):
    deriv = np.diff(d['MMb_M'].values)

    # Find the maximum point of the derivative
    ax2.plot(d['time'].values[:-1],  deriv, '--', label=f'{g:0.4f}',
                color = cmap[counter], lw=1.5, zorder=1000)
    # ax[1].plot(d['time'], d['OD'], '-', label=g,
                # color = cmap[counter])

    # ind = np.argmax(deriv)
    # ax[0].plot(d['time'].values[:-1][ind], deriv[ind], 'o', label='__nolegend__', ms=6,
                # color=cmap[counter])
    # ax[1].plot(d['time'].values[ind], d['OD'].values[ind], 'o', label='__nolegend__', ms=6,
                # color=cmap[counter])
    counter += 1
# ax[1].set_yticks([0.01, 0.1, 1])
# ax[1].set_ylim([0.01, 3])
# ax[1].set_xlim([0, 4])
ax[0].legend(title='condition')
# plt.savefig('../../figures/ppGpp_final_generation.pdf', bbox_inches='tight')
    # %%
