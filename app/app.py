import time
import contiflow

import subprocess, os, shutil

from .taskitem import TaskItem, TaskState

if 'CONTIFLOW_WORKDIR' not in os.environ:
    raise BaseException("contiflow workingdir not set")

workdir = os.environ['CONTIFLOW_WORKDIR']
if not os.path.exists(workdir):
    os.makedirs(workdir)

client = contiflow.from_env()

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
    env['CONTIFLOW_PROJECT'] = str(job.getProjectId())
    env['CONTIFLOW_JOB'] = str(job.getJobId())
    env['CONTIFLOW_STEP'] = str(job.getStepNumber())
    env['CONTIFLOW_WORKDIR'] = job.working_dir
    
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