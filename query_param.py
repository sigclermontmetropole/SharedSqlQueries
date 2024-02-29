﻿from __future__ import absolute_import
from builtins import str
import os
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtGui import * 
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import Qt, QObject

from qgis.gui import QgsMapCanvas, QgsRubberBand
from qgis.core import QgsVectorLayer, QgsWkbTypes

from .customSqlQuery import CustomSqlQuery
from .translate import tr

from .tools import tools_points

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'query_param.ui'))

# header param that should not be shown to user
HIDDEN_HEADER_VALUE = {'gid', 'geom', 'layer storage', 'result as'}

# dialog to edit query parameters
class QueryParamDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, dbrequest, query, parent=None):

        """Constructor."""
        super(QueryParamDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.iface = iface
        self.dbrequest = dbrequest
        self.query = query

        #translate widget
        self.setWindowTitle(tr(self.windowTitle()))

        # index of widget by param name
        self.widgetParam = None

        # in case of failure
        self.errorMessage = ""

        self.buttonBox.accepted.connect(self.DialogToParametersUpdate)

        # edit geom button
        self.mToolbar = QToolBar() # self.widget.addToolBar(self.widget.mPluggin_name)
        self.mToolbar.setMinimumSize(100, 40)
        self.mToolbar.setOrientation(Qt.Horizontal)
        self.tools = None # array of tools to be used to edit a potential custom geometry parameter
        self.editedGeom = None # current edited geometry

        # rubber to display edited geom after it has been validated
        self.mRb = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry )
        self.mRb.setColor(QColor(255, 20, 20, 200))
        self.mRb.setWidth(5)


        # dialog init
    def showEvent(self, evnt):
        super(QueryParamDialog, self).showEvent(evnt)
        self.ParametersToDialogUpdate()

    # add widgets to the dialog that are related to each editable parameter
    def ParametersToDialogUpdate(self):
        query = self.query
        self.labelQueryName.setText(query.name)

        # index for param, header param separated from other param
        self.widgetParam = {"header": {}, "param": {}}

        for header_or_param in {"header", "param"}:

            listParam = self.query.param
            if header_or_param == "header":
                listParam = self.query.header

            def sort_param(key):
                return listParam[key]["order"]

            for paramName in sorted(listParam, key=sort_param): # in listParam:

                # ignore hidden header parameters
                if header_or_param == "header":
                    if paramName in HIDDEN_HEADER_VALUE:
                        continue

                value = listParam[paramName]
                # add param to dialog and index its widget
                self.widgetParam[header_or_param][paramName] = self.addParam(tr(paramName), value)

        # adjust dialog size
        self.setFixedHeight(40 + self.gridLayoutHeader.rowCount() * 25)

    # add a param in dialog
    def addParam(self, paramName, value):
        grid = self.gridLayoutHeader

        row_number = grid.rowCount()

        # type of parameter
        [type_widget, type_options, name] = splitParamNameAndType(paramName)

        # name
        grid.addWidget(QLabel(name), row_number, 0)

        # value
        if "value" in value:
            value = value["value"]
        else:
            value = value["default"]

        # update widget

        if type_widget == "text":
            edit_widget = QLineEdit()
            edit_widget.setText(value)

        elif type_widget == "date":
            edit_widget = QDateEdit()
            edit_widget.setCalendarPopup(True)
            edit_widget.lineEdit().setText(value)

        elif type_widget == "select":
            edit_widget = QComboBox()
            edit_widget.setEditable(True)
            self.dbrequest.sqlFillQtWidget(type_options, edit_widget)
            edit_widget.setEditText(value)

        elif type_widget == "selected_item":
            if type_options != "geom":
                edit_widget = QLabel(tr(u"Attribute of selected feature") + " : " + type_options)
            else:
                edit_widget = QLabel(tr(u"Geometry of selected feature"))

        elif type_widget == "selected_items" or type_widget == "selected_items_text":
            if type_options != "geom":
                edit_widget = QLabel(tr(u"Attribute of selected features") + " : " + type_options)
            else:
                edit_widget = QLabel(tr(u"Geometry of selected features"))

        elif type_widget == "edited_geom":
            # geometry required
            self.mToolbar.setVisible(True)
            edit_widget = self.mToolbar
            self.tools = []

            if type_options.rfind("point")>=0:
                self.CreateEditingTool(tools_points.CreatePointTool(self.iface.mapCanvas()),
                                       tr(u"Click a point on map"),
                                       u":/plugins/SharedSqlQueries/resources/createpoint.svg")

            if type_options.rfind("line")>=0:
                self.CreateEditingTool(tools_points.CreateLineTool(self.iface.mapCanvas()),
                                       tr(u"CLick a line on map"),
                                       u":/plugins/SharedSqlQueries/resources/createline.svg")

            if type_options.rfind("polygon")>=0:
                self.CreateEditingTool(tools_points.CreatePolygonTool(self.iface.mapCanvas()),
                                       tr(u"CLick a line on map"),
                                       u":/plugins/SharedSqlQueries/resources/createpolygon.svg")


        grid.addWidget(edit_widget, row_number, 1)
        return edit_widget

    # create tools for editing geometry
    def CreateEditingTool(self, tool, tooltip, svg):

        idtool = len(self.tools)
        self.tools.append(tool)

        def geometryEdited(geom):
            self.editedGeom=geom
            activateTool(False) # end editing
            self.mRb.setToGeometry(geom, None)

        def activateTool(state):
            tool = self.tools[idtool]
            ActivateTool(self.iface.mapCanvas(), tool, state, self.tools)

            # edit event
            try :
                tool.created.disconnect(geometryEdited)
            except : pass
            if state:
                tool.created.connect(geometryEdited)
