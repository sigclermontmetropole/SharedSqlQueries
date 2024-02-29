"""
/***************************************************************************
 tools
                                 A QGIS plugin
                                 
 Outils (maptools)
  
                              -------------------
        begin                : 2014-09-02
        copyright            : (C) 2014 by JLebouvier
        email                : jlebouvier@ville-clermont-ferrand.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import math
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import * 
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from qgis.gui import *

class CreatePointTool(QgsMapTool):

    created = pyqtSignal(QgsGeometry)

    def __init__(self, canvas, deltaAngle = -90):
        QgsMapTool.__init__(self, canvas)
        self.mCanvas = canvas
        self.mLayer = None
        self.mRb = None
        self.mColor = QColor(255, 50, 50, 100)
        self.mWidth = 5
        self.cursor = QCursor(QPixmap(["17 17 3 1",
                                      "      c None",
                                      ".     c None",
                                      "+     c #000000",
                                      "                 ",
                                      "        +        ",
                                      "      +++++      ",
                                      "     +  +  +     ",
                                      "    +   +   +    ",
                                      "   +    +    +   ",
                                      "  +     +     +  ",
                                      " ++     +     ++ ",
                                      " ++++++++++++++++",
                                      " ++     +     ++ ",
                                      "  +     +     +  ",
                                      "   +    +    +   ",
                                      "   ++   +   +    ",
                                      "    ++  +  +     ",
                                      "      +++++      ",
                                      "       +++       ",
                                      "        +        "]))



    def canvasPressEvent(self, event):
        if self.mRb:
            self.mRb.reset()

    def canvasMoveEvent(self,event):
        if not self.mRb:
            self.mRb = QgsRubberBand(self.mCanvas, QgsWkbTypes.LineGeometry )
            self.mRb.setColor(self.mColor)
            self.mRb.setWidth(self.mWidth)   
                 
        self.mRb.reset()
        x = event.pos().x()
        y = event.pos().y()        
        pos = self.mCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        newGeom = QgsGeometry().fromPointXY(pos)

        # draw it to rubber
        self.mRb.setToGeometry( newGeom, None )  

        
    def canvasReleaseEvent(self,event):

        # get clicked coordinates
        x = event.pos().x()
        y = event.pos().y()        
        pos = self.mCanvas.getCoordinateTransform().toMapCoordinates(x, y)


        newGeom = QgsGeometry().fromPointXY(pos)
        self.mRb.reset()
        self.mRb.setToGeometry(newGeom, None)

        # event end editing geom
        self.created.emit(newGeom)

    
    def activate(self):
        self.mCanvas.setCursor(self.cursor)
  
    def deactivate(self):
        if self.mRb:
            self.mRb.reset()
            self.mRb = None
        if self != None:
            self.deactivated.emit()

    def isZoomTool(self):
        return False
  
    def isTransient(self):
        return False
    
    def isEditTool(self):
        return False


class CreateLineTool(QgsMapTool):

    created = pyqtSignal(QgsGeometry)

    def __init__(self, canvas, deltaAngle=-90):
        QgsMapTool.__init__(self, canvas)
        self.mCanvas = canvas
        self.mLayer = None
        self.mRb1 = None
        self.mRb2 = None
        self.mColor1 = QColor(255, 0, 0, 255)
        self.mColor2 = QColor(255, 0, 0, 255)
        self.mWidth1 = 2
        self.mWidth2 = 1
        self.mStyle1 = Qt.SolidLine
        self.mStyle2 = Qt.DashLine
        self.mPoints = []
        self.mGeom = None
        self.cursor = QCursor(QPixmap(["17 17 3 1",
                                       "      c None",
                                       ".     c None",
                                       "+     c #000000",
                                       "                 ",
                                       "        +        ",
                                       "      +++++      ",
                                       "     +  +  +     ",
                                       "    +   +   +    ",
                                       "   +    +    +   ",
                                       "  +     +     +  ",
                                       " ++     +     ++ ",
                                       " ++++++++++++++++",
                                       " ++     +     ++ ",
                                       "  +     +     +  ",
                                       "   +    +    +   ",
                                       "   ++   +   +    ",
                                       "    ++  +  +     ",
                                       "      +++++      ",
                                       "       +++       ",
                                       "        +        "]))

    def canvasPressEvent(self, event):
        if self.mRb1:
            self.mRb1.reset()

    def canvasMoveEvent(self, event):

        if not self.mRb2:
            self.mRb2 = QgsRubberBand(self.mCanvas, QgsWkbTypes.LineGeometry )
            self.mRb2.setColor(self.mColor2)
            self.mRb2.setWidth(self.mWidth2)
            self.mRb2.setLineStyle(self.mStyle2)

        self.mRb2.reset()
        if len(self.mPoints) > 0:
            # last point coordinate
            x = event.pos().x()
            y = event.pos().y()
            pos = self.mCanvas.getCoordinateTransform().toMapCoordinates(x, y)
            pt = self.mPoints[len(self.mPoints) - 1]
            if len(self.mPoints) > 1:
                #  polygon = [QgsPointXY(i[0],i[1]) for i in self.mPoints]
                polygon = [i for i in self.mPoints]
                polygon.append(pos)
                g = QgsGeometry.fromPolylineXY(polygon)
            else:
                g = QgsGeometry().fromPolylineXY([pt, pos])
            self.mRb2.setToGeometry( g, None )

    def canvasReleaseEvent(self, event):

        # get coordinates
        x = event.pos().x()
        y = event.pos().y()
        pos = self.mCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        # Rubber
        if not self.mRb1:
            self.mRb1 = QgsRubberBand(self.mCanvas, QgsWkbTypes.LineGeometry )
            self.mRb1.setColor(self.mColor1)
            self.mRb1.setWidth(self.mWidth1)
            self.mRb1.setLineStyle(self.mStyle1)


        # intermediate point
        if event.button() != Qt.RightButton:
            self.mPoints.append(pos)
            return
        else:
            if len(self.mPoints) < 3:
                return

        # save geom
        self.mGeom = None
        if len(self.mPoints) >= 3:
            self.mGeom = QgsGeometry().fromPolylineXY(self.mPoints)

        self.mRb1.reset()
        self.mRb2.reset()
        self.mRb1.setToGeometry(self.mGeom, None)

        # stop here for intermediate points
        # desactive sept 2022 if event.button() != Qt.RightButton: return

        # Save geom
        self.mGeom = None
        if len(self.mPoints) > 1:
            self.mGeom = QgsGeometry().fromPolylineXY(self.mPoints)

        # end editing event
        self.created.emit(self.mGeom)


    def activate(self):
        self.mCanvas.setCursor(self.cursor)


    def deactivate(self):
        if self.mRb1:
            self.mRb1.reset()
            self.mRb1 = None
            self.mRb2.reset()
            self.mRb2 = None
        if self != None:
            self.deactivated.emit()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False



class CreatePolygonTool(QgsMapTool):

    created = pyqtSignal(QgsGeometry)

    def __init__(self, canvas, deltaAngle=-90):
        QgsMapTool.__init__(self, canvas)
        self.mCanvas = canvas
        self.mLayer = None
        self.mRb1 = None
        self.mRb2 = None
        self.mColor1 = QColor(255, 0, 0, 100)
        self.mColor2 = QColor(255, 50, 0, 105)
        self.mWidth1 = 2
        self.mWidth2 = 1
        self.mStyle1 = Qt.SolidLine
        self.mStyle2 = Qt.DashLine
        self.mPoints = []
        self.mGeom = None
        self.cursor = QCursor(QPixmap(["17 17 3 1",
                                       "      c None",
                                       ".     c None",
                                       "+     c #000000",
                                       "                 ",
                                       "        +        ",
                                       "      +++++      ",
                                       "     +  +  +     ",
                                       "    +   +   +    ",
                                       "   +    +    +   ",
                                       "  +     +     +  ",
                                       " ++     +     ++ ",
                                       " ++++++++++++++++",
                                       " ++     +     ++ ",
                                       "  +     +     +  ",
                                       "   +    +    +   ",
                                       "   ++   +   +    ",
                                       "    ++  +  +     ",
                                       "      +++++      ",
                                       "       +++       ",
                                       "        +        "]))

    def canvasPressEvent(self, event):
        if self.mRb1:
            self.mRb1.reset()

    def canvasMoveEvent(self, event):

        if not self.mRb2:
            self.mRb2 = QgsRubberBand(self.mCanvas, QgsWkbTypes.LineGeometry )
            self.mRb2.setColor(self.mColor2)
            self.mRb2.setWidth(self.mWidth2)
            self.mRb2.setLineStyle(self.mStyle2)

        self.mRb2.reset()
        if len(self.mPoints) > 0:
            # last point coordinate
            x = event.pos().x()
            y = event.pos().y()
            pos = self.mCanvas.getCoordinateTransform().toMapCoordinates(x, y)
            pt = self.mPoints[len(self.mPoints) - 1]
            if len(self.mPoints) > 1:
                #  polygon = [QgsPointXY(i[0],i[1]) for i in self.mPoints]
                polygon = [i for i in self.mPoints]
                polygon.append(pos)
                g = QgsGeometry.fromPolygonXY([polygon])
            else:
                g = QgsGeometry().fromPolylineXY([pt, pos])
            self.mRb2.setToGeometry( g, None )

    def canvasReleaseEvent(self, event):

        # get coordinates
        x = event.pos().x()
        y = event.pos().y()
        pos = self.mCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        # Rubber
        if not self.mRb1:
            self.mRb1 = QgsRubberBand(self.mCanvas, QgsWkbTypes.LineGeometry )
            self.mRb1.setColor(self.mColor1)
            self.mRb1.setWidth(self.mWidth1)
            self.mRb1.setLineStyle(self.mStyle1)

        # intermediate point
        if event.button() != Qt.RightButton:
            self.mPoints.append(pos)
            return
        else:
            if len(self.mPoints) < 3:
                return

        # save geom
        self.mGeom = None
        if len(self.mPoints) >= 3:
            self.mGeom = QgsGeometry().fromPolygonXY([self.mPoints])

        self.mRb1.reset()
        self.mRb2.reset()
        self.mRb1.setToGeometry(self.mGeom, None)

        # stop here for intermediate points
        # desactive sept 2022 if event.button() != Qt.RightButton: return

        # Save geom
        self.mGeom = None
        if len(self.mPoints) > 1:
            self.mGeom = QgsGeometry().fromPolygonXY([self.mPoints])

        # end editing event
        self.created.emit(self.mGeom)

    def activate(self):
        self.mCanvas.setCursor(self.cursor)


    def deactivate(self):
        if self.mRb1:
            self.mRb1.reset()
            self.mRb1 = None
            self.mRb2.reset()
            self.mRb2 = None
        if self != None:
            self.deactivated.emit()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False