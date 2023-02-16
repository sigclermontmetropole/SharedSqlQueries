SET PATH=C:\QGIS_Beta\apps\Python37\Scripts;C:\OSGeo4W64\bin;C:\OSGeo4W64\apps\Qt5\bin;%PATH%
SET PYUIC="C:\QGIS_Beta\apps\Python37\Scripts\pyuic5.bat"
SET PYRCC="C:\QGIS_Beta\apps\Python37\Scripts\pyrcc5.bat" 
C:
cd "C:\QGIS3_ProfileLocal\herve-plugindev\SharedSqlQueries"
%PYRCC% -o resources.py resources.qrc
pause