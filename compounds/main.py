__author__ = 'sebastian'

"""
This file controls the drug bot. It can be run with two command line options:
User can choose to run either with aggregation of data or without. And the user can choose if the data file should be
generated from scratch or aggregation of data should just be continued.
"""

import sys
import argparse
from drug_data_aggregator import DrugDataAggregator


def main():
    parser = argparse.ArgumentParser(description='Drug bot usage')
    parser.add_argument('--from-scratch', action='store_false', help='Build drug data file from scratch')
    parser.add_argument('--no-aggregation', action='store_true', help='Do not aggregate data, only run the bot')
    args = parser.parse_args()

    if args.no_aggregation:
        # DrugBot()
        pass
    else:
        DrugDataAggregator(aggregate=args.from_scratch)
        # DrugBot()

if __name__ == '__main__':
    sys.exit(main())
