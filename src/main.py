from pathlib import Path
from qgis.core import (
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsApplication,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsVectorDataProvider,
    QgsWkbTypes,
    QgsTopologyPreservingSimplifier,
)
from PyQt5.QtCore import QVariant

import argparse
import csv
import sys

maxInt = sys.maxsize

while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)


current_file_path = Path(__file__).parent.absolute()
current_file_parent_path = Path(__file__).parent.parent.absolute()

Parser = argparse.ArgumentParser(description="Check geometry validity for Arches")

Parser.add_argument(
    "--input",
    "-i",
    dest="input",
    help="Input file defaults to ../data/example.csv",
    default=current_file_parent_path / "data/example.csv",
    required=False,
)

Parser.add_argument(
    "--maxNodes",
    "-m",
    dest="maxNodes",
    help="Maximum number of nodes for each polygon",
    default=150,
    required=False,
)

Parser.add_argument(
    "--simplifyingTolerance",
    "-s",
    dest="simplifyingTolerance",
    help="Simplifying tolerance",
    default=0.0001,
    required=False,
)


args = Parser.parse_args()
inputfile_path = args.input
inputfile_name = Path(args.input).stem
inputfile_suffix = Path(args.input).suffix
outputfile_path = Path(args.input).parent / (
    str(inputfile_name) + "_valid" + str(inputfile_suffix)
)

# check if the input file exists
if not Path(inputfile_path).is_file():
    print("Input file does not exist")
    exit()


maxNodes = int(args.maxNodes)
simplifyingTolerance = float(args.simplifyingTolerance)

QgsApplication.setPrefixPath("/usr/bin/qgis", True)
QgsApplication.setPrefixPath("/usr/share/qt5", True)

memory_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "memory_layer", "memory")

with open(inputfile_path, "r") as csv_file:
    csv_data = csv.DictReader(csv_file)

    list_of_csv_fieldnames = csv_data.fieldnames

    fields = QgsFields()
    for fieldname in list_of_csv_fieldnames:
        fields.append(QgsField(fieldname, QVariant.String))

    memory_layer.dataProvider().addAttributes(fields)

    memory_layer.updateFields()

    for row in csv_data:
        feature = QgsFeature(fields)

        for fieldname in list_of_csv_fieldnames:
            if fieldname != "Geometry":
                feature.setAttribute(fieldname, row[fieldname])

        wkt_geometry = row["Geometry"]
        geometry = QgsGeometry.fromWkt(wkt_geometry)
        feature.setGeometry(geometry)

        memory_layer.dataProvider().addFeature(feature)

    memory_layer.updateExtents()


def simplify_geometry(geometry, simplifyingTolerance):
    topology_preserving_simplifier = QgsTopologyPreservingSimplifier(
        simplifyingTolerance
    )
    simplified_geometry = topology_preserving_simplifier.simplify(geometry)
    return simplified_geometry


def write_polygon_geometry_and_resource_id_to_a_new_feature(
    memory_layer, feature, polygon_geometry
):
    new_feature = QgsFeature(fields)

    new_feature.setGeometry(polygon_geometry)
    new_feature.setAttribute("ResourceID", feature.attribute("ResourceID"))

    memory_layer.dataProvider().addFeature(new_feature)


def spilt_one_polygon_into_parts(polygon_geometry, simplify_switch=True):
    if simplify_switch:
        polygon_geometry = simplify_geometry(
            polygon_geometry, simplifyingTolerance=simplifyingTolerance
        )
    subdivided_polygon = polygon_geometry.subdivide(maxNodes=maxNodes)
    return subdivided_polygon


def spilt_geometry_into_parts(geometry):
    if geometry.isMultipart():
        list_of_geometries = geometry.asGeometryCollection()
    else:
        list_of_geometries = [geometry]

    subdivided_parts = []
    for polygon_geometry in list_of_geometries:
        subdivided_part = spilt_one_polygon_into_parts(polygon_geometry)
        subdivided_parts = subdivided_parts + subdivided_part.asGeometryCollection()

    return subdivided_parts


for feature in memory_layer.getFeatures():
    if (
        (not feature.geometry().isEmpty())
        and (not feature.geometry().isNull())
        and (
            (feature.geometry().wkbType() == QgsWkbTypes.Polygon)
            or (feature.geometry().wkbType() == QgsWkbTypes.MultiPolygon)
        )
    ):
        subdivided_parts = spilt_geometry_into_parts(feature.geometry())
        if len(subdivided_parts) > 0:
            feature.setGeometry(subdivided_parts[0])
            memory_layer.dataProvider().changeGeometryValues(
                {feature.id(): subdivided_parts[0]}
            )
            if len(subdivided_parts) > 1:
                for subdivided_part in subdivided_parts[1:]:
                    write_polygon_geometry_and_resource_id_to_a_new_feature(
                        memory_layer, feature, subdivided_part
                    )
memory_layer.commitChanges()

options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "CSV"
options.fileEncoding = "UTF-8"
options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
options.layerOptions = ["GEOMETRY=AS_WKT"]

success, message = QgsVectorFileWriter.writeAsVectorFormat(
    layer=memory_layer, fileName=str(outputfile_path), options=options
)
