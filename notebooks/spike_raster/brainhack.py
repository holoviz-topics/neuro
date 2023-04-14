import os

datetag = '2022-11-28'

import torch
torch.set_printoptions(precision=3, linewidth=140, sci_mode=False)

if torch.backends.mps.is_available():
    device = torch.device('mps')
elif torch.cuda.is_available():
    device = torch.device('cuda')
else:
    device = torch.device('cpu')
device = torch.device('cpu')


import numpy as np
phi = np.sqrt(5)/2 + 1/2
import matplotlib
import matplotlib.pyplot as plt

import matplotlib
subplotpars = matplotlib.figure.SubplotParams(left=0.125, right=.95, bottom=0.25, top=.975, wspace=0.05, hspace=0.05,)

figpath = None
figpath = 'figures'

def printfig(fig, name, ext='png', figpath=figpath, dpi_exp=None, bbox='tight'):
    fname = os.path.join(figpath, name + '.' + ext)
    fig.savefig(fname, dpi = dpi_exp, bbox_inches=bbox, transparent=True)


def ground_truth_spike_synchronous(spiketrains):
    # Function to find the real position of the pattern
    # Works only for synchronus activity, when ALL neurons 
    # are activated at the same time
    # INPUT : spike trains without the added noise
    dict_spiketrains = {}
    # remove the quantity (s) of the spiketrains array
    for neurons in range(len(spiketrains)):
        a = [float(x) for x in spiketrains[neurons]]
        dict_spiketrains[str(neurons)] = a

    list_keys=list(dict_spiketrains.keys())
    common_spikes = set(dict_spiketrains.get(list_keys[0])).intersection(dict_spiketrains.get(list_keys[1]))
    for key in list_keys[1:-1]:
        num_key=int(key)
        common_spikes = set(common_spikes).intersection(dict_spiketrains.get(str(num_key+1)))

    return common_spikes



# https://docs.python.org/3/library/dataclasses.html?highlight=dataclass#module-dataclasses
from dataclasses import dataclass, asdict, field

@dataclass
class Params:
    datetag: str = datetag
    N_pre: int = 144 # number of presynaptic inputs
    N_PG_time: int = 71 # number of timesteps in PG, must be a odd number for convolutions
    N_PGs: int = 35 # number of polychronous groups
    E_PG: float = 10. # excitability range of PGs
    p_PG: float = .005 # ratio of non-zero coefficients in PGs
    tau_decay: float = .4 # time constant for the decay of the PG enveloppe
    tau_rise: float = .05 # time constant for the rise of the PG enveloppe

    ## Raster plots
    N_time: int =  2**10 # number of timesteps for the raster plot
    N_trials: int = 10 # number of trials
    p_B: float = .001 # prior probability of firing for postsynaptic raster plot
    p_A: float = .001 # prior probability of firing for presynaptic raster plot
    seed: int = 42 # seed

    ## figures
    verbose: bool = False # Displays more verbose output.
    fig_width: float = 12 # width of figure
    phi: float = 1.61803 # beauty is gold
    N_PG_show: float = 5 # number of PG to show in plot_PG

