#%%
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
import growth.viz
import growth.model
import scipy.integrate
colors, palette = growth.viz.matplotlib_style()

# Load the dataset
data = pd.read_csv('../../data/upshift_mass_fraction.csv')


# Set the constants
gamma_max = 20 * 3600/ 7459 
nu_init = 0.8 
nu_shift = 1.05 #1.83
total_time = 8
shift_time = 2

# ppGpp params
Kd_TAA = 2E-5
Kd_TAA_star = 2E-5 
tau = 3
phi_Rb = 0.005
phi_Rb_star = 0.00005
phi_Mb = 1 - phi_Rb - phi_Rb_star
OD_CONV = 1.5E17

# Init params
M0 = 0.001 * OD_CONV
M_Rb = phi_Rb * M0
M_Rb_star = phi_Rb_star * M0
M_Mb = phi_Mb * M0
T_AA = 0.0002
T_AA_star = 0.0002
k_Rb = 10
kappa_max = (88 * 5 * 3600) / 1E9 #0.002
dt = 0.0001
time = np.arange(0, 5, dt)
init_params = [M_Rb, M_Rb_star, M_Mb, T_AA, T_AA_star]
preshift_args = (gamma_max, nu_init, tau, Kd_TAA_star, Kd_TAA, kappa_max, 0, 
                k_Rb, False, True, True, True)
preshift_out = scipy.integrate.odeint(growth.model.batch_culture_self_replicator_ppGpp,
                             init_params, time, args=preshift_args)


rbstar_df = pd.DataFrame(preshift_out, columns=['M_Rb', 'M_Rb_star', 'M_Mb', 'T_AA', 'T_AA_star'])
rbstar_df['total_biomass'] = rbstar_df['M_Rb'].values + rbstar_df['M_Rb_star'].values + rbstar_df['M_Mb'].values
rbstar_df['relative_biomass'] = rbstar_df['total_biomass'] / M0
rbstar_df['mrb/m'] = rbstar_df['M_Rb'].values / rbstar_df['total_biomass'].values
rbstar_df['mrb_star/m'] = rbstar_df['M_Rb_star'].values / rbstar_df['total_biomass'].values
rbstar_df['tRNA_balance'] = rbstar_df['T_AA_star'].values / rbstar_df['T_AA']
rbstar_df['prescribed_phiRb'] = rbstar_df['tRNA_balance'] / (rbstar_df['tRNA_balance'] + tau)
rbstar_df['time'] = time


init_params = [M_Rb, M_Mb, T_AA, T_AA_star]
preshift_args = (gamma_max, nu_init, tau, Kd_TAA_star, Kd_TAA, kappa_max, 0, 
                k_Rb, False, True, True, False)
preshift_out = scipy.integrate.odeint(growth.model.batch_culture_self_replicator_ppGpp,
                             init_params, time, args=preshift_args)


preshift_df = pd.DataFrame(preshift_out, columns=['M_Rb', 'M_Mb', 'T_AA', 'T_AA_star'])
preshift_df['total_biomass'] = preshift_df['M_Rb'].values +  preshift_df['M_Mb'].values
preshift_df['relative_biomass'] = preshift_df['total_biomass'] / M0
preshift_df['mrb/m'] = preshift_df['M_Rb'].values / preshift_df['total_biomass'].values
preshift_df['tRNA_balance'] = preshift_df['T_AA_star'].values / preshift_df['T_AA']
preshift_df['prescribed_phiRb'] = preshift_df['tRNA_balance'] / (preshift_df['tRNA_balance'] + tau)
preshift_df['time'] = time



fig, ax = plt.subplots(2, 2, figsize=(6,6))
ax[0,0].plot(preshift_df['time'], preshift_df['relative_biomass'], 'k-')
ax[1,1].plot(preshift_df['time'], preshift_df['mrb/m'], 'k-')
ax[0,1].plot(preshift_df['time'], preshift_df['prescribed_phiRb'], 'k-')
ax[0, 0].set(yscale='log')
ax[0,0].plot(rbstar_df['time'], rbstar_df['relative_biomass'], 'r--')
ax[0,1].plot(rbstar_df['time'], rbstar_df['prescribed_phiRb'], 'r--')
ax[1,0].plot(rbstar_df['time'], rbstar_df['mrb_star/m'], 'r--')
ax[1,1].plot(rbstar_df['time'], rbstar_df['mrb/m'], 'r--')

