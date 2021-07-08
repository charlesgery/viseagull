from .Clusterer import Clusterer

class LogicalClusterer(Clusterer):

    def __init__(self, distance_matrix) -> None:
        super().__init__(distance_matrix)

    def compute_clustering(self):
        
        self.clusters, self.clusters_labels = self.cluster_dataframe(
                    self.distance_matrix,
                    method='AggClustering',
                    distance_matrix=True,
                    min_size=3,
                    max_eps=1,
                    join_clusterless_samples=True)

        