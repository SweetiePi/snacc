from sklearn import manifold
from sklearn.decomposition import PCA
import pandas as pd
import matplotlib.pyplot as plt
plt.switch_backend('agg')
def read_dist(filename):
  df = pd.read_csv(filename)
  return df
  
def reduce_dimension(D, projection='mds'):
  projections = {'mds' : manifold.MDS(2, dissimilarity="precomputed"),
                     'tsne' : manifold.TSNE(2, metric="precomputed")
  }
  
  X = projections[projection].fit_transform(D)
  return X
  
def test_plot(csv_file, plt_file):
  projections = ['mds', 'tsne']
  D = read_dist(csv_file)
  fig, ax = plt.subplots(len(projections),1)
  for i,p in enumerate(projections):
    X = reduce_dimension(D, p)
    ax[i].scatter(*X.T)
    ax[i].set_title(p)
  plt.tight_layout()
  plt.savefig(plt_file, bbox_inches="tight")
  
if __name__ == "__main__":
  test_plot("../test_dataset/distance_matrix_mysteryGenome1-8.csv", "../test_dataset/distance_matrix_mysteryGenome1-8.png")