class ABCD:

    def __init__(self, opt):
        self.opt: Params = opt
        self.init()

    def init(self):
        self.logit_p_A = torch.logit(torch.tensor(self.opt.p_A))

        temporal_mod = torch.zeros(self.opt.N_PG_time)
        time = torch.linspace(0, 1, self.opt.N_PG_time)
        temporal_mod = torch.exp(- time / self.opt.tau_decay)
        temporal_mod *= 1 - torch.exp(- time / self.opt.tau_rise)
        # temporal_mod = temporal_mod.flip([0])
        #self.temporal_mod = (torch.eye(self.opt.N_PGs).unsqueeze(2)) * (temporal_mod.unsqueeze(0).unsqueeze(0))
        self.temporal_mod = torch.ones((self.opt.N_pre, self.opt.N_PGs, 1)) * (temporal_mod.unsqueeze(0).unsqueeze(0))

        spike = torch.tensor([1, -.8, -.2])
        self.spike = (torch.eye(self.opt.N_PGs).unsqueeze(2)) * (spike.flip([0]).unsqueeze(0).unsqueeze(0))


    def set_PG(self, seed=None, seed_offset=0):
        if seed is None: seed = self.opt.seed + seed_offset
        torch.manual_seed(seed)
        
        # 1/ define PGs as matrices to be used as kernels
        PG = self.opt.E_PG * torch.randn(self.opt.N_pre, self.opt.N_PGs, self.opt.N_PG_time)
        #threshold = torch.abs(PG).quantile(1-self.opt.p_PG)

        # 2/ zero out everything below the threshold
        # TODO : get analytically
        from scipy.stats import norm
        threshold = self.opt.E_PG * norm.ppf(1-self.opt.p_PG)
        PG *= (PG > threshold)

        # 3/ modulate in time
        PG *= self.temporal_mod

        # 4/ convolve with a spike shape to induce some sort of refractory period
        PG = torch.conv1d(PG, self.spike, padding=self.spike.shape[-1]//2)
        return PG

    def get_b(self, seed=None, seed_offset=1):
        if seed is None: seed = self.opt.seed + seed_offset
        torch.manual_seed(seed)
        # draw causes (PGs) as a matrix of sparse PG activations uniformly in postsynaptic space and time
        # to avoid border effects with the temporal convolution,
        # we set it to zero everywhere
        b_proba = torch.zeros(self.opt.N_trials, self.opt.N_PGs, self.opt.N_time)
        # except outside the borders
        b_proba[:, :, (self.opt.N_PG_time//2):-(self.opt.N_PG_time//2)] = self.opt.p_B
        # b_proba = torch.zeros(self.opt.N_trials, self.opt.N_PGs, self.opt.N_time) * self.opt.p_B
        
        
        return torch.bernoulli(b_proba)

    def plot_raster(self, raster, raster_post=None, PG=None, 
                    i_trial=0, xticks=6, yticks=16, spikelength=.9, 
                    colors=None, figsize=None, subplotpars=subplotpars, 
                    ylabel='address', linewidths=1.0):

        N_neurons = raster.shape[1]
        if colors is None: # blue if nothing assigned
            colors = ['b'] * N_neurons
        else: # give the colors or ...
            if len(colors)==1: # ... paint everything the same color
                colors = colors[0] * N_neurons

        if figsize is None: figsize = (self.opt.fig_width, self.opt.fig_width/self.opt.phi)

        fig, ax = plt.subplots(1, 1, figsize=figsize, subplotpars=subplotpars)
        if raster_post is None:
            for i in range(0, N_neurons):
                ax.eventplot(np.where(raster[i_trial, i, :] == 1.)[0], 
                    colors=colors[i], lineoffsets=1.*i+spikelength/2, 
                    linelengths=spikelength, linewidths=linewidths)
        else:
            for i_PG in range(self.opt.N_PGs):
                b_ = torch.zeros_like(raster_post)
                b_[i_trial, i_PG, :] = raster_post[i_trial, i_PG, :]
                a_ = self.draw_a(b_, PG)
                for i in range(0, self.opt.N_pre):
                    ax.eventplot(np.where(a_[i_trial, i, :] == 1.)[0], colors=colors[i_PG], lineoffsets=1.*i+spikelength/2, 
                    linelengths=spikelength, linewidths=linewidths)
    
        ax.set_ylabel(ylabel)
        ax.set_xlabel('Time (a. u.)')
        ax.set_xlim(0, self.opt.N_time)
        ax.set_ylim(0, N_neurons)

        # ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(yticks))
        ax.set_yticks(np.linspace(0, N_neurons, yticks, endpoint=False)+.5)
        ax.set_yticklabels(np.linspace(1, N_neurons, yticks, endpoint=True).astype(int))
        for side in ['top', 'right']: ax.spines[side].set_visible(False)
        
        ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(4))
        ax.set_xticks(np.linspace(1, self.opt.N_time, xticks, endpoint=True))
        ax.set_xticklabels(np.linspace(1, self.opt.N_time, xticks, endpoint=True).astype(int))

        ax.grid(visible=True, axis='y', linestyle='-', lw=.5)
        ax.grid(visible=True, axis='x', which='both', linestyle='-', lw=.1)

        return fig, ax


    def plot_b(self, b, i_trial=0, xticks=6, yticks=16, spikelength=.9, colors=None, figsize=None, subplotpars=subplotpars):
        b_shifted = torch.roll(b, self.opt.N_PG_time//2, dims=-1)

        fig, ax = self.plot_raster(raster=b_shifted, i_trial=i_trial, xticks=xticks, yticks=yticks, spikelength=spikelength, colors=colors, figsize=figsize, subplotpars=subplotpars, ylabel='@ Motif')
        return fig, ax

    def model_a_logit(self, b, PG):
        """
        defines the evidence of firing for each presynaptic address over time
        input b -> postsynaptic raster plot
            PG -> polychronous groups as spatio temporal kernels
            p_A -> prior proba of firing for the presynaptic addresses
        
        """
        logit_B = torch.conv1d(b*1., PG, padding=self.opt.N_PG_time//2)
        return self.logit_p_A + logit_B

    def model_a(self, b, PG):
        """
        defines the probability of firing for each presynaptic address over time from its evidence
        
        """
        logit_A = self.model_a_logit(b, PG)
        return torch.sigmoid(logit_A)

    def draw_a(self, b, PG, seed=None, seed_offset=2):
        # draws binary events from the probability of firing
        if seed is None: seed = self.opt.seed + seed_offset
        torch.manual_seed(seed)
        # generate the corresponding raster plot
        A_proba = self.model_a(b, PG)
        return torch.bernoulli(A_proba)

    def plot_a(self, a, b=None, PG=None, i_trial=0, xticks=6, yticks=16, spikelength=.9, colors=None, figsize=None, subplotpars=subplotpars):
        fig, ax = self.plot_raster(raster=a, raster_post=b, PG=PG, i_trial=i_trial, xticks=xticks, yticks=yticks, spikelength=spikelength, colors=colors, figsize=figsize, subplotpars=subplotpars, ylabel='@ Neuron')
        return fig, ax

    def inference_with_PGs(self, a, b, PG, max_quant=10000000):
        # infer 
        b_hat = torch.conv_transpose1d(a*1., PG, padding=self.opt.N_PG_time//2)
        # decision
        p_B = b.sum()/(self.opt.N_trials*self.opt.N_PGs*self.opt.N_time) # ça suppose qu'on connait b.sum()...
        if len(b_hat.ravel()) > max_quant:
            ind_quant = torch.randperm(len(b_hat.ravel()))[:max_quant]
            b_threshold = torch.quantile(b_hat.ravel()[ind_quant], 1-env.opt.p_B)
        else:
            b_threshold = torch.quantile(b_hat, 1-p_B)
        b_hat_bin = (b_hat > b_threshold) * 1.
        # b_hat_bin = torch.bernoulli(b_hat)
        return b_hat, b_hat_bin

    def generative_model(self, seed=None, seed_offset=3):
        if seed is None: seed = self.opt.seed + seed_offset
        torch.manual_seed(seed)
        PG, b = self.set_PG(seed=seed), self.get_b(seed=seed+1)
        a = self.draw_a(b, PG, seed=seed+2)
        return a, b, PG

    def test_model(self, PG, PG_true=None, seed=None, seed_offset=4):
        if seed is None: seed = self.opt.seed + seed_offset
        torch.manual_seed(seed)
        if PG_true is None: PG_true = PG
        # define PGs
        # draw causes (PGs)
        b = self.get_b(seed=seed)
        # generate the corresponding raster plot
        a = self.draw_a(b, PG_true, seed=seed+1)
        # infer 
        b_hat, b_hat_bin = self.inference_with_PGs(a, b, PG)
        # count
        accuracy = torch.mean((b_hat_bin == b)*1.)
        TP = torch.mean(b_hat_bin[b==1]*1.)
        TN = 1-torch.mean(b_hat_bin[b==0]*1.)
        return accuracy, TP, TN
        
    def plot_PG(self, PG, cmap='seismic', colors=None, aspect=None, figsize=None, subplotpars=subplotpars, N_PG_show=None):
        if N_PG_show == None: N_PG_show = self.opt.N_PG_show
        if PG.dtype == torch.bool:
            PG_max = 1
            PG_min = 0
            cmap = 'binary'
        else:
            # PG = PG.numpy()
            PG_max = np.abs(PG).max()#.item()
            PG_min = -PG_max

        if figsize is None: figsize = (self.opt.fig_width, self.opt.fig_width/self.opt.phi)

        fig, axs = plt.subplots(1, N_PG_show, figsize=figsize, subplotpars=subplotpars)
        for i_PG in range(N_PG_show):
            ax = axs[i_PG]
            ax.set_axisbelow(True)

            ax.pcolormesh(PG[:, i_PG, :], cmap=cmap, vmin=PG_min, vmax=PG_max)
            #ax.imshow(PG[:, i_PG, :], cmap=cmap, vmin=PG_min, vmax=PG_max, interpolation='none')
            
            ax.set_xlim(0, PG.shape[2])

            ax.set_xlabel('Delay')
            ax.set_title(f'motif #{i_PG+1}', color='k' if colors is None else colors[i_PG])
            if not aspect is None: ax.set_aspect(aspect)

            ax.set_ylim(0, self.opt.N_pre)
            ax.set_yticks(np.arange(0, self.opt.N_pre, 1)+.5)
            if i_PG>0: 
                ax.set_yticklabels([])
            else:
                ax.set_yticklabels(np.arange(0, self.opt.N_pre, 1)+1)

            for side in ['top', 'right']: ax.spines[side].set_visible(False)
            ax.set_xticks([0, self.opt.N_PG_time//2, self.opt.N_PG_time-1])
            ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(self.opt.N_PG_time//4))
            #ax.xaxis.set_minor_locator(AutoMinorLocator(4))
            #ax.set_xticklabels([-(self.opt.N_PG_time//2), 0, self.opt.N_PG_time//2])
            ax.set_xticklabels([0, (self.opt.N_PG_time//2), (self.opt.N_PG_time)])
            # ax.grid(True, axis='y', linestyle='-', lw=1)
            # ax.grid(True, axis='x', which='both', linestyle='-', lw=.1)

        axs[0].set_ylabel('@ Neuron')
        return fig, axs

    def plot_a_histo(self, a,  xticks=1, spikelength=.9, colors=None, figsize=None, subplotpars=subplotpars):
        if figsize is None: figsize = (self.opt.fig_width, self.opt.fig_width/self.opt.phi)

        fig, ax = plt.subplots(1, 1, figsize=figsize, subplotpars=subplotpars)
        ax.step(np.arange(self.opt.N_pre), a.numpy().mean(axis=(0, 2)), label='firing rate')
        ax.hlines(self.opt.p_A, 0, self.opt.N_pre, linestyles='--', color='orange', label='probability of firing for each address')
        ax.set_xlabel('address')
        ax.set_ylim(0)
        ax.legend()
        return fig, ax

    def plot_inference(self, b, b_hat, b_hat_bin, i_trial = 0, t_min = 100, t_max = 150, figsize=None, subplotpars=subplotpars):
        if figsize is None: figsize = (self.opt.fig_width, self.opt.fig_width/self.opt.phi)
        fig, ax = plt.subplots(1, 3, figsize=figsize, subplotpars=subplotpars)
        ax[2].imshow(b_hat_bin[i_trial, :, t_min:t_max])
        ax[0].imshow(b[i_trial, :, t_min:t_max])
        ax[1].imshow(b_hat[i_trial, :, t_min:t_max])
        return fig, ax

    def plot_inference_histo(self, b_hat, nb_bins = 100, figsize=None, subplotpars=subplotpars):
        if figsize is None: figsize = (self.opt.fig_width, self.opt.fig_width/self.opt.phi)

        fig, ax = plt.subplots(1, 1, figsize=figsize, subplotpars=subplotpars)
        ax.hist(b_hat.numpy().ravel(), bins=nb_bins)
        ax.set_ylabel('smarts')
        ax.set_xlabel('value of b_hat')
        ax.set_yscale('log')
        return fig, ax


def vonmises(N_inputs, A, theta, k=2):
    return A*norm(np.exp(k*np.cos(2*np.pi*(np.linspace(0, 1, N_inputs)-theta))))

def cospattern(N_inputs, A, theta, k=4):
    return A*norm(np.cos(k*np.pi*(np.linspace(0, 1, N_inputs)-theta)))

def linear(N_inputs, A, theta):
    return np.linspace(0, A, N_inputs)

def norm(X):
    return (X-X.min())/(X.max()-X.min())

import neo

def make_spiketrains_motif(nb_syn, noise_density, simtime, T, t_true, theta=0, function='cosinus', discard_spikes = None, sd_temp_jitter=None, seed=None):
    
    np.random.seed(seed)
    # draw random gaussian noise spike timings -> shape (nb_syn, nb_ev_noise)
    N_noise = int(noise_density*simtime*nb_syn)
    adress_noise = np.random.randint(0, nb_syn, N_noise)
    time_noise = np.random.rand(N_noise)*simtime

    all_timestamps = time_noise
    all_addresses = adress_noise
    # draw stimulus -> stim
    for t_true_ in t_true:
        adress_pattern = np.arange(nb_syn)
        time_pattern = function(nb_syn, T, theta) + t_true_ #.astype(int)
        if sd_temp_jitter:
            time_pattern += np.random.normal(loc=0, scale=sd_temp_jitter, size=time_pattern.shape)
        if discard_spikes:
            indices = np.random.randint(nb_syn,size=discard_spikes)
            adress_pattern = np.delete(adress_pattern, indices)
            time_pattern = np.delete(time_pattern, indices)
        # make address event representation
        all_timestamps = np.hstack((all_timestamps, time_pattern))
        all_addresses = np.hstack((all_addresses, adress_pattern))
        
    sorted_timestamps = np.argsort(all_timestamps)
    aer = (all_addresses[sorted_timestamps], all_timestamps[sorted_timestamps])
    
    spike_trains = []
    for add in range(nb_syn):
        spike_times = all_timestamps[all_addresses==add]
        spike_trains.append(neo.SpikeTrain(spike_times, units='ms', t_stop=simtime))
    #st = neo.SpikeTrain([3, 4, 5], units='sec', t_stop=10.0)

    return spike_trains, (adress_pattern, time_pattern)

def plot_input(aer_noise, aer_pattern):
    adress_noise, time_noise = aer_noise
    adress_pattern, time_pattern = aer_pattern
    fig, ax = plt.subplots(figsize = (4, 4))
    pattern = ax.scatter(time_pattern, adress_pattern, marker='|', color='blue', alpha = 1, label = 'pattern');
    noise = ax.scatter(time_noise, adress_noise, marker='|', color='grey', alpha = .6, label = 'noise')
    #ax.legend()
    ax.set_xlabel('time (ms)')
    ax.set_ylabel('neuron adress')
    ax.set_title('neural activity')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    return fig, ax

def gaussian_kernel(x, tau):
    return np.exp(-x**2/(2*tau**2))

def absolute_kernel(x, tau):
    return np.exp(-np.abs(x)/tau)

def lif_kernel(x, tau):
    return np.exp(-x/tau)

def make_input_aer(nb_syn, noise_density, simtime, T, t_true, theta=0, function=cospattern, discard_spikes = None, seed=None):
    np.random.seed(seed)
    # draw random gaussian noise spike timings -> shape (nb_syn, nb_ev_noise)
    N_noise = int(noise_density*simtime*nb_syn)
    adress_noise = np.random.randint(0, nb_syn, N_noise)
    time_noise = np.random.rand(N_noise)*simtime

    # draw stimulus -> stim
    adress_pattern = np.arange(nb_syn)
    time_pattern = function(nb_syn, T, theta) + t_true #.astype(int)
    if discard_spikes:
        #indices = np.random.randint(discard_spikes)
        indices = np.arange(0,10)
        adress_pattern = np.delete(adress_pattern, indices)
        time_pattern = np.delete(time_pattern, indices)

    # make address event representation
    all_timestamps = np.hstack((time_noise, time_pattern))
    all_addresses = np.hstack((adress_noise, adress_pattern))
    sorted_timestamps = np.argsort(all_timestamps)
    aer = (all_addresses[sorted_timestamps], all_timestamps[sorted_timestamps])

    return (adress_noise, time_noise), (adress_pattern, time_pattern), aer


class hsd_neuron(object):
    """
    Spiking neuron with heterogeneous delays
    
    """
    def __init__(self, nb_syn, delay_amplitude=100,  
                 tau=20, V_threshold=1, V_resting=0, gain = 1):
        self.delays = np.random.rand(nb_syn) * delay_amplitude
        self.tau = tau # membrane time constant
        self.V_threshold = V_threshold # membrane potential threshold
        self.V_resting = V_resting # resting membrane potential
        self.weights = np.random.rand(nb_syn) #synaptic weights
        self.weights /= np.sum(self.weights)
        self.gain = gain

    def code(self, aer):
        addresses, timestamps = aer
        delayed_timestamps = timestamps + self.delays[addresses]
        sorted_indices = np.argsort(delayed_timestamps)
        sorted_times = delayed_timestamps[sorted_indices]
        sorted_addresses = addresses[sorted_indices]
        dts = np.diff(np.hstack((0, sorted_times))) # = time[ev]-time[ev-1]
        V = np.zeros_like(dts) # computes membrane potential at each event delayed timestamp
        output_spike = []
        V[0] = self.V_resting
        for i, dt in enumerate(dts[1:]):
            if i==0:
                V[i] = self.V_resting
            else:
                if V[i-1]>=self.V_threshold:
                    V[i] = self.V_resting
                    output_spike.append(sorted_times[i])
                else:
                    V[i] = np.exp( - dt / self.tau) * V[i-1] + self.gain * self.weights[sorted_addresses[i]] + self.V_resting
        return V, sorted_times, sorted_addresses, np.float64(output_spike)
    
def plot_learning_figure(sorted_times, V, N, t_out, t_true, delay_amplitude, aer_noise, aer_pattern, delay_gradient=None):
    fig = plt.figure(constrained_layout=True, figsize = (15, 8))
    axs = fig.subplot_mosaic(
    """
    AAAC
    BBBC
    """
    )

    axs['A'].plot(sorted_times, V, color='blue', alpha = .7, label = 'Membrane potential')
    if V.max() > N.V_threshold: 
        axs['A'].vlines(sorted_times[V>N.V_threshold], 1, 2.5, color='red', alpha = .3, label = 'Spikes = detection of the pattern') # spike
        axs['A'].vlines([t_out], 0, 2.5, color='red', alpha = .7, label = 'First spike = earliest detection of the pattern') # spike
    axs['A'].vlines([t_true], 0, 1, linestyles='dotted', color='purple', label = 'Start of the pattern')
    axs['A'].vlines([t_true+delay_amplitude], 0, 1, linestyles='dashed', color='purple', lw = 2, label = 'End of the pattern')
    axs['A'].axvspan( xmin = t_true, xmax = t_true+delay_amplitude, ymin=0, ymax=.4, color = 'purple', alpha = .05, label = 'Pattern duration')

    axs['A'].hlines(N.V_threshold, 0, sorted_times[-1], color = 'orange',linestyles='--', label = 'threshold', linewidth = .9)

    axs['A'].set_xlim(0, sorted_times[-1])
    axs['A'].set_ylim(0, 2.5)

    axs['A'].legend(loc = 'upper right')
    axs['A'].set_xlabel('time (ms)')
    axs['A'].set_ylabel('membrane potential')
    axs['A'].set_title('Evolution of membrane potential across time, with time of the pattern and its detection')
    axs['A'].spines['top'].set_visible(False)
    axs['A'].spines['right'].set_visible(False)
    axs['A'].spines['left'].set_visible(False)
    axs['A'].spines['bottom'].set_visible(False)
    adress_noise, time_noise = aer_noise
    adress_pattern, time_pattern = aer_pattern
    i_adress = np.arange(len(N.delays))

    axs['B'].scatter(time_pattern, adress_pattern, marker='|', color='red', label = 'Right pattern');
    
    if len(t_out)>0:
        for t_post in t_out:
            axs['B'].scatter(t_post - N.delays[:,np.newaxis], i_adress, marker = '|', color = 'orange')
        axs['B'].scatter(t_post - N.delays[:,np.newaxis], i_adress, marker = '|', color = 'orange', label = 'Learned pattern')

    axs['B'].vlines(t_true, 0, 50, linestyles='dotted', color='purple', label = 'Start of the pattern')
    axs['B'].vlines(t_true+delay_amplitude, 0, 50, color='purple', linestyles = 'dashed', label = 'End of the pattern')
    axs['B'].axvspan(t_true, t_true+delay_amplitude, 0, 1, color = 'purple', alpha = .05, label = 'Pattern duration')

    axs['B'].scatter(time_noise, adress_noise, marker='|', color='blue', alpha = .4, label = 'Noise')

    axs['B'].set_xlim(0, sorted_times[-1])
    axs['B'].legend(loc = 'upper right')
    axs['B'].set_xlabel('time (ms)')
    axs['B'].set_ylabel('neuron adress')
    axs['B'].set_title('Comparison of the right pattern to learn and the learned pattern ')
    axs['B'].spines['top'].set_visible(False)
    axs['B'].spines['right'].set_visible(False)
    axs['B'].spines['left'].set_visible(False)
    axs['B'].spines['bottom'].set_visible(False)

    axs['C'].eventplot(N.delays[:,np.newaxis], color = 'orange')
    axs['C'].set_xlabel('time (ms)')
    axs['C'].set_ylabel('neuron adress')
    axs['C'].set_title('Representation of the learned delay')
    if delay_gradient is not None:
        axs['C'].plot(N.delays+delay_gradient, np.arange(len(N.delays)), '.')
    axs['C'].spines['top'].set_visible(False)
    axs['C'].spines['right'].set_visible(False)
    axs['C'].spines['left'].set_visible(False)
    axs['C'].spines['bottom'].set_visible(False)
    plt.show()
    
    
def plot_hsd_response(sorted_times, sorted_addresses, V, N, t_true, t_out, delay_amplitude, aer_noise, aer_pattern, spike_marker_size = 50):
    fig = plt.figure(constrained_layout=True, figsize = (15, 8))
    axs = fig.subplot_mosaic(
    """
    BBB
    AAA
    """
    )
    
    title_size = 20
    axis_size = 16
    legend_size = 12

    axs['A'].plot(sorted_times, V, color='blue', alpha = .7, label = 'Membrane potential')
    if V.max() > N.V_threshold: 
        axs['A'].vlines(sorted_times[V>N.V_threshold], 1, 2.5, color='red', alpha = 1, label = 'Output spike')
        
    axs['A'].hlines(N.V_threshold, 0, sorted_times[-1], color = 'orange',linestyles='--', label = 'Threshold', linewidth = .9)
    axs['A'].set_xlim(0, sorted_times[-1])
    axs['A'].set_ylim(0, 1.5)

    axs['A'].legend(loc = 'upper right', fontsize=legend_size)
    axs['A'].set_xlabel('Time (ms)', fontsize=axis_size)
    axs['A'].set_ylabel('Membrane potential', fontsize=axis_size)
    axs['A'].set_title('Evolution of membrane potential across time, with time of the pattern and its detection', fontsize=title_size)
    axs['A'].spines['top'].set_visible(False)
    axs['A'].spines['right'].set_visible(False)
    axs['A'].spines['left'].set_visible(False)
    axs['A'].spines['bottom'].set_visible(False)
    adress_noise, time_noise = aer_noise
    adress_pattern, time_pattern = aer_pattern
    i_adress = np.arange(len(adress_pattern))
    
    axs['B'].vlines(t_true, 0, len(N.delays)-1, linestyles='dotted', color='purple', label = 'Start of the pattern')
    axs['B'].vlines(t_true+delay_amplitude, 0, len(N.delays)-1, color='purple', linestyles = 'dashed', label = 'End of the pattern')
    axs['B'].axvspan(t_true, t_true+delay_amplitude, 0, 1, color = 'purple', alpha = .05, label = 'Pattern duration')
        
    axs['B'].scatter(time_pattern, adress_pattern, marker='|', s = spike_marker_size, color='red', label = 'Spiking motif');

    for syn in range(len(N.delays)):
        axs['B'].quiver([time_pattern[syn]], [syn], [N.delays[syn]/delay_amplitude], [0], scale = 10, color='orange', alpha=.1, headwidth = 3, headlength = 4, headaxislength = 3)
    axs['B'].quiver([time_pattern[syn]], [syn], [N.delays[syn]/delay_amplitude], [0], scale = 10, color='orange', alpha=.1, headwidth = 3, headlength = 4, headaxislength = 3, label = 'Synaptic delays')
    
    axs['B'].scatter(time_pattern+N.delays, adress_pattern, marker = '|', s = spike_marker_size, color = 'orange', label = 'Multiplexed motif')

    axs['B'].scatter(time_noise, adress_noise, marker='|', color='blue', s = spike_marker_size, alpha = .4, label = 'Noise')

    axs['B'].set_xlim(0, sorted_times[-1])
    axs['B'].legend(loc = 'upper right', fontsize=legend_size)
    axs['B'].set_xlabel('Time (ms)', fontsize=axis_size)
    axs['B'].set_ylabel('Synapse adress', fontsize=axis_size)
    axs['B'].set_title('Two different spiking motifs embedded in a raster plot', fontsize=title_size)
    axs['B'].spines['top'].set_visible(False)
    axs['B'].spines['right'].set_visible(False)
    axs['B'].spines['left'].set_visible(False)
    axs['B'].spines['bottom'].set_visible(False)
    plt.show()
    return fig, axs