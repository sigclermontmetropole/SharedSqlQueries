﻿# -*- coding: utf-8 -*-
"""
/***************************************************************************
connection to pg a database whose paramaters are read in json config
 ***************************************************************************/
"""
from __future__ import print_function
from builtins import chr
from builtins import str
from builtins import object

import os
# deprecated from db_manager.db_plugins.postgis.connector import PostGisDBConnector
import psycopg2 # use standard postgresql python library instead of old db_managers
from qgis.core import *
from qgis.core import QgsVectorFileWriter
from qgis.PyQt import QtGui
from qgis.PyQt.QtCore import *

class Connection(object):
    #param : list with host, port, dbname :
    def __init__(self, param):
        self.param = param
        #set connector property for the given database type and parameters
        self.uri = QgsDataSourceUri()

        # optional parameters
        user=""
        if 'user' in self.param:
            user=str(self.param['user'])
        else :
            self.param['user'] = ''
        pwd=""

        if 'password' in self.param:
            pwd=str(self.param['password'])
        else :
            self.param['password'] = ''

        port='5432'
        if 'port' in self.param:
            port=str(self.param['port'])
        else :
            self.param['port'] = port

        self.uri.setConnection(
            str(self.param['host']),
            port,
            str(self.param['dbname']),
            user,
            pwd
        )

    # perform sql command and return data : [header, data, rowCount]
    def sqlExec(self, sql):

        sql = makeSqlValidForLayer(sql)

        # Execute a SQL query and, return [header, data, rowCount]

        # connexion with psycopg2 library
        conn = psycopg2.connect("dbname='" + self.param["dbname"]  \
                                + "' user='" + self.param["user"]  \
                                + "' host='" + self.param['host'] \
                                + "' port='" + str(self.param['port']) \
                                + "' password='" + self.param['password'] + "'")
        cur = conn.cursor()

        #print "DEBUG dbrequest : sql = " + sql

        try:
            cur.execute(str(sql))
            data = cur.fetchall()
            header = []
            for column in cur.description :
                header.append(column.name)
        except:
            print("Error SQL : " + str(sql))  # debug purpose
            raise

        row_count = len(data)

        cur.close()
        conn.close()

        return [header, data, row_count]

    #perform sql and return 1 value (None if no data)
    def sqlExec1Value(self, sql):
        [header, data,  row_count] = self.sqlExec(sql)
        if row_count == 0: return None
        return data[0][0]

    #perform sql and return 1 list of values (empty list if no data)
    def sqlExec1Column(self, sql):
        [header, data, row_count] = self.sqlExec(sql)
        list = []
        for row in data: list.append(row[0])
        return list

    # add a layer from an sql query. If another layer with the same name already exists, delete it.
    # return the added layer
    def sqlAddLayer(self, sql, layer_name, key_column, geom_column="geom", sqlFilter=""):

        sql = makeSqlValidForLayer(sql, ['%'])

        # allow query with no geometry column
        if geom_column == 'None':
            geom_column = None

        # print "DEBUG sqlAddLayer geom_column " + str(geom_column)
        self.uri.setDataSource("", "(" + sql + ")", geom_column, sqlFilter, key_column)

        layer = QgsVectorLayer(self.uri.uri(), layer_name, "postgres")

        return addLayer(layer)


    # add a layer into memory from sql. Suited for time consuming query.
    def sqlAddMemoryLayer(self, sql, layer_name, key_column, geom_column="geom", sqlFilter=""):

        sql = makeSqlValidForLayer(sql)

        self.uri.setDataSource("", "(" + sql + ")", geom_column, sqlFilter, key_column)

        # layer postgis to read features
        pg_layer = QgsVectorLayer(self.uri.uri(), "temporary layer", "postgres")

        # print "DEBUG sqlAddMemoryLayer : pg_layer.geometryType() =" + str(pg_layer.geometryType())

        # memory layer to store features
        srs = pg_layer.crs()
        if pg_layer.geometryType() > 2:
            exc = SyntaxError()
            exc.text = u"No geometry type found for memory layer ! Unable to load unknown geometry type !"
            print(sql)
            raise exc

        memory_layer = QgsVectorLayer(['Point', 'MultiLineString', 'MultiPolygon'][pg_layer.geometryType()] +
                                      "?crs=" + srs.authid(),
                                      layer_name, "memory")

        # provider used to create fields of memory layer
        provider = memory_layer.dataProvider()
        # add fields to memory layer
        memory_layer.startEditing()
        provider.addAttributes(pg_layer.dataProvider().fields().toList())
        memory_layer.updateFields()

        # Export features from pg_layer to memory_layer
        features = pg_layer.getFeatures()
        for feat in features:
            memory_layer.addFeature(feat)

        # validate
        result_commit = memory_layer.commitChanges()
        memory_layer.updateExtents()

        # print "DEBUG sqlAddMemoryLayer : memory_layer commit = " + str(result_commit)

        # add to legend
        return addLayer(memory_layer)

    # add a layer from sql and save it as a file (ogr_driver can be GeoJSON, ESRI Shapefile, ...).
    # Suited for time consuming query.
    def sqlAddFileLayer(self, sql, ogr_driver, layer_path, layer_name, key_column, geom_column="geom", sqlFilter=""):

        sql = makeSqlValidForLayer(sql)

        self.uri.setDataSource("", "(" + sql + ")", geom_column, sqlFilter, key_column)

        # layer postgis to read features
        pg_layer = QgsVectorLayer(self.uri.uri(), "temporary layer", "postgres")

        errorCode, errorMessage = QgsVectorFileWriter.writeAsVectorFormat(layer=pg_layer, fileName=layer_path, fileEncoding="utf-8",
                                                        destCRS=QgsCoordinateReferenceSystem(), driverName=ogr_driver)

        if errorCode == QgsVectorFileWriter.NoError:
            file_layer = QgsVectorLayer(layer_path, layer_name, "ogr")
            return addLayer(file_layer)
        else:
            exc = SyntaxError()
            exc.text = u"QgsVectorFileWriter error : " + errorMessage
            raise exc

    # fill a QtWidget (QComboBox) with the result of an sql query
    def sqlFillQtWidget(self, sql, list):
        [header, data, rowCount] = self.sqlExec(sql)
        model = QtGui.QStandardItemModel(list)
        for line in data:
            item = QtGui.QStandardItem()
            item.setText(line[0])
            item.setData(line, Qt.UserRole)
            model.appendRow(item)
        list.setModel(model)
        list.show()
        return [header, data, rowCount]

# transform sql so it can be loader as a layer data source
def makeSqlValidForLayer(sql, forbidenChar = []):
    # remove utf8 header character :
    sql = sql.replace(chr(65279), '')
    # remove new line characters
    sql = sql.replace(chr(13), ' ').replace(chr(10), ' ').replace('\t', ' ')
    # remove ; and blanck at the end of sql
    sql = sql.strip(' ;')

    #print sql

    # error if forbiden caracter %
    for c in forbidenChar:
        if c in sql:
            exc = SyntaxError()
            exc.text = u"% is not allowed in SQL QGIS layer : please use mod function instead"
            raise exc

    return sql

def addLayer(layer):

    # Existing layer ?
    layerList = QgsProject.instance().mapLayersByName(layer.name())
    if (len(layerList)>0):
        QgsProject.instance().removeMapLayer(layerList[0].id())

    # add layer to registry and affect same layer variable to the result,
    # to be sure it had been correctly added (None result if not)

    # before adding layer, ensure that it will be put on the top of all layers
    QgsProject.instance().layerTreeRegistryBridge().setLayerInsertionPoint(QgsProject.instance().layerTreeRoot(), 0)

    layer = QgsProject.instance().addMapLayer(layer, True)

    return layer