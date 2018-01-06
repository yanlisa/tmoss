import numpy as np
from util import *
from tmoss import load_top_matches
from argparse import ArgumentParser

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

################################## Constants ##################################
NON_HEC_CSV = "non_hec.csv"
HEC_CSV = "hec.csv"
FIGNAME = "gumbel.png"
PWM, MM, MM_NP = range(3)

################################ Arguments ####################################
parser = ArgumentParser(description="Gumbel fit")
parser.add_argument('--out', '-o',
        type=str,
        help="Destination for outputting matches.",
        default="out")
parser.add_argument('--ulim', '-ulim',
        type=int,
        help="x-axis bound for similarity score.",
        default=1000)
parser.add_argument('--nbins', '-nbins',
        type=int,
        help="number of histogram bins",
        default=30)
parser.add_argument('--xlabel', '-x',
        type=str,
        help="x axis label",
        default="similarity score")
parser.add_argument('--gumbel-fit', '-g',
        type=int,
        help="Type of gumbel fit (1: probability of weighted moments, " + \
            "2: method of moments, 3: method of moments (from numpy docs)).",
        default=PWM)
args = parser.parse_args()

################################# Loading #####################################
def get_scores(results):
  return [result.get_score() for result in results]

def get_all_results(out_dir):
  non_hec_results = []
  hec_results = []
  for course_dir in sorted(os.listdir(out_dir)):
    if not os.path.isdir(os.path.join(out_dir, course_dir)): continue
    non_hec_results += load_top_matches(course_dir, out_dir, fname=NON_HEC_CSV)
    hec_results += load_top_matches(course_dir, out_dir, fname=HEC_CSV)
  return non_hec_results, hec_results

    
############################## Gumbel helpers #################################
#estimating parameters of gumbel distribution using the methods of moments, probability weighted moments and maximum likelihood
#https://revistas.ucr.ac.cr/index.php/matematica/article/download/259/239
from scipy.special import binom
def prob_weighted_moments(x, r, s):
    def prob_weighted_beta(x, r):
        n = x.shape[0]
        numerators = binom(np.arange(n), r)
        denominators = binom(n-1, r) * np.ones(x.shape)
        ordered_x = np.sort(x)
        summands = numerators * ordered_x / denominators
        return np.average(summands)
    def get_alpha(r, s, beta_r, beta_s):
        numerator = (r + 1) * beta_r - (s + 1) * beta_s
        denominator = np.log(r + 1) - np.log(s + 1)
        return numerator / denominator
    def get_epsilon(r, beta_r, alpha, gamma):
        return (r + 1) * beta_r - alpha * (np.log(r + 1) + gamma)

    gamma = 0.577215 # euler's constant
    beta_r = prob_weighted_beta(x, r)
    beta_s = prob_weighted_beta(x, s)
    #print "beta_r", beta_r, "beta_s", beta_s
    beta = get_alpha(r, s, beta_r, beta_s) # alpha in paper
    mu = get_epsilon(r, beta_r, beta, gamma) # epsilon in paper
    return mu, beta, 'PWM(%s,%s)' % (r,s)

def method_of_moments(x):
    x_mean, x_var = np.mean(x), np.var(x)
    # mu := epsilon = mean - gamma * alpha
    # beta := alpha = sqrt(var/ (J - gamma^2))
    J = 1.978
    gamma = 0.577215 # euler's constant
    beta = np.sqrt(x_var/(J - np.power(gamma,2)))
    mu = x_mean - gamma * beta
    return mu, beta, 'MM2'

# https://en.wikipedia.org/wiki/Method_of_moments_(statistics)
# https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.random.gumbel.html
def method_of_moments_np(x):
    x_mean, x_var = np.mean(x), np.var(x)
    # mean = mu + 0.57721 beta
    # var = (pi^2 / 6 )* beta^2
    beta = np.sqrt(6*x_var/np.power(np.pi, 2))
    mu = x_mean - 0.57721 * beta
    return mu, beta,'MM'

def gumbel_pdf(x, mu, beta):
    return (1/beta)*np.exp(-(x - mu)/beta) * np.exp( -np.exp( -(x - mu) /beta) )

def gumbel_cdf(x, mu, beta):
    return 1 - np.exp( -np.exp( -(x - mu) /beta) )

############################## Main functions #################################
def plot_all(args):
  non_hec_results, hec_results = get_all_results(args.out)
  non_hec_scores = np.array(get_scores(non_hec_results))
  if not non_hec_results and not hec_results:
    print "Could not save any figure because results are empty."
    return
  hec_scores = np.array(get_scores(hec_results))

  bin_range = np.linspace(0, args.ulim, num=args.nbins).tolist()

  fig = plt.figure()
  ax = plt.gca()
  graph_histogram(ax, non_hec_scores, bin_range, color='b', label='Non-HEC')
  graph_histogram(ax, hec_scores, bin_range, color='r', label='HEC')

  plot_gumbel(ax, non_hec_scores, bin_range, gumbel_fit=args.gumbel_fit)
  ax.set_xlabel(args.xlabel)
  title_str = "Distribution of similarity scores"
  ax.set_title(title_str)
  ax.legend()

  fig_dest = os.path.join(args.out, FIGNAME)
  plt.savefig(fig_dest)
  print "Gumbel figure saved to {}".format(fig_dest)

def graph_histogram(ax, arr, bin_range,
                    normed=1, bins=30,color='b',label=None):
    vals2, bins2 = np.histogram(arr, bins=bin_range)
    vals2 = vals2/float(arr.shape[0])
    vals, bins, patches = ax.hist(arr, bins=bin_range,
        alpha=0.5,normed=normed,align='mid',color=color,
        edgecolor='white',label=label)
    return vals, bins, patches

def plot_gumbel(ax, vals, bin_range, nitems=1000, normed=True, gumbel_fit=PWM):
    ulim = max(bin_range)
    x = np.linspace(0, ulim, num=nitems)
    if gumbel_fit == PWM:
      mu, beta, calc_str = prob_weighted_moments(vals, 0, 1)
    elif gumbel_fit == MM:
      mu, beta, calc_str = method_of_moments(vals)
    elif gumbel_fit == MM_NP:
      mu, beta, calc_str = method_of_moments_np(vals)
    width = bin_range[1] - bin_range[0]
    y = gumbel_pdf(x, mu, beta)
    if not normed:
        y *= width*vals.shape[0]
    ax.plot(x, y,label='mu=%.2f,b=%.2f (%s)'%(mu, beta, calc_str),alpha=0.5)
    print mu, beta
    ax.legend()
    return x, y

if __name__ == "__main__":
  plot_all(args)

