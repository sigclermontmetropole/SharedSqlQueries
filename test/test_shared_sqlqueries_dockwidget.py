# coding=utf-8
"""DockWidget test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
from __future__ import absolute_import

__author__ = 'hchristol@ville-clermont-ferrand.fr'
__date__ = '2016-01-07'
__copyright__ = 'Copyright 2016, Ville de Clermont-Ferrand'

import unittest

from qgis.PyQt.QtGui import * 
from qgis.PyQt.QtWidgets import *

from shared_sqlqueries_dockwidget import SharedSqlQueriesDockWidget

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class SharedSqlQueriesDockWidgetTest(unittest.TestCase):
    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        self.dockwidget = SharedSqlQueriesDockWidget(None)

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_ok(self):
        """Test we can click OK."""
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(SharedSqlQueriesDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

