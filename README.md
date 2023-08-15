# Master-Thesis-RJ
 A Federated Computational Workflow for Analysis of DISKOS Digital  Palynological Slides

# Setting up

It is assumed you have docker installed in your pc and running.

In a terminal (this project was done in Linux OS) run each of the following commands.

## Set up virtual env


1. Create the virtual environment (if you haven't done it already):
   python -m venv thesis


2.Activate the virtual environment
  source thesis/bin/activate

3.Install the dependencies from the requirements.txt file
  
  pip install -r requirements.txt


## Set up of Airflow

You must be in the virtual env created (thesis)

1. Run the following command.
  
  airflow db init

You must receive a message saying "Initialization done"

2. Run the following command.

   airflow webserver

The webserver should be open in this url (http://localhost:8081/home) you should login with username and password as "admin" both. This keep running in that terminal so you must open a new terminal to run the next command.Activate virtual env.

2. Run the following command.

   airflow scheduler

The scheduler keep running in that terminal, so open a new terminal to keep going with the set up process. Activate virtual env.


## Set up of Dash

Navigate to the folder Thesis in the terminal with the virtual env activated.

1.Run the following command
 python app2.py

You have to open the app here ( http://127.0.0.1:8050/ ) or the url shows up in the terminal, depends on your localhost config.


# Running a process with the app

Read thesis document.









