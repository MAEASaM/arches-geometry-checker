import pathlib
from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsApplication, QgsFields, QgsField, QgsFeature, QgsGeometry, QgsVectorDataProvider, QgsVectorLayerExporter, QgsWkbTypes, QgsVectorLayerExporter
from PyQt5.QtCore import QVariant

import argparse
import csv


QgsApplication.setPrefixPath("/usr/bin/qgis", True)
QgsApplication.setPrefixPath("/usr/share/qt5", True)

# qgs = QgsApplication([], False)
# qgs.initQgis()
# QgsApplication.setThemeName("PANTHEON")
# dummy_feedback = QgsProcessingFeedback()
# QgsApplication.processingFeedback().setProgressText(dummy_feedback)




csv_file = pathlib.Path("../data/example.csv")

memory_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "memory_layer", "memory")


# Open the CSV file for reading
with open(csv_file, "r") as csv_file:
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



# Parser = argparse.ArgumentParser(description='Check geometry validity for Arches')

# Parser.add_argument('--input', '-i', dest='input', required=True, help='Input file')

# args = Parser.parse_args()
# inputfile_name = pathlib.Path(args.input).name
# output = pathlib.Path(args.input).parent / (str(inputfile_name.stem) + '_valid' + str(inputfile_name.suffix))


# vector_layer = QgsVectorLayer(str(csv_file), "csv_layer", "delimitedtext")

# print(vector_layer.geometryType())

for feature in memory_layer.getFeatures():
    if (not feature.geometry().isEmpty()) and(not feature.geometry().isNull()):
        # Get the geometry of the feature
        original_geometry = feature.geometry()
        # Check if the geometry is a polygon and is not empty
        if original_geometry.isMultipart():  # Check if the geometry is a polygon
            # Iterate over the parts (rings) of the multipart geometry
            subdivided_parts = []
            for part in original_geometry.asGeometryCollection():
                # Apply the subdivide method to each part
                subdivided_part = part.subdivide(maxNodes=150)  # Replace 10 with your desired max nodes
                subdivided_parts.append(subdivided_part)
                if feature.attribute("ResourceID") == "ADMN-KEN-0000015":
                    print(subdivided_part)
            if len(subdivided_parts) == 1:
                memory_layer.dataProvider().changeGeometryValues({feature.id(): subdivided_parts[0]})
            else:
                # create a new feature for each part with olny the geometry and ResourceID
                for subdivided_part in subdivided_parts:
                    new_feature = QgsFeature(fields)
                    new_feature.setGeometry(subdivided_part)
                    new_feature.setAttribute("ResourceID", feature.attribute("ResourceID"))
                    memory_layer.dataProvider().addFeature(new_feature)
                # delete the original feature
                memory_layer.dataProvider().deleteFeatures([feature.id()])

# # Save changes to the layer
memory_layer.commitChanges()

csv_output_path = "../data/output.csv"

# Set up the writer parameters
options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "CSV"
options.fileEncoding = "UTF-8"
options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
options.layerOptions = ['GEOMETRY=AS_WKT']


# Write the layer to CSV
success, message = QgsVectorFileWriter.writeAsVectorFormat(memory_layer, csv_output_path, options)