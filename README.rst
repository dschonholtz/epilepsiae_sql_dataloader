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

Next you must get seizure_lists.
These files are not available via SFTP, and to the best of our knowledge at Northeastern, the only way to get access to them, is to 
navigate the website and to manually pull them down.

This is extremely painful, so we have automated this process in the FileFerry directory with a selenium script. 
You'll have to enter your username and password in the script, and then you can run it with:

```
python GetSeizureLists.py --username <username> --password <password>
```

This will make a dir of seizurelists locally, and then you can push them up to the server in the right locations with another script:
        
        ```
        pushSeizureListsToServer.py
        ```

For that script you will have to enter your password for each separate SCP, but each file will end up exactly where you need it.

Finally, the website for FR216 seizures in surf30 does not render on the website.
So we extracted the data from the table and stored in as a string in the HandleFR216_surf30.py file and you can push that specific 
file to the server by running that script. (This should be the only data from the epilepsiae dataset you'll find in this repo.)


1. Setup postgreSQL. 

This should be fairly easy. We cloned the repository onto our server and then ran the commands in the makefile:

`make run-postgres`
`make create-db`

This sets up and instantiates a postgres server with the tables defined in epilepsiae_sql_dataloader/models


2. Add metadata to the database

This will add all of the seizure and patient/sample metadata to the database. This way we can quickly query when seizures happened for what patients in what datasets without having to do raw file navigation.

To do this you can run the following command:

```
cd epilepsiae_sql_dataloader
python -m venv venv
source venv/bin/activate
pip install -e .
python -m epilepsiae_sql_dataloader.RelationalRigging.MetaDataBuilder --directories /mnt/external1/raw/inv --drop-tables
python -m epilepsiae_sql_dataloader.RelationalRigging.MetaDataBuilder --directories /mnt/external1/raw/surf30
```

This does the following:
1. Install a python virtual environment
2. Installs the entire repo as a python package
3. Runs the MetaDataBuilder script with the directories specified. This will take a while. It will also drop the tables and recreate them. This is useful if you want to update the metadata.

Notice, you may want to look at the RelationalRiggingMetaDataBuilder.py file to figure out exactly what options you want.


3. Index and partition the database.

If you look in alembic/versions you'll find a variety of migration scripts
Unfortunately, several of the changes described there have already been added to the DB.
To get the DB into a high performance state you will have to write a new alembic script, or a new SQL script that indexes and partitions the DB.

I believe that: alembic/versions/dabdda1fb359_patient_id_partitions_for_data_chunks.py does everything you need except that the data_chunk id 
is a normal int when you will need big ints to work with billions of records.

4. Add the binary data to the database

Assuming you are still in the virtual environment you can run the following command:

```
python epilepsiae_sql_dataloader/RelationalRigging/PushBinaryToSql.py --dir /mnt/external1/raw/inv
```

For right now there is no option to drop the tables, or to add multiple directories.


5. Use the dataloaders.

You can now use the dataloaders in DataDinghy to load data into your ML model.
It is worth noting, as long as the database is set up, you can pip install this package
and use it in your project without having to deal directly with the source code.

The package is not yet on PyPi, but you can install it from github with:

```
git clone git@github.com:dschonholtz/epilepsiae_sql_dataloader.git
cd epilepsiae_sql_dataloader
python -m venv venv
source venv/bin/activate
pip install .
```

Then you can use the dataloaders in DataDinghy to load data into your ML model.
In your python project you can do something like:

```
from epilepsiae_sql_dataloader.DataDinghy import Pytorch
```

Finally, you can also run:

```
python epilepsiae_sql_dataloader/DataDinghy/Stats.py
```

To see stats on every single patient. 
This takes a little while, but it will list out the number of seizures and each type of datachunk.
This is mostly a debugging tool but loading data into the DB, but it can also serve as a framework for writing custom dataloaders
for custom data.
Or for finding proper ratios for things like sigmoid focal loss.

Features
--------

* Build SQL Alchemy Tables that all of the epilepsiae data can be loaded into and be queried from
* Build a dataloader that can be used to load data into a ML model

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage


Adding a new Dataset
----

There are two possible methods. 1. Create a new MetaDataBuilder file, and PushBinaryToSql file for your new dataset that relies on the same underlying
database structure and 2. Convert your data into the same format as the existing datasets and use the existing MetaDataBuilder and PushBinaryToSql files.

Generally, I would strongly recomend method 2.

Method 1: Create a new MetaDataBuilder file, and PushBinaryToSql file for your new dataset that relies on the same underlying
----

To add a new dataset you will have to do the following:
1. In RelationalRigging create a new MetaDataBuilder.py equivilant that will populate your metadata tables.

This will include the dataset, patients, and seizure information.

I would copy the MetaDataBuilder.py file as is and adjust for your file structure.
Then modify the read_sample_data function to read your data into those fields. That function already designates in the code what fields are actually
required:

            "start_ts",
            "num_samples",
            "sample_freq",
            "num_channels",
            "adm_id",
            "rec_id",
            "duration_in_sec",

Most of these are self explanatory and really are required for proper data processing, except for adm_id and rec_id.

Adm_id is not used anywhere currently and can be a static value for every record if you'd like. For our historic data, it is a cluster of recordings
for a specific patient and if you wanted to query for recordingds in this group this column would allow that.

Rec_id is the recording id. This is used to group several hours of consecutive records together. So to calculate seizures with respect to 
where they are in a long recording across many diverse binary samples, this is important.

Finally, there is the data_file column, not listed above as it is added later. This references the path to the raw binary.
It is used to load the binary in the PushBinaryToSql code later. The path must be the absolute path here.

2. In RelationalRigging create a new PushBinaryToSql.py equivilant that will populate your binary tables.

This is fairly complicated and involves pulling electrode labels, and channels and assigning them accordingly.



Method 2: Convert your data into the same format as the existing datasets and use the existing MetaDataBuilder and PushBinaryToSql files.

The existing format is fairly simple:

- DATASET_NAME
|--- PATIENT_ID  # formatted as pat_####
|---|--- seizure_list
|---|--- ADM_ID # formatted as adm_####
|---|---|--- REC_ID # formatted as rec_####
|---|---|---|--- #####_####.data
|---|---|---|--- #####_####.head

Where the seizurelists are formatted like this:

```seizure_list
# list of seizures of patient FR_139
                
# colums are tab-separated: 
# onset offset onset_sample offset_sample
2003-11-19 21:06:03.707031 2003-11-19 21:06:21.605469 542389 546971

2003-11-24 19:23:38.166016 2003-11-24 19:27:03.941406 264277 369634
```

These should be tab delimitted but they are not, and they are assumed to just have spaces between the columns.
You also only need the timestamps, the onset_sample and offset_sample can be dummy values as the values there are never used.

The .head values look like this:

```example.head
start_ts=2008-12-01 19:45:39.000
num_samples=3686400
sample_freq=1024
conversion_factor=0.179000
num_channels=72
elec_names=[HLA1,HLA2,HLA3,HLA4,HLA5,BFLA1,BFLA2,BFLA3,BFLA4,BFLA5,BFLA6,BFLA7,BFLA8,BFLA9,HLB1,HLB2,HLB3,HLB4,HLB5,BFLB1,BFLB2,BFLB3,BFLB4,BFLB5,BFLB6,BFLB7,BFLB8,BFLB9,HLC1,HLC2,HLC3,HLC4,HLC5,TPR1,TPR2,TPR3,TPR4,TPR5,HRA1,HRA2,HRA3,HRA4,HRA5,BFRA1,BFRA2,BFRA3,BFRA4,BFRA5,BFRA6,BFRA7,BFRA8,BFRA9,HRB1,HRB2,HRB3,HRB4,HRB5,HRC1,HRC2,HRC3,HRC4,HRC5,BFRB1,BFRB2,BFRB3,BFRB4,BFRB5,BFRB6,BFRB7,BFRB8,BFRB9,ECG]
pat_id=107302
adm_id=1073102
rec_id=107300102
duration_in_sec=3600
sample_bytes=2
```

You do not need conversion_factor, but everything else is required. Sample_bytes is just the number of bytes the integers are used to represent data in the corresponding .data file.
The electrode names must be included and are used to differentiate ECG, EKG, EEG and IEEG. To learn and modify what is used for what, see process_data_types in PushBinaryToSql.py

Finally, the .data files are just binary files of integers. The integers are the raw data values.
It must be of the shape num_channels x num_samples. The integers are assumed to be 16 bit signed integers, if the sample_bytes is 2.