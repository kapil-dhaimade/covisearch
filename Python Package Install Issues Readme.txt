
# Pip Upgrade Issue: If pip is on older version like 10.x, then some Python dependencies may fail to install. It requests that we upgrade pip using 'pip install --upgrade pip' command. But the command also fails from inside Pycharm terminal in virtual env. To solve this, there is a PY file which you need to run from your project's root folder in Pycharm's terminal. This PY file, kept here as 'pip-upgrade.py' file upgrades pip successfully. 
-Sources:
	-SO: Python 3.7 - PIP upgrade error on windows 10:
	https://stackoverflow.com/questions/53764054/python-3-7-pip-upgrade-error-on-windows-10
	
	
# Google Cloud Package Install Issue / Pycharm lock on setuptools egg file issue: Google Cloud packages like Firestore, API Core won't install. Reason is that these packages updates the setuptools egg file in venv and Pycharm keeps lock on that file.  This is a bug in Pycharm. Fix: Close Pycharm, go to project's venv, open Powershell from there, run activate.ps1 present in venv, then install the Google Cloud packages, then re-open Pycharm.
-Sources:
	-Jetbrains Pycharm Trac: Pycharm does not release lock on setuptools egg (see ans by Amir Katz, 2 Oct 2019):
	https://youtrack.jetbrains.com/issue/PY-38096