#            else:
#                self.editedGeom=None

        # Création du bouton et ajout du bouton à la toolbar
        self.mToolbar.addAction(
            CreateAction(self.iface, activateTool, self.tools[idtool] , \
                tooltip, svg)
        )


    # update parameters of query
    def DialogToParametersUpdate(self):

        # update all parameters from dialog widget
        for header_or_param in {"header", "param"}:

            listParam = self.query.param
            if header_or_param == "header":
                listParam = self.query.header

            for paramName in list(self.widgetParam[header_or_param].keys()):

                # widget linked to this parameter
                widget = self.widgetParam[header_or_param][paramName]
                param = listParam[paramName]

                [type_widget, type_options, name] = splitParamNameAndType(paramName)

                # update value param

                if type_widget == "text":
                    param["value"] = widget.text()

                elif type_widget == "date":
                    param["value"] = widget.lineEdit().text()

                elif type_widget == "select":
                    param["value"] = widget.currentText()

                # selected item : read the attribute of a selected item on map
                elif type_widget == "selected_item":

                    currentLayer = self.iface.mapCanvas().currentLayer()
                    if not type(currentLayer) is QgsVectorLayer:
                        self.errorMessage = tr(u"Select a vector layer !")
                        continue
                    if currentLayer.selectedFeatureCount() != 1:
                        self.errorMessage = tr(u"Select just one feature on map !")
                        continue
                    currentFeature = currentLayer.selectedFeatures()[0]

                    # standard attribute :
                    if type_options != "geom":

                        if currentFeature.fields().indexFromName(type_options) == -1:
                            self.errorMessage = tr(u"This feature does not have such an attribute : ") + type_options
                            continue
                        param["value"] = str(currentFeature.attribute(type_options))

                    # geom attribut :
                    else:
                        geom = currentFeature.geometry()

                        param["value"] = "ST_GeomFromEWKT('SRID=" + str(currentLayer.crs().postgisSrid()) + ";" \
                                         + geom.asWkt() + "')"

                # several selected items :  read the attribute or geometry of several selected item on map
                elif type_widget == "selected_items" or type_widget == "selected_items_text":

                    currentLayer = self.iface.mapCanvas().currentLayer()
                    if not type(currentLayer) is QgsVectorLayer:
                        self.errorMessage = tr(u"Select a vector layer !")
                        continue
                    if currentLayer.selectedFeatureCount() <= 0:
                        self.errorMessage = tr(u"Select one or more feature on map !")
                        continue
                    currentFeatures = currentLayer.selectedFeatures()

                    # standard attribute :
                    if type_options != "geom":

                        if currentFeatures[0].fields().indexFromName(type_options) == -1:
                            self.errorMessage = tr(u"This feature does not have such an attribute : ") + type_options
                            continue

                        sql_liste = ""
                        for f in currentFeatures :
                            geom = f.geometry()
                            if sql_liste != "":
                                sql_liste += ", "
                            if type_widget == "selected_items_text":  # text field
                                sql_liste += "'" + str(f.attribute(type_options)) + "'"
                            else:  # numeric field
                                sql_liste += str(f.attribute(type_options))

                        param["value"] = sql_liste

                    # geom attribut :
                    else:
                        sql_liste = ""
                        for f in currentFeatures :
                            geom = f.geometry()
                            if sql_liste != "":
                                sql_liste += ", "
                            sql_liste += "ST_GeomFromEWKT('SRID=" + str(currentLayer.crs().postgisSrid()) + ";" \
                                         + geom.asWkt() + "')"

                        param["value"] = sql_liste

                # selected item : try to read the attribute of a selected item on map
                elif type_widget == "edited_geom":
                    geom = self.editedGeom
                    param["value"] = "ST_GeomFromEWKT('SRID=" + str(self.iface.mapCanvas().mapSettings().destinationCrs().postgisSrid()) + ";" \
                                 + geom.asWkt() + "')"


