.. sphinx-colored-tables documentation master file, created by
   sphinx-quickstart on Wed Apr 23 08:52:59 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

sphinx-colored-tables documentation
===================================

.. csv-table:: csv-table directive
   :file: _static/sample.csv
   :header-rows: 1
   :align: center

.. colored-csv-table:: colored-csv-table directive 
   :file: _static/sample.csv
   :header-rows: 1
   :align: center
   :color-column: Category
   :color-map: High=red, Medium=orange, Low=green