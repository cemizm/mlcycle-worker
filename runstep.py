import contiflow
import os

import logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)

os.environ['GIT_PYTHON_TRACE'] = "full"

from git import Repo

client = contiflow.init()

print("------------------------------------------------------------------------------------ ")
print("------------------------------ Step execution started ------------------------------ ")
print("------------------------------------------------------------------------------------ ")

print()
print("Loading environment...")
workdir = os.environ['CONTIFLOW_WORKDIR']
if not workdir:
    raise ValueError("CONTIFLOW_WORKDIR is not valid path")

jobId = os.environ['CONTIFLOW_JOB']
if not jobId:
    raise ValueError("CONTIFLOW_JOB is not set")

stepnr = os.environ['CONTIFLOW_STEP']
if not stepnr.isdigit():
    raise TypeError("CONTIFLOW_STEP is not an integer")

stepnr = int(stepnr)
print("Working dir:\t{}".format(workdir))
print("Job Id:\t\t{}".format(jobId))
print("Step Nr:\t{}".format(stepnr))

print()
print("Loading job information...")
job = client.Jobs.getById(jobId)
if not job:
    raise ValueError("CONTIFLOW_JOB is not in environment variables")

step = next((s for s in job['steps'] if s['number'] == stepnr), None)
if not step:
    raise ValueError("Step number is not in environment variables")

print("Project:\t{}".format(job['project']['name']))
print("Repository:\t{}".format(job['project']['gitRepository']))
print("Step:\t\t{}. {}".format(step['number'], step['name']))

print()
print("Cloning git repository...")

rep_url = job['project']['gitRepository']
rep_path = os.path.join(workdir, "repo")

rep = Repo.clone_from(rep_url, rep_path, depth=1)

print()
print("Loading pipeline configuration...")
cfg = os.path.join(rep_path, "pipeline.yml")
if not os.path.exists(cfg):
    raise FileNotFoundError(cfg)