# return the type of parameter
def splitParamNameAndType(paramName):
    # default values
    type_widget = "text"
    type_options = ""
    name = paramName

    for possible_type in ["text", "date", "select", "selected_item", "selected_items", "selected_items_text", "edited_geom"]:
        searched = possible_type + " "
        i = paramName.strip().find(searched)
        if i == 0:
            type_widget = possible_type

            # type options ( for type with : mytype myoptions; )
            if possible_type == "select" or possible_type == "selected_item" or \
                    possible_type == "selected_items" or possible_type == "selected_items_text" or possible_type == "edited_geom" :
                i_end_type_with_option = paramName.strip().find(";")
                type_options = paramName.strip()[:i_end_type_with_option]
                searched = type_options + ";"

            # remove type name from option (return myoptions istead of mytype myoptions)
            if possible_type == "selected_item" or possible_type == "selected_items" or possible_type == "selected_items_text" or possible_type == "edited_geom":
                type_options = type_options[len(possible_type + " "):].strip()

            name = paramName.strip()[len(searched):].strip()

            return [type_widget, type_options, name]

    return [type_widget, type_options, name]

# create an action related to a given QgsMapTool tool
def CreateAction(iface, fct_action, tool, tooltip, icone):

    action = QAction(
        QIcon(icone),
        tooltip, iface.mainWindow())
    action.toggled.connect(fct_action)
    action.setCheckable(True)
    if tool != None:
        tool.setAction(action)
    return action

# activate or desactivate a QgsMapTool tool
def ActivateTool(canvas, tool, etat, otherTools = None):

    # En fonction du nouvel état j'active ou non l'outil correspondant
    if etat:
        if tool.action().isVisible():
            canvas.setMapTool(tool)
        else: #desactive outil s'il n'est pas visible
            canvas.unsetMapTool(tool)
            tool.deactivate()
            tool.action().setChecked(False)

        # others tools to be desactivated ?
        if otherTools is not None :
            for otherTool in otherTools:
                if (otherTool != tool):
                    canvas.unsetMapTool(otherTool)
                    otherTool.action().setChecked(False)
                    otherTool.deactivate()
    else:
        canvas.unsetMapTool(tool)
        tool.deactivate()
        tool.action().setChecked(False)