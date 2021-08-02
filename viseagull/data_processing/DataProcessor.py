import logging

from sklearn import manifold
from prince import MCA
from pandas import DataFrame

class DataProcessor:

    def __init__(self, analyzer, clusterer) -> None:

        self.analyzer = analyzer
        self.clusterer = clusterer
        self.cluster_to_route = None
        self.cluster_centroid = None
        self.citiesData = []
        

    def setup_visualization_data(self, save_data=False):
        """Creates a file containing the data necessary for the visualization."""

        df_reduced = self.dimensionality_reduction(self.analyzer.distance_matrix, method='tSNE')

        self.cluster_to_route = self.find_routes(self.clusterer.clusters, self.analyzer.df)
        self.cluster_centroid = self.find_centroids(df_reduced, self.clusterer.clusters_labels)
        
        self.analyzer.df["sum"] = self.analyzer.df.sum(axis=1)

        self.citiesData = []
        for key in self.clusterer.clusters.keys():


            cityData = {}
            cityData['label'] = key
            cityData['centroid'] = {'x':self.cluster_centroid[key][0], 'y':self.cluster_centroid[key][1]}
            cityData['buildings'] = [{'height':self.analyzer.df.loc[name, "sum"], 'fileName':name} for name in self.clusterer.clusters[key] if name in list(self.analyzer.df.index)]

            if len(cityData['buildings']) > 0:
                self.citiesData.append(cityData)

        self.create_js_file(save_data)



    def dimensionality_reduction(self, df, method='tSNE'):
        """ Performs a dimensionality reduction on a given dataframe, using the given method.
        """

        if method == 'tSNE':
            tsne = manifold.TSNE(n_components=2, perplexity=5, metric='precomputed', square_distances=True)
            embedded_data = tsne.fit_transform(df)

        
        elif method == 'MCA':
        
            df.replace({0: "False", 1: "True"}, inplace = True)
            mca = MCA(n_components=2)
            embedded_data = mca.fit_transform(df)
        

        elif method == 'NMDS':

            nmds = manifold.MDS(n_components=2, metric=False, max_iter=3000, eps=1e-12,
                    dissimilarity="precomputed",
                    n_init=1)
            embedded_data = nmds.fit_transform(df)

        df_embedded = DataFrame(embedded_data, index=df.index)

        return df_embedded

    def find_routes(self, clusters, df):
        """ Find the routes between clusters for a Software as Cities visualization.
        """

        cluster_to_commits = {}
        for cluster_number, cluster_files in clusters.items():
            cluster_to_commits[cluster_number] = []
            for cluster_file in cluster_files:
                for column in df.columns:
                    if cluster_file in list(df.index) and df.loc[cluster_file, column] == 1:
                        cluster_to_commits[cluster_number].append(column)

        cluster_to_route = {}
        for cluster_a_number, cluster_a_commits in cluster_to_commits.items():
            for cluster_b_number, cluster_b_commits in cluster_to_commits.items():

                if cluster_a_number != cluster_b_number:
                    number_common_commits = len(set(cluster_a_commits).intersection(set(cluster_b_commits)))
                
                    if (cluster_a_number, cluster_b_number) not in cluster_to_route and number_common_commits > 0:
                        cluster_to_route[(cluster_a_number, cluster_b_number)] = number_common_commits

        return cluster_to_route

    def find_centroids(self, df, clusters_labels):
        """ Find the centroids of the clusters in a Software as Cities visualization.
        """
        
        X = df.iloc[:, 0]
        Y = df.iloc[:, 1]

        cluster_points = {}
        for (x, y, label) in zip(X, Y, clusters_labels):

            if label not in cluster_points:
                cluster_points[label] = []
            cluster_points[label].append((x, y))

        cluster_centroid = {}
        for cluster_label, points in cluster_points.items():
            mean = [sum(ele) / len(points) for ele in zip(*points)]
            cluster_centroid[int(cluster_label)] = mean

        max_x = max([mean[0] for mean in cluster_centroid.values()])
        max_y = max([mean[1] for mean in cluster_centroid.values()])

        cluster_centroid = {cluster_label:(x/max_x, y/max_y) for cluster_label, (x,y) in cluster_centroid.items()}

        return cluster_centroid

    def create_js_file(self, save_data=False):

        template = """const citiesData = ["""
        for city in self.citiesData:
            template += '{ centroid : {x :' + str(city['centroid']['x']) +', y :' + str(str(city['centroid']['y'])) + '},'
            template += 'buildings : ['
            for building in city['buildings']:
                parsed_name =  str(building['fileName']).replace('\\', '/')
                template += '{height: ' + str(building['height']) + ', fileName:' + f"'{parsed_name}'" + '},'
            template += '],'
            template += 'cityLabel : ' + str(city['label']) + '},'
        template += '];\n'

        template += "const routesData = ["
        for route, routeWidth in self.cluster_to_route.items():
            template += '{ route : {start :' + str(route[0]) + ', end :' + str(route[1]) + '}, width : ' + str(routeWidth) + '},'
        template += '];\n'

        template += 'const commitToFiles = {'
        for key, value in self.analyzer.commit_to_files.items():
            parsed_values = [value[i].replace('\\', '/') for i in range(len(value))]
            template += f'"{key}" : {parsed_values},'
        template += '};\n'

        template += 'const filesModificationsDates = {'
        for key, value in self.analyzer.files_modification_dates.items():
            parsed_key = key.replace('\\', '/')
            template += f"'{parsed_key}' : "
            template += '{ creation_date : '
            template += f'"{value["creation_date"]}", last_modification : "{value["last_modification"]}"'
            template += '}, '
        template += "};\n"

        if self.analyzer.is_remote:
            print(self.analyzer.url[-4:])
            if self.analyzer.url[-4:] == '.git':
                url = self.analyzer.url[:-4]
            else:
                url = self.analyzer.url
            template += f"const url = '{url}';\n"
            template += f"const activeBranch = '{self.analyzer.active_branch}';\n"
        else:
            template += "const url = null;\n"
            template += f"const activeBranch = null;\n"

        template += "const commitsHashes = "
        template += str(['None'] + self.analyzer.commits_hashes)
        template += ';\n'


        template += """\n"""
        template += "export { citiesData, routesData, commitToFiles, filesModificationsDates, url, commitsHashes, activeBranch };"

        with open("./visualization/data.js", "w") as f:
            f.write(template)

        if save_data:
            file_name = f'data_{self.analyzer.couplings_type}_{self.analyzer._get_repo_name_from_url(self.analyzer.url)}.js'
            with open("./saved_templates/" + file_name, "w") as f:
                f.write(template)
            
            logger = logging.getLogger('viseagull')
            logger.info(f"Saved template as {file_name} in ./saved_templates folder")


        return template