#%%

postshift_args = (gamma_max, nu_shift, tau, Kd_TAA_star, Kd_TAA, False, True, True, True, kappa_max)
preshift_out = scipy.integrate.odeint(growth.model.batch_culture_self_replicator_ppGpp,
                             init_params, np.arange(0, 200, dt), args=preshift_args)
postshift_out = scipy.integrate.odeint(growth.model.batch_culture_self_replicator_ppGpp,
                             init_params, np.arange(0, 200, dt), args=postshift_args)

preshift_out = preshift_out[-1]
postshift_out = postshift_out[-1]
init_phiRb = (preshift_out[0]) / (preshift_out[0] + preshift_out[1])
shift_phiRb = (postshift_out[0]) / (postshift_out[0] + postshift_out[1])
init_phiMb = 1 - init_phiRb
shift_phiMb = 1 - shift_phiRb
init_T_AA = preshift_out[2]
init_T_AA_star = preshift_out[3]

# Do the shift
init_params = [M0 * init_phiRb, M0 * init_phiMb, init_T_AA, init_T_AA_star]
init_args = (gamma_max, nu_init, tau, Kd_TAA_star, Kd_TAA, False, True, True, True, kappa_max)
dynamic = growth.model.nutrient_shift_ppGpp(nu_init, nu_shift, shift_time, 
                                            init_params, init_args,
                                            total_time)
init_params = [M0 * init_phiRb, M0 * init_phiMb, init_T_AA, init_T_AA_star]
init_args = (gamma_max, nu_init, tau, Kd_TAA_star, Kd_TAA, False, True, True, False, kappa_max, init_phiRb)
shift_args = (gamma_max, nu_shift, tau, Kd_TAA_star, Kd_TAA, False, True, True, False, kappa_max, shift_phiRb)
instant = growth.model.nutrient_shift_ppGpp(nu_init, nu_shift, shift_time, 
                                            init_params, init_args,
                                            total_time, postshift_args=shift_args)


fig, ax = plt.subplots(1, 1)
ax.set_xlabel('time from up-shift [min]')
ax.set_ylabel('ribosome mass fraction $M_{Rb}/M$')
ax.plot((dynamic['time'].values - shift_time)*60, dynamic['realized_phiR'].values,  
        '-', lw=1, color=colors['primary_black'], label='dynamic reallocation')
ax.plot((instant['time'].values - shift_time) * 60, instant['realized_phiR'].values,  
        '-', lw=1, color=colors['primary_blue'], label='instantaneous reallocation')


# Plot the Bremer data
_data = data[data['source']=='Erickson et al., 2017']
ax.plot(_data['time_from_shift_min'], _data['mass_fraction'], 'o', ms=4, label=_data['source'].values[0])
ax.vlines(60 * np.log(shift_phiRb/init_phiRb)/(gamma_max * 0.2), ax.get_ylim()[0], ax.get_ylim()[1], color=colors['primary_red'])
# ax.set_xlim([0, 100])
ax.legend()
# %%
# Compute the instantaneous growth rate
dynamic_gr = np.log(dynamic['total_biomass'].values[1:] / dynamic['total_biomass'].values[:-1]) / np.diff(dynamic['time'].values)[1]
instant_gr = np.log(instant['total_biomass'].values[1:] / instant['total_biomass'].values[:-1]) / np.diff(instant['time'].values)[1]

# %%
lam_data = pd.read_csv('../../data/Erickson2017_Fig1B.csv')
plt.plot((dynamic['time'].values[1:] - shift_time), dynamic_gr, 'k-', lw=1)
plt.plot((instant['time'].values[1:] - shift_time), instant_gr, '-', lw=1, color=colors['primary_blue'])
plt.plot(lam_data['time_from_shift_hr'], lam_data['growth_rate_hr'], 'o', ms=4)

# %%

# %%

# %%
