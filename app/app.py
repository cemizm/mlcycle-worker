import time
import mlcycle

import subprocess, os, shutil

from .taskitem import TaskItem, TaskState

# Initialize and check environment variable

workdir = os.environ.get('MLCYCLE_WORKDIR')
volname = os.environ.get('MLCYCLE_VOLUME')
runtime = os.environ.get('MLCYCLE_RUNTIME')
host = os.environ.get('MLCYCLE_HOST')

if not workdir:
    raise ValueError("Configuration Error: MLCYCLE_WORKDIR is not set")

if not volname:
    raise ValueError("Configuration Error: MLCYCLE_VOLUME is not set")

if not host:
    raise ValueError("Configuration Error: MLCYCLE_HOST is not set")

print("------------------------------- Initialize Environment ------------------------------")
print("Working dir:\t{}".format(workdir))
print("Volume:\t\t{}".format(volname))
print("Runtime:\t{}".format(runtime))
print("Host:\t\t{}".format(host))

print()
print("------------------------------------ Start worker -----------------------------------")

client = mlcycle.init_with(host)
jobs = list()

def run():
    while True:

        while len(jobs) > 0:
            job = jobs[0]

            print('job: {} - TaskState: {}'.format(job.getJobId(), job.state))

            if job.retries > 3:
                removeJob(job)
            elif job.state == TaskState.Claim:
                claimStep(job)
            elif job.state == TaskState.Work:
                runStep(job)
            elif job.state == TaskState.Upload:
                uploadFile(job)
            elif job.state == TaskState.Complete:
                completeJob(job)
            elif job.state == TaskState.Remove:
                removeJob(job)

        print("waiting for new jobs...")
        resp = client.Scheduler.getPending()
        if not resp:
            time.sleep(5)
            continue

        for job in resp:
            initJob(TaskItem(job))

        print('{} new job(s) queued'.format(len(resp)))

def initJob(job):
    jobId = job.getJobId()

    job.working_dir = os.path.join(workdir, jobId)    
    if not os.path.exists(job.working_dir):
        os.makedirs(job.working_dir)

    jobs.append(job)


def claimStep(job):
    jobId = job.getJobId()
    step = job.getStepNumber()

    if not client.Scheduler.claim(jobId, step):
        job.state = TaskState.Remove
    else:
        job.state = TaskState.Work

def runStep(job):
    env = os.environ.copy()
    env['MLCYCLE_PROJECT'] = str(job.getProjectId())
    env['MLCYCLE_JOB'] = str(job.getJobId())
    env['MLCYCLE_STEP'] = str(job.getStepNumber())
    env['MLCYCLE_WORKDIR'] = job.working_dir
    
    job.logfile = os.path.join(job.working_dir, "console.log")

    retCode = -1
    with open(job.logfile, "w") as f:
        retCode = subprocess.call(['python', 'runstep.py'], stdout=f, stderr=f, env=env)

    job.error = retCode != 0
    job.state = TaskState.Upload

def uploadFile(job):
    if not job.logfile:
        job.state = TaskState.Complete
        return
    
    job.retriesInc()

    jobId = job.getJobId()
    step = job.getStepNumber()

    fragment = {
        'name': 'Console Log',
        'filename':  str(job.getStepNumber()) + '_console.log',
        'type': 1
    }

    res = False
    with open(job.logfile, "r") as f:
        res = client.Fragments.upload(jobId, step, fragment, f)

    if res:
        job.retriesReset()
        job.state = TaskState.Complete

def completeJob(job):
    jobId = job.getJobId()
    step = job.getStepNumber()

    job.retriesInc()

    res = None
    if job.error:
        res = client.Scheduler.error(jobId, step)
    else:
        res = client.Scheduler.complete(jobId, step)

    if res:
        job.retriesReset()
        job.state = TaskState.Remove

def removeJob(job):
    if job.state in (TaskState.Complete, TaskState.Remove):
        jobs.remove(job)
        shutil.rmtree(job.working_dir, ignore_errors=True)
    else:
        job.state = TaskState.Complete
        job.error = True
        job.retriesReset()