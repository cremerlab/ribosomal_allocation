#%%
import numpy as np 
import matplotlib.pyplot as plt 
import pandas as pd 
import bokeh.io
import bokeh.plotting 
import bokeh.models 
import bokeh.layouts
import growth.viz 
import growth.integrate
import growth.model
import scipy.integrate
import tqdm
colors, palette = growth.viz.bokeh_style()
const = growth.model.load_constants()

# Load the reference parameter set
gamma_max = const['gamma_max']
nu_max = 4.5
tau = const['tau']
kappa_max = const['kappa_max']
Kd_TAA = const['Kd_TAA']
Kd_TAA_star = const['Kd_TAA_star']
phi_O = const['phi_O']

# Find the equilibrium state
args = {'gamma_max': gamma_max,
        'nu_max': nu_max,
        'kappa_max':kappa_max,
        'tau':tau,
        'Kd_TAA': Kd_TAA,
        'Kd_TAA_star':Kd_TAA_star,
        'phi_O': phi_O}
out = growth.integrate.equilibrate_FPM(args)

# Unpack equilibrium parameters
TAA = out[-2]
TAA_star = out[-1]
ratio = TAA_star / TAA 
gamma = gamma_max * TAA_star / (TAA_star + Kd_TAA_star)
nu = nu_max * TAA / (TAA + Kd_TAA)
phiRb = (1 - phi_O) * ratio / (ratio + tau)
kappa = kappa_max * ratio / (ratio + tau)
phiRb_range = np.arange(0, 1 - phi_O, 0.001)

#%%
dt = 0.00001
df = pd.DataFrame({})
for i, phi in enumerate(tqdm.tqdm(phiRb_range)):
    # Equilibrate the model at this phiR
    args = {'gamma_max': gamma_max,
            'nu_max': nu_max,
            'Kd_TAA': Kd_TAA,
            'Kd_TAA_star': Kd_TAA_star,
            'kappa_max': kappa_max,
            'phi_O': phi_O,
            'tau': tau,
            'dynamic_phiRb': False,
            'phiRb':  phi}
    _out = growth.integrate.equilibrate_FPM(args, t_return=2)
    out = _out[-1]
    lam = np.log(_out[-1][0] / _out[0][0]) / dt

    # Compute the various properties
    gamma = gamma_max * (out[-1] / (out[-1] + Kd_TAA_star))
    nu = nu_max * (out[-2] / (out[-2] + Kd_TAA))
    ratio = out[-1] / out[-2]

    results = {'gamma': gamma,
               'nu': nu, 
               'lam': gamma * phi, 
               'TAA': out[-2],
               'TAA_star':out[-1],
               'ratio': out[-1]/out[-2],
               'tot_tRNA': out[-1] + out[-2],
               'kappa': kappa_max * phi,
               'phi_Rb': phi,
               'metabolic_flux': nu * (1 - phi_O - phi) + kappa_max * phi,
               'translational_flux': gamma * phi * (1 - out[-1] - out[-2])}
    df = df.append(results, ignore_index=True)
#%%
# Precalculate the equilibration trajectories
args = {'gamma_max':gamma_max,
        'nu_max':nu_max,
        'tau': tau,
        'kappa_max': kappa_max,
        'phi_O': phi_O,
        'Kd_TAA': Kd_TAA,
        'Kd_TAA_star': Kd_TAA_star}

dt = 0.001
time_range = np.arange(0, 5, dt)
data_dict = {'init_phiRb': [],
             'phiRb': [],
             'nu': [],
             'gamma': [],
             'TAA': [],
             'TAA_star': [],
             'metab_flux': [],
             'trans_flux': [],
             'time': [time_range[::10]]}
for i, phi in enumerate(phiRb_range):
        TAA = df['TAA'].values[i]
        TAA_star = df['TAA_star'].values[i]
        params = [1, phi, 1 - phi_O - phi, TAA, TAA_star]
        out = scipy.integrate.odeint(growth.model.self_replicator_FPM,
                                     params, time_range, (args,))
        out = out.T 
        TAA_ = out[:][-2]
        TAA_star_ = out[:][-1]
        gamma_ = gamma_max * TAA_star_ / (TAA_star_ + Kd_TAA_star)
        nu_ = nu_max * TAA_ / (TAA_ + Kd_TAA)
        ratio_ =  TAA_star_ / TAA_
        phiRb_ = (1 - phi_O) * (ratio_ / (ratio_ + tau)) 
        kappa_ = kappa_max * (ratio_ / (ratio_ + tau))
        metab_flux_ = nu * (1 - phi_O - phiRb_) + kappa_
        trans_flux_ = gamma * phiRb_ * (1 - TAA_ - TAA_star_)
        data_dict['init_phiRb'].append(phi)
        data_dict['phiRb'].append(phiRb_[::10])
        data_dict['nu'].append(nu_[::10])
        data_dict['gamma'].append(gamma_[::10])
        data_dict['TAA'].append(TAA_[::10])
        data_dict['TAA_star'].append(TAA_star_[::10])
        data_dict['metab_flux'].append(metab_flux_[::10])
        data_dict['trans_flux'].append(trans_flux_[::10])
        

