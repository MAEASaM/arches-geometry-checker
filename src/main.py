import pathlib
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
)
from PyQt5.QtCore import QVariant

import argparse
import csv

Parser = argparse.ArgumentParser(description="Check geometry validity for Arches")

Parser.add_argument(
    "--input",
    "-i",
    dest="input",
    required=True,
    help="Input file deafults to ../data/example.csv",
    default=pathlib.Path("../data/example.csv"),
)

args = Parser.parse_args()
inputfile_path = args.input
inputfile_name = pathlib.Path(args.input).name
outputfile_path = pathlib.Path(args.input).parent / (
    str(inputfile_name.stem) + "_valid" + str(inputfile_name.suffix)
)

maxNodes = 150

QgsApplication.setPrefixPath("/usr/bin/qgis", True)
QgsApplication.setPrefixPath("/usr/share/qt5", True)


memory_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "memory_layer", "memory")


# Open the CSV file for reading
with open(inputfile_path, "r") as csv_file:
    # Read the CSV data using the Python CSV reader
    csv_data = csv.DictReader(csv_file)

    list_of_csv_fieldnames = csv_data.fieldnames

    # Define fields for the layer
    fields = QgsFields()
    # fields.append(QgsField("ID", QVariant.Int))
    for fieldname in list_of_csv_fieldnames:
        fields.append(QgsField(fieldname, QVariant.String))

    # Add fields to the layer
    memory_layer.dataProvider().addAttributes(fields)

    # Update fields and refresh the layer
    memory_layer.updateFields()

    # Iterate over CSV data and add features to the layer
    for row in csv_data:
        # Create a new feature
        feature = QgsFeature(fields)

        # Set other attributes from the CSV data
        for fieldname in list_of_csv_fieldnames:
            if fieldname != "Geometry":
                feature.setAttribute(fieldname, row[fieldname])

        # Parse WKT and create QgsGeometry
        wkt_geometry = row["Geometry"]
        geometry = QgsGeometry.fromWkt(wkt_geometry)

        # set the geometry
        feature.setGeometry(geometry)

        # Add the feature to the layer
        memory_layer.dataProvider().addFeature(feature)

    # Refresh the layer
    memory_layer.updateExtents()


def write_polygon_geometry_and_resource_id_to_a_new_feature(
    memory_layer, feature, polygon_geometry
):
    # Create a new feature
    new_feature = QgsFeature(fields)

    # Set geometry and ResourceID
    new_feature.setGeometry(polygon_geometry)
    new_feature.setAttribute("ResourceID", feature.attribute("ResourceID"))

    # Add the feature to the layer
    memory_layer.dataProvider().addFeature(new_feature)


def spilt_one_polygon_into_parts(polygon_geometry):
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
            (feature.geometry().wkbType() == QgsWkbTypes.PolygonGeometry)
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
# # Save changes to the layer
memory_layer.commitChanges()

csv_output_path = "../data/output.csv"

# Set up the writer parameters
options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "CSV"
options.fileEncoding = "UTF-8"
options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
options.layerOptions = ["GEOMETRY=AS_WKT"]

# Write the layer to CSV
success, message = QgsVectorFileWriter.writeAsVectorFormat(
    layer=memory_layer, fileName=csv_output_path, options=options
)
