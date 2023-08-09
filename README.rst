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


SETUP
-----

The majority of the time you are going to want to use the DataLoaders in DataDinghy for your machine learning model. However, before you can do that. You'll have to do a fairly large amount of set up.

1. Download the raw data from https://epilepsiae.uniklinik-freiburg.de/ and place it in a directory.
This is between you and them and we did it with an SFTP connection. The important bit here is the destination directories.
This repo only handles inv and surf30 datasets. The inv dataset comes in multiple chunks and for the purposes of this project everything was
moved into the inv dir.

For us they live on an external drive at /mnt/external1/raw/inv and /mnt/external1/raw/surf30

2. Setup postgreSQL. 

This should be fairly easy. We cloned the repository onto our server and then ran the commands in the makefile:

`make run-postgres`
`make create-db`

This sets up and instantiates a postgres server with the tables defined in epilepsiae_sql_dataloader/models

3. Add metadata to the database

This will add all of the seizure and patient/sample metadata to the database. This way we can quickly query when seizures happened for what patients in what datasets without having to do raw file navigation.

To do this you can run the following command:

```bash
cd epilepsiae_sql_dataloader
python -m venv venv
source venv/bin/activate
pip install -e .
python -m epilepsiae_sql_dataloader.RelationalRigging.MetaDataBuilder --directories /mnt/external1/raw/inv --directories /mnt/external1/raw/surf30 --drop-tables
```

This does the following:
1. Install a python virtual environment
2. Installs the entire repo as a python package
3. Runs the MetaDataBuilder script with the directories specified. This will take a while. It will also drop the tables and recreate them. This is useful if you want to update the metadata.

Notice, you may want to look at the RelationalRiggingMetaDataBuilder.py file to figure out exactly what options you want.


4. Add the binary data to the database

Assuming you are still in the virtual environment you can run the following command:

```bash
python epilepsiae_sql_dataloader/RelationalRigging/PushBinaryToSql.py --dir /mnt/external1/raw/inv
```

For right now there is no option to drop the tables, or to add multiple directories.


5. Use the dataloaders.

You can now use the dataloaders in DataDinghy to load data into your ML model.
It is worth noting, as long as the database is set up, you can pip install this package
and use it in your project without having to deal directly with the source code.

The dataloaders are a work in progress though and will be published shortly

Features
--------

* Build SQL Alchemy Tables that all of the epilepsiae data can be loaded into and be queried from
* Build a dataloader that can be used to load data into a ML model

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