#%%
bokeh.io.output_file('./interactive_equilibration.html')
dt = 0.00001
time_range = np.arange(0, 10, dt)
# ##############################################################################
# SOURCE DEFINITION
# ##############################################################################
perturbed_point = bokeh.models.ColumnDataSource({'phiRb':[phiRb],
                                                 'MRb_M':[phiRb],
                                                 'growth_rate': [gamma * phiRb]})
trace_display = bokeh.models.ColumnDataSource({'phi_Rb':[],
                                        'time': time_range,
                                        'metab_flux':[],
                                        'trans_flux':[]})
trace_source = bokeh.models.ColumnDataSource(data_dict)
fluxes = bokeh.models.ColumnDataSource({'phiRb_range': list(phiRb_range),
                                        'metab_flux':list(nu * (1 - phiRb_range - phi_O) + kappa),
                                        'trans_flux': list(gamma * phiRb_range * (1 - TAA - TAA_star))})
# ##############################################################################
# WIDGET DEFINITION
# ##############################################################################
phiRb_slider = bokeh.models.Slider(start=phiRb_range[0], end=phiRb_range[-1], step=np.diff(phiRb_range)[0],
                                    value=phiRb, title='allocation towards ribosomes')
equilibrate = bokeh.models.Button(label='Equilibrate!', button_type='success')
# ##############################################################################
# CANVAS DEFINITION
# ##############################################################################
tent_ax = bokeh.plotting.figure(width=500, 
                                height=500, 
                                x_axis_label = 'allocation towards ribosomes',
                                y_axis_label = 'rate [per hr]',
                                y_range=[0, 1.75])

phiRb_ax = bokeh.plotting.figure(width=300,
                                 height=150,
                                 x_axis_label = 'time [hr]',
                                 y_axis_label = 'allocation towards ribosomes')
                                 
metab_flux_ax = bokeh.plotting.figure(width=300,
                                height=150,
                                x_axis_label = 'time [hr]',
                                y_axis_label = 'metabolic flux [per hr]')

trans_flux_ax = bokeh.plotting.figure(width=300,
                                height=150,
                                x_axis_label = 'time [hr]',
                                y_axis_label = 'translational flux [per hr]')

# ##############################################################################
# GLYPH DEFINITION
# ##############################################################################
tent_ax.line(x='phi_Rb', y='lam',  color=colors['primary_black'], line_width=2,
             legend_label='growth rate λ', source=df)
tent_ax.line(x='phiRb_range', y='metab_flux', color=colors['primary_purple'],
            line_width=2, source=fluxes, line_dash='dashed', legend_label='metabolic flux')
tent_ax.line(x='phiRb_range', y='trans_flux', color=colors['primary_gold'],
            line_width=2, source=fluxes, line_dash='dashed',
            legend_label='translational flux')
tent_ax.circle(x='phiRb', y='growth_rate', size=10, color=colors['primary_black'],
             source=perturbed_point)

phiRb_ax.line(x='time', y='phi_Rb', color=colors['primary_gold'],
              line_width=3, source=trace_display)
metab_flux_ax.line(x='time', y='metab_flux', color=colors['primary_purple'],
              line_width=3, source=trace_display, line_dash='dashed')
trans_flux_ax.line(x='time', y='trans_flux', color=colors['primary_gold'],
              line_width=3, source=trace_display, line_dash='dashed')

# ##############################################################################
# CALLBACK DEFINITION
# ##############################################################################
init_args = {'phiRb_range': phiRb_range,
             'growth_rate_range': df['lam'].values,
             'kappa': df['kappa'].values,
             'gamma': df['gamma'].values,
             'nu': df['nu'].values,
             'tot_tRNA': df['tot_tRNA'].values,
             'flux_source':fluxes,
             'point_source': perturbed_point,
             'phiRb_slider': phiRb_slider,
             'phi_O': phi_O,
             'trace_source': trace_source,
             'trace_display': trace_display,
            } 

equil_args  = {
        # Fixed params
        'gamma_max': gamma_max,
        'nu_max': nu_max,
        'phi_O': phi_O,
        'Kd_TAA': Kd_TAA,
        'Kd_TAA_star': Kd_TAA_star,
        'tau': tau,
        'kappa_max': kappa_max,
        
        # Precalculated FPM
        'TAA': df['TAA'].values,
        'TAA_star': df['TAA_star'].values, 

        # Sources
        'flux_source': fluxes,
        'point_source': perturbed_point,

        # Inputs
        'phiRb_slider':phiRb_slider,
        'equilibrate':  equilibrate,

        # Sources
        'point_source': perturbed_point,
        'flux_source': fluxes,
        'trace_source': trace_source,
         
        'step': dt,
}


init_cb = growth.viz.load_js('./interactive_equilibration_init.js', init_args)
equil_cb = growth.viz.load_js(['./functions.js', './interactive_equilibration_trace.js'], args=equil_args)
phiRb_slider.js_on_change('value', init_cb)
equilibrate.js_on_click(equil_cb)


# ##############################################################################
# LAYOUT DEFINITION
# ##############################################################################
col = bokeh.layouts.Column(phiRb_ax, metab_flux_ax, trans_flux_ax)
row = bokeh.layouts.Row(tent_ax, col)
widgets = bokeh.layouts.Row(phiRb_slider, equilibrate)
layout = bokeh.layouts.Column(widgets, row)
bokeh.io.save(layout)


# %%

# %%

# %%

# %%

# %%
