=======================
EpilepsiaeSQLDataloader
=======================


.. image:: https://img.shields.io/pypi/v/epilepsiae_sql_dataloader.svg
        :target: https://pypi.python.org/pypi/epilepsiae_sql_dataloader

.. image:: https://img.shields.io/travis/dschonholtz/epilepsiae_sql_dataloader.svg
        :target: https://travis-ci.com/dschonholtz/epilepsiae_sql_dataloader

.. image:: https://readthedocs.org/projects/epilepsiae-sql-dataloader/badge/?version=latest
        :target: https://epilepsiae-sql-dataloader.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/dschonholtz/epilepsiae_sql_dataloader/shield.svg
     :target: https://pyup.io/repos/github/dschonholtz/epilepsiae_sql_dataloader/
     :alt: Updates



This leverages the https://epilepsiae.uniklinik-freiburg.de/ epilepsy dataset to allow you to arbitrarily query data for an ML dataloader. You must have the raw binary data to configure a SQL DB or a preconfigured DB that you can reference for the dataloader.


* Free software: MIT license
* Documentation: https://epilepsiae-sql-dataloader.readthedocs.io.


Features
--------

* Build SQL Alchemy Tables that all of the epilepsiae data can be loaded into and be queried from
* Build a dataloader that can be used to load data into a ML model

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
