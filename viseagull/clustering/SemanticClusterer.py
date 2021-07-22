from .Clusterer import Clusterer

class SemanticClusterer(Clusterer):

    def __init__(self, distance_matrix) -> None:
        super().__init__(distance_matrix)

    def compute_clustering(self):

        for i in range(self.distance_matrix.shape[0]): #iterate over rows
            for j in range(self.distance_matrix.shape[1]): #iterate over columns
                self.distance_matrix.iloc[i, j] = 1.0 - self.distance_matrix.iloc[i, j]
        
        self.clusters, self.clusters_labels = self.cluster_dataframe(
                    self.distance_matrix,
                    method='BIRCH',
                    distance_matrix=True,
                    min_size=3,
                    eps=0.95,
                    join_clusterless_samples=True)