from sklearn.cluster import OPTICS, AgglomerativeClustering, Birch, DBSCAN

class Clusterer:

    def __init__(self, distance_matrix) -> None:
        
        self.distance_matrix = distance_matrix
        self.clusters = None
        self.clusters_labels = None

    def compute_clustering(self):
        pass

    def cluster_dataframe(self, df, method='HDBSCAN', distance_matrix=True, min_size=2, eps=None, join_clusterless_samples=True):
        """ Clusters a dataframe using a given method.
        """
        
        if method == 'OPTICS':

            if distance_matrix:
                if eps is not None:
                    clusterer = OPTICS(min_samples=min_size, metric='precomputed', n_jobs=4, max_eps=eps)
                else:
                    clusterer = OPTICS(min_samples=min_size, metric='precomputed', n_jobs=4)
            else:
                clusterer = OPTICS(min_samples=min_size, n_jobs=4)

        elif method == 'AggClustering':

            if distance_matrix:
                clusterer = AgglomerativeClustering(
                        n_clusters=None,
                        affinity='precomputed',
                        linkage='average',
                        distance_threshold=0.95)
            else:
                clusterer = clusterer = AgglomerativeClustering(
                        n_clusters=None,
                        distance_threshold=1)

        elif method == 'BIRCH':

            if distance_matrix:
                clusterer = Birch(
                        n_clusters=None,
                        threshold=0.95)
            else:
                clusterer = Birch(
                        n_clusters=None)

        elif method == 'DBSCAN':

            if distance_matrix:
                clusterer = DBSCAN(
                        eps=5,
                        min_samples=2,
                        metric='precomputed',
                        n_jobs=-1)
            else:
                clusterer = DBSCAN(
                        eps=0.5,
                        min_samples=2,
                        n_jobs=-1)

        clusterer.fit(df)
        
        filenames = df.index.tolist()
        clusters = {}

        cluster_labels = []

        if not join_clusterless_samples:
            backwards_index = -1

        for (filename, cluster) in zip(filenames, clusterer.labels_):

            #filename = filename.replace("/", "\\")

            if not join_clusterless_samples and cluster == -1:
                cluster = backwards_index
                backwards_index -= 1
            
            cluster_labels.append(cluster)
            
            if cluster in clusters:
                clusters[cluster].append(filename)
            else:
                clusters[cluster] = [filename]

        return clusters, cluster_labels