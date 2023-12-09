import pathlib
from qgis.core import QgsProcessing
import argparse

Parser = argparse.ArgumentParser(description='Check geometry validity for Arches')

Parser.add_argument('--input', '-i', dest='input', required=True, help='Input file')

args = Parser.parse_args()
inputfile_name = pathlib.Path(args.input).name
output = pathlib.Path(args.input).parent / (str(inputfile_name.stem) + '_valid' + str(inputfile_name.suffix))




