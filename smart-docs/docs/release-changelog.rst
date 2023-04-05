Release Notes and Change Log
============================

Release v.1.0.0
****************

Release v.2.0.1
****************

This version has no changes from the initial functionality of SMART, but makes the following maintenance updates:

Changes from 1.0.0
******************

* Upgrades frontend and backend packages to maintain usability and patch potential security issues found in older package versions. NOTE: several packages had not been maintained, and so had to be removed. The most notable is the package responsible for the loading bar which appears when the user is loading large data files into the software.
* Adds in pre-commit hooks and automated formatting options to make the code cleaner and more readable
* Replaces the default data from sentiment data challenge with new cleaner dataset
* *Bug fix*: deck of cards for labeling will not duplicate itself if someone flips through tabs during annotation
* *Bug fix*: admin charts now automatically resize to fit window when tab changes (this initially was true and then later broke)
* *Bug fix*: IRR admin table search bar now functions for filtering the first coder field

Release v.3.0.0
***************

This version has a ton of updates from the previous version, as it's the culmination of about a year's worth of development and user testing. Most of these are quality-of-life improvements or bug fixes, 
with a few new features thrown in. Specifically SMART now better supports those projects which just intend to use SMART as a labeling platform and do not intend to use the model features, something which we've discovered is a fairly common ask.

.. warning:: 
  This version has a lot of new features, some of which were added recently. We will try and post new updates regularly as new bugs are found and fixed.

Changes from 2.0.1
******************

**New Features**

* Metadata fields can now be provided with data and options have been added for deduplication based on this (see "Metadata [NEW]"[TODO link])
* A database connection can now be set up for ingesting new data and exporting labeled data. Currently only supports Microsoft SQL Server (MSSQL) databases [TODO verify and link]
* Labels can now be loaded in from files during project creation (see :ref:`create-new-project`)
* Projects can not be added to Groups which mainly just affects the project page (see "Project Grouping [NEW]")
* For projects with more than 5 labels, the top 5 most likely labels are now provided when annotating using label embeddings (see "Most Likely Label Prediction [NEW]")
* The production build has been updated to be more functional (see "Production Settings [NEW]")
* The history table is now searchable and project admin can see and edit the historic labels of all coders
* The history table can now be filtered by either text or metadata fields, and is paginated by 100 result batches.
* Unlabeled data can now be viewed in the history table for projects that do not use IRR.
* The skew page is now searchable more directly and returns the top 50 items
* Project admin can now un-assign coders on the admin page, to free up items for other coders to label. 
* There is now a timeout in affect for the lock on the admin tables. If an admin has not done anything in the last 15 minutes in a project, and another admin requests the project page, the lock will be given to the new admin. 
* The project page now lists counts for the data left to code. This excludes items in the recycle bin.
* The details page now provides counts for the data in the project and where the data is in the coding or IRR pipeline.
* The Skip button has been changed so it merely un-assigns the card to be labeled later. Instead, there is a separate "Adjudicate" button which has the old skip functionality of sending the card to the Admin table. This button now also requires a reason for sending to the Admin.


**Removed Features**

* The progress bar on the coding page has been removed due to both the underlying package not being supported, and the fact that due to how SMART assigns data, it was not terribly useful. 

**Bug Fixes**

* The email functionality has been fixed so that users who set an email for their account can use this email to reset their password.
  * NOTE: Please check spam and quarantine folders if unable to find the emails.
  * NOTE: by default the password reset emails will say they are from "example.com." This can be changed in a deployed SMART instance through the Django admin interface `see instructions here <https://stackoverflow.com/questions/11372064/django-registration-how-do-i-change-example-com-in-the-email>`_
* The annotate page can now refill itself when there are no cards assigned, instead of relying on other processes like the model build to call a refill. This helps in cases where those other processes fail to refill the queue for some reason.
* The leave-coding-page functionality has been fixed for Chrome, after a recent update disabled it. When broken, Chrome users signing out of SMART would not free up admin tables or un-assign their cards for other users. 
* Many small frontend bugs to do with getting long content to render properly have been fixed
* A button was added to the project create Codebook page to help with removing an uploaded codebook file
* The project permissions page has been updated to prevent duplicate or conflicting permission assignments
* The IRR queue now is filled proportionally to how much the non-IRR queue is filled in cases where IRR is not 100% or 0%. Previous to this fix the IRR queue would always add batch size x percent IRR new items to itself each time fill_queue was called even if no items were added to the normal queue, causing the number of items classified as IRR to be far larger than the expected proportion.
* Broken tests have been fixed

**Other Changes**

* We are now using pip-tools for backend feature building and maintenance. See the project README section "Dependency management in Python" for instructions on upgrading packages.
* The timezone for frontend-facing date/time output like downloaded labeled data now defaults to EST (see the project README section "Timezones" for instructions for changing the default timezone for the frontend.)
* An empty Label column is no longer required for uploaded data with no labels
* Various charts in SMART have been updated to make them more practical for projects with many labels
* The defaults in the Advanced Project Settings page have been updated:
    * Batch size defaults to 30 instead of the number of labels times 10 
    * By default the model and active learning are turned off and have to be enabled
    * IRR is disabled by default and must be enabled
* The steps on the project creation page have been re-arranged so Advanced Settings is last
* The annotate page has been updated to make things more readable and work with the new Metadata options. In addition projects with many labels will see them appear in a dropdown instead of as individual buttons.
* Frontend dependencies have been updated so that they pull in new bug fix versions.
* Messages for admin lockout or when there are no cards to assign have been updated for clarity.
* Some small GUI changes were made based on feedback from a UX designer

Contributors
************

* Durk Steed
* Peter Baumgartner
* Rob Chew
* Emily Hadley
* Caroline Kery
* Lucy Liu
* Joey Morris
* Jason Nance
* Keith Richards
* Michael Wenger
* Souliya Chittarath
* Alex Harding