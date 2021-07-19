import logging
import argparse
import shutil

from viseagull.webserver import run_webserver
from viseagull.analysis.LogicalAnalyzer import LogicalAnalyzer
from viseagull.analysis.SemanticAnalyzer import SemanticAnalyzer

from viseagull.clustering.LogicalClusterer import LogicalClusterer
from viseagull.clustering.SemanticClusterer import SemanticClusterer

from viseagull.data_processing.DataProcessor import DataProcessor

def get_analyzer(couplings_type, url):
    
    if couplings_type is not None:
        if couplings_type[0] == 'logical':
            analyzer = LogicalAnalyzer(url)
        elif couplings_type[0] == 'semantic':
            analyzer = SemanticAnalyzer(url)
        else:
            raise ValueError("Wrong couplings type")
    else:
        analyzer = LogicalAnalyzer(url)

    return analyzer

def get_clusterer(couplings_type, distance_matrix):
    
    if couplings_type is not None:
        if couplings_type[0] == 'logical':
            clusterer = LogicalClusterer(distance_matrix)
        elif couplings_type[0] == 'semantic':
            clusterer = SemanticClusterer(distance_matrix)
        else:
            raise ValueError("Wrong couplings type")
    else:
        clusterer = LogicalClusterer(distance_matrix)

    return clusterer

def main():

    logging.basicConfig(level=logging.CRITICAL)

    logger = logging.getLogger('viseagull')
    logger.setLevel(level=logging.INFO)

    license = """A ludic visualization tool to explore your codebase. Copyright (C) 2021  Charles Géry
This program comes with ABSOLUTELY NO WARRANTY;'.
This is free software, and you are welcome to redistribute it
under certain conditions;\n\n"""
    logger.info(license)

    parser = argparse.ArgumentParser(description='Process repository url')
    parser.add_argument('url', type=str, nargs=1)
    parser.add_argument('--couplings', type=str, nargs=1, help="logical or semantic")
    parser.add_argument('--save', help='save template', action='store_true')
    parser.add_argument('--load', help='load existing template', type=str, nargs=1)
    args = parser.parse_args()

    if args.load is not None:

        logger.info('Loading existing template')
        src = './saved_templates/' + args.load[0]
        dest = './visualization/data.js'
        shutil.copy(src, dest)

    else:

        logger.info('STEP 1/5 - Initializing analyzer')
        analyzer = get_analyzer(args.couplings, args.url[0])
        

        logger.info('STEP 2/5 - Analyzing Couplings')
        analyzer.compute_couplings()

        logger.info('STEP 3/5 - Computing distance matrix')
        distance_matrix = analyzer.get_distance_matrix()

        logger.info('STEP 4/5 - Computing Clustering')
        clusterer = get_clusterer(args.couplings, distance_matrix)
        clusterer.compute_clustering()

        logger.info('STEP 5/5 - Setting up visualization data')
        data_processor = DataProcessor(analyzer, clusterer)
        data_processor.setup_visualization_data(args.save)

    logger.info('Visualization web server running at localhost:8000')
    run_webserver()
    

if __name__ == "__main__":

    main()
