import logging
import time

from argparse import ArgumentParser
from shutil import copy

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

    parser = ArgumentParser(description='Process repository url')
    parser.add_argument('url', type=str, nargs='?')
    parser.add_argument('--couplings', type=str, nargs=1, help="logical or semantic")
    parser.add_argument('--save', help='save template', action='store_true')
    parser.add_argument('--load', help='load existing template', type=str, nargs=1)
    parser.add_argument('--debug', help='displays running times', action='store_true')
    args = parser.parse_args()

    if args.url is None and args.load is None:
        parser.error("Viseagull requires the url to a repository. See --help for more details.")

    if args.load is not None:

        logger.info('Loading existing template')
        src = './saved_templates/' + args.load[0]
        dest = './visualization/data.js'
        copy(src, dest)

    else:

        logger.info('STEP 1/5 - Initializing analyzer')
        analyzer = get_analyzer(args.couplings, args.url)
        

        logger.info('STEP 2/5 - Analyzing Couplings')
        if args.debug:
            start_time = time.time()
        analyzer.compute_couplings()
        if args.debug:
            logger.info(f'STEP 2/5 Executed in {time.time() - start_time}s')

        logger.info('STEP 3/5 - Computing distance matrix')
        if args.debug:
            start_time = time.time()
        distance_matrix = analyzer.get_distance_matrix()
        if args.debug:
            logger.info(f'STEP 3/5 Executed in {time.time() - start_time}s')

        logger.info('STEP 4/5 - Computing Clustering')
        if args.debug:
            start_time = time.time()
        clusterer = get_clusterer(args.couplings, distance_matrix)
        clusterer.compute_clustering()
        if args.debug:
            logger.info(f'STEP 4/5 Executed in {time.time() - start_time}s')

        logger.info('STEP 5/5 - Setting up visualization data')
        if args.debug:
            start_time = time.time()
        data_processor = DataProcessor(analyzer, clusterer)
        data_processor.setup_visualization_data(args.save)
        if args.debug:
            logger.info(f'STEP 5/5 Executed in {time.time() - start_time}s')

    logger.info('Visualization web server running at localhost:8000')
    logger.info('Open localhost:8000 in your browser to view the visualization')
    run_webserver()
    

if __name__ == "__main__":

    main()
