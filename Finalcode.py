import sys
import os
from qgis.core import (
    QgsProject,
    QgsApplication,
    QgsLayoutItemLabel,
    QgsPrintLayout,
    QgsLayoutItemMap,
    QgsLayoutItemLegend,
    QgsLayoutItemPicture,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsUnitTypes,
    QgsLayoutExporter,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
    QgsPalLayerSettings,
    QgsRectangle,
    QgsSimpleLineSymbolLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsLayoutItemScaleBar,
    QgsLegendStyle
)
from qgis.PyQt.QtGui import QColor, QFont


# Set the path to your QGIS installation
qgis_path = r"C:/Program Files/QGIS 3.34.14/apps/qgis"
# Define the path to save the image
image_path = r"D:\LABROTATION\Hessen\District_Maps"

# Configure the QGIS environment
QgsApplication.setPrefixPath(qgis_path, True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Set Project CRS to EPSG:25832
project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:25832"))  # Ensures Hessen CRS
QgsProject.instance().write()  # Save settings

# Define OSM XYZ tile layer correctly (Keep EPSG:3857)
osm_url = "type=xyz&zmin=0&zmax=19&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
osm_layer = QgsRasterLayer(osm_url, "OpenStreetMap", "wms")

# Ensure OSM is in EPSG:3857
osm_layer.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

if not osm_layer.isValid():
    print("Failed to load OpenStreetMap!")
else:
    QgsProject.instance().addMapLayer(osm_layer)
    print("OpenStreetMap successfully added as the base map!")

# Paths to shapefiles
path_hessen_districts = r"D:/LABROTATION/DigVGr-epsg25832-shp/KREIS_LA.shp"

# Load the Hessen Districts layer
vlayer_Hessen_districts = QgsVectorLayer(path_hessen_districts, "Hessen Districts Layer", "ogr")
if not vlayer_Hessen_districts.isValid():
    print("Hessen Districts Layer failed to load!")
else:
    QgsProject.instance().addMapLayer(vlayer_Hessen_districts)
    print("Hessen Districts Layer successfully loaded!")

# Apply unique colors to categories based on an attribute
field_name = "KREIS_BZ"  # Replace with the actual attribute field you want to categorize
categories = []

# Iterate through unique values in the field to assign colors
unique_values = sorted(vlayer_Hessen_districts.uniqueValues(vlayer_Hessen_districts.fields().indexOf(field_name)))
num_values = len(unique_values) 
#for value in unique_values:
for i, value in enumerate(unique_values):
    symbol = QgsSymbol.defaultSymbol(vlayer_Hessen_districts.geometryType())
    #symbol.setColor(QColor.fromHsv(hash(value) % 360, 255, 255))  # Assign unique color
    # Ensure unique hues by spreading them evenly
    hue = (i * 137) % 360  # 137 is chosen to maximize hue spread and avoid clustering
    symbol.setColor(QColor.fromHsv(hue, 255, 255))  # Assign unique color
    category = QgsRendererCategory(value, symbol, str(value))  # Create category
    categories.append(category)

# Set categorized renderer
renderer = QgsCategorizedSymbolRenderer(field_name, categories)
vlayer_Hessen_districts.setRenderer(renderer)
vlayer_Hessen_districts.triggerRepaint()
print("Unique colors have been applied to each district.")

# Paths to additional layers
path_Hessen_highways = r"D:\LABROTATION\INDIA\hessen_data\hessen_data\hessen_highways_only.gpkg"
path_Hessen_waterlines = r"D:\LABROTATION\INDIA\hessen_data\hessen_data\hessen_waterlines.gpkg"

# Load the Hessen Highways layer
vlayer_Hessen_highways = QgsVectorLayer(path_Hessen_highways, "Hessen Highways Layer", "ogr")
if not vlayer_Hessen_highways.isValid():
    print("Hessen Highways Layer failed to load!")
else:
# Apply styling: Black color with increased thickness
    highway_symbol = QgsSymbol.defaultSymbol(vlayer_Hessen_highways.geometryType())
    if highway_symbol:
        line_symbol_layer = QgsSimpleLineSymbolLayer(color=QColor("black"), width=0.6)  # Adjust width as needed
        highway_symbol.changeSymbolLayer(0, line_symbol_layer)
        vlayer_Hessen_highways.renderer().setSymbol(highway_symbol)
        vlayer_Hessen_highways.triggerRepaint()  # Refresh the layer
    QgsProject.instance().addMapLayer(vlayer_Hessen_highways)
    print("Hessen Highways Layer successfully loaded and styled!")
    
# Load the Hessen Waterlines layer
vlayer_Hessen_waterlines = QgsVectorLayer(path_Hessen_waterlines, "Hessen Waterlines Layer", "ogr")
if not vlayer_Hessen_waterlines.isValid():
    print("Hessen Waterlines Layer failed to load!")
else:
# Apply styling: Blue color with increased thickness
    waterline_symbol = QgsSymbol.defaultSymbol(vlayer_Hessen_waterlines.geometryType())
    if waterline_symbol:
        line_symbol_layer = QgsSimpleLineSymbolLayer(color=QColor("blue"), width=0.3)  # Adjust width as needed
        waterline_symbol.changeSymbolLayer(0, line_symbol_layer)
        vlayer_Hessen_waterlines.renderer().setSymbol(waterline_symbol)
        vlayer_Hessen_waterlines.triggerRepaint()  # Refresh the layer
    QgsProject.instance().addMapLayer(vlayer_Hessen_waterlines)
    print("Hessen Waterlines Layer successfully loaded and styled!")

 

# Loop through each district and generate a separate map
for district in unique_values:
    print(f"Processing district: {district}")

    # Apply filter to show only the current district
    expression = f'"{field_name}" = \'{district}\''
    vlayer_Hessen_districts.setSubsetString(expression)

    # Reference to the project instance
    project = QgsProject.instance()
    layout_manager = project.layoutManager()

    # Create a new print layout
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(f"District Map - {district}")

    # Check for existing layouts with the same name and remove them
    for existing_layout in layout_manager.printLayouts():
        if existing_layout.name() == layout.name():
            layout_manager.removeLayout(existing_layout)

    # Add the new layout to the layout manager
    layout_manager.addLayout(layout)

    # Access the layout's page collection
    page = layout.pageCollection().pages()[0]
    
    # Set smaller page size for district maps
    page.setPageSize(QgsLayoutSize(125, 125, QgsUnitTypes.LayoutMillimeters))  # Adjust page size for district

    # Create a map item
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(10, 10, 200, 200)  # Set a smaller map size
    
    district_extent = vlayer_Hessen_districts.extent()
    buffer = 20000  # Adjust this value if necessary (in map units)
    padded_extent = QgsRectangle(
        district_extent.xMinimum() - buffer,
        district_extent.yMinimum() - buffer,
        district_extent.xMaximum() + buffer,
        district_extent.yMaximum() + buffer
    )

    map_item.zoomToExtent(padded_extent)
    map_item.setFrameEnabled(True)  # Enable frame to debug if map is being cut off

    # Set the extent to the current district's bounding box
    map_item.setExtent(vlayer_Hessen_districts.extent())

    map_item.setScale(map_item.scale() * 1.8)  # Adjust to zoom out slightly

    # Adjust the map position and size
    map_item.attemptMove(QgsLayoutPoint(5, 25, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(70,70, QgsUnitTypes.LayoutMillimeters))  # Adjusted size

    # Add the map item to the layout
    layout.addLayoutItem(map_item)

    # Add a title
    title = QgsLayoutItemLabel(layout)
    title.setText(f"District: {district}")
    title.setFont(QFont('Arial', 12, QFont.Bold))
    title.adjustSizeToText()
    
    # Center title horizontally
    title_width = title.rectWithFrame().width()
    center_x = (120 - title_width) / 2
    title.attemptMove(QgsLayoutPoint(center_x, 10, QgsUnitTypes.LayoutMillimeters))
    
    layout.addLayoutItem(title)

    # Add a scale bar
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setStyle('Single Box')
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegments(3)
    scalebar.setUnitsPerSegment(5)  # Adjusted scale for district maps
    scalebar.setLinkedMap(map_item)
    scalebar.setUnitLabel('km')
    scalebar.setFont(QFont('Arial', 8))
    scalebar.update()
    layout.addLayoutItem(scalebar)
    scalebar.attemptMove(QgsLayoutPoint(10,100, QgsUnitTypes.LayoutMillimeters))

    # Add a district-specific legend
    district_legend = QgsLayoutItemLegend(layout)
    district_legend.setTitle(f"Legend - {district}")
    district_legend.setLinkedMap(map_item)
    district_legend.setAutoUpdateModel(False)  # Disable automatic updates

    legend_model = district_legend.model()

    while legend_model.rowCount() > 0:
        legend_model.removeRow(0)

    # Add only the current district's symbol to the legend
    for category in renderer.categories():
        if category.value() == district:
            legend_model.insertRow(0)
            index = legend_model.index(0, 0)
            legend_model.setData(index, category.label())
            
    # Reduce text size in the legend
    small_font = QFont()
    small_font.setPointSize(7)  # Adjust font size as needed
    district_legend.setStyleFont(QgsLegendStyle.Title, small_font)  # Font for the legend title
    district_legend.setStyleFont(QgsLegendStyle.SymbolLabel, small_font)  # Font for legend symbol labels


    district_legend.attemptMove(QgsLayoutPoint(80, 30, QgsUnitTypes.LayoutMillimeters))
    district_legend.attemptResize(QgsLayoutSize(5, 10, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(district_legend) 
    # Define the path to save the image
    district_image_path = os.path.join(image_path, f"{district}.png")

    # Export the layout to an image
    exporter = QgsLayoutExporter(layout)
    result = exporter.exportToImage(district_image_path, QgsLayoutExporter.ImageExportSettings())
    if result == QgsLayoutExporter.Success:
        print(f"Map for {district} successfully saved to {district_image_path}")
    else:
        print(f"Failed to export map for {district}")

# Reset the subset filter after exporting all maps
vlayer_Hessen_districts.setSubsetString("")
    
    
# Ensure all layers align
combined_extent = vlayer_Hessen_districts.extent()
combined_extent.combineExtentWith(vlayer_Hessen_highways.extent())
combined_extent.combineExtentWith(vlayer_Hessen_waterlines.extent())    


# Create Print Layout
layout_manager = project.layoutManager()
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName("Hessen State and Districts Layout")


# Check for existing layouts with the same name and remove them
for existing_layout in layout_manager.printLayouts():
    if existing_layout.name() == layout.name():
        layout_manager.removeLayout(existing_layout)

# Add the new layout to the layout manager
layout_manager.addLayout(layout)

# Access the layout's page collection
page = layout.pageCollection().pages()[0]

# Set page size to Square (320 x 320 mm) in portrait orientation
page.setPageSize(QgsLayoutSize(320, 320, QgsUnitTypes.LayoutMillimeters))  # Square size in mm (320x320)


# Add Map Item
map_item = QgsLayoutItemMap(layout)
map_item.setRect(10, 10, 200, 200)
map_item.setExtent(combined_extent)
map_item.attemptMove(QgsLayoutPoint(10, 20, QgsUnitTypes.LayoutMillimeters))
map_item.attemptResize(QgsLayoutSize(190, 280, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(map_item)

# Add a title to the layout
title = QgsLayoutItemLabel(layout)
title.setText("Hessen")
title.setFont(QFont('Arial', 20, QFont.Bold))
title.adjustSizeToText()

# Position the title at the center of the A4 page (210 mm width)
title_width = title.rectWithFrame().width()
center_x = (320 - title_width) / 2
title.attemptMove(QgsLayoutPoint(center_x, 10, QgsUnitTypes.LayoutMillimeters))

# Add the title label to the layout
layout.addLayoutItem(title)

# Add a legend
legend = QgsLayoutItemLegend(layout)
legend.setTitle("Legend")
legend.setLinkedMap(map_item)
layout.addLayoutItem(legend)
legend.attemptMove(QgsLayoutPoint(220, 60, QgsUnitTypes.LayoutMillimeters))
legend.attemptResize(QgsLayoutSize(50,100,QgsUnitTypes.LayoutMillimeters))
                    
# Add a north arrow
north_arrow = QgsLayoutItemPicture(layout)
north_arrow.setPicturePath(r"C:/Users/hp/Desktop/images.svg")  # Update path to your north arrow
north_arrow.attemptMove(QgsLayoutPoint(240, 10, QgsUnitTypes.LayoutMillimeters))
north_arrow.attemptResize(QgsLayoutSize(35, 35, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(north_arrow)

# Add a scale bar
scalebar = QgsLayoutItemScaleBar(layout)
scalebar.setStyle('Single Box')
scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
scalebar.setNumberOfSegments(5)
scalebar.setNumberOfSegmentsLeft(0)  # Number of segments to the left
scalebar.setUnitsPerSegment(10)
scalebar.setLinkedMap(map_item)
scalebar.setUnitLabel('km')
scalebar.setFont(QFont('Arial', 14))
scalebar.update()
scalebar.attemptMove(QgsLayoutPoint(20, 300, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(scalebar)


# Position the scale bar
scalebar.attemptMove(QgsLayoutPoint(20, 300, QgsUnitTypes.LayoutMillimeters))  # Adjust position as needed




# Ensure the directory exists before writing
import os
os.makedirs(os.path.dirname(image_path), exist_ok=True)

# Refresh the layout before exporting
layout.refresh()

# Export the layout to an image
exporter = QgsLayoutExporter(layout)
hessen_map_path = r"D:\LABROTATION\Hessen\District_Maps\Hessen_State_Map.png"
result = exporter.exportToImage(hessen_map_path, QgsLayoutExporter.ImageExportSettings())

if result == QgsLayoutExporter.Success:
    print(f"Map successfully saved to {hessen_map_path}")
else:
    print("Failed to export the map.")



# Save the project to a QGZ file
project_path = r"D:/LABROTATION/INDIA/Hessen_Project.qgz"

if project.write(project_path):
    print(f"Project successfully saved to {project_path}")
else:
    print("Failed to save the project.")

