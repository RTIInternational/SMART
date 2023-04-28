SMART User Docs
===============

SMART is an open source application designed to help data scientists and research teams efficiently build labeled training datasets for supervised machine learning tasks.

Feature Highlights
^^^^^^^^^^^^^^^^^^

* **Active Learning** algorithms for selecting the next batch of data to label.
* **Label Suggestions** to suggest likely labels for each data item, using embeddings.
* **Inter-rater reliability** metrics to help determine a human-level baseline and the understand the test validity of your labeling task.
* **Admin dashboard** and other project management tools to help oversee the labeling process and coder progress.
* **Multi-user coding**, for parallel annotation efforts within a project.
* **Self-hosted installation**, to keep sensitive data secure within your organization’s firewall.

Quick Start
^^^^^^^^^^^
::

	$ git clone https://github.com/RTIInternational/SMART.git
	$ cd smart/envs/dev/
	$ docker-compose build
	$ docker volume create --name=vol_smart_pgdata
	$ docker volume create --name=vol_smart_data
	$ docker-compose run --rm backend ./migrate.sh
	$ docker-compose up -d

Open your browser to http://localhost:8000

.. _user-docs:

.. toctree::
   :maxdepth: 1
   :caption: Tutorial

   tutorial-installation
   tutorial-new-project
   tutorial-review-projects
   tutorial-annotate
   tutorial-admin-dash
   tutorial-download

.. toctree::
   :maxdepth: 2
   :caption: Advanced Features

   features

.. _about-docs:

.. toctree::
	:maxdepth: 2
	:caption: About SMART

	faq
	release-changelog
	license

