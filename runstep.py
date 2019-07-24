import contiflow
import os

import yaml
import git
import docker
import datetime

cclient = contiflow.from_env()
dclient = docker.from_env()

print("------------------------------------------------------------------------------------")
print("------------------------------ Step execution started ------------------------------")
print("------------------------------------------------------------------------------------")

print()
print("------------------------------- Initialize Environment------------------------------")
workdir = os.environ['CONTIFLOW_WORKDIR']

jobId = os.environ['CONTIFLOW_JOB']

stepnr = os.environ['CONTIFLOW_STEP']
if not stepnr.isdigit():
    raise TypeError("CONTIFLOW_STEP is not an integer")

volname = os.environ['CONTIFLOW_VOLUME']

stepnr = int(stepnr)
print("Working dir:\t{}".format(workdir))
print("Job Id:\t\t{}".format(jobId))
print("Step Nr:\t{}".format(stepnr))

print()
print("------------------------------- Load job information -------------------------------")
job = cclient.Jobs.getById(jobId)
if not job:
    raise ValueError("CONTIFLOW_JOB is not in environment variables")

step = next((s for s in job['steps'] if s['number'] == stepnr), None)
if not step:
    raise ValueError("Step number is not in environment variables")

print("Project:\t{}".format(job['project']['name']))
print("Repository:\t{}".format(job['project']['gitRepository']))
print("Step:\t\t{}. {}".format(step['number'], step['name']))


print()
print("-------------------------------- Clone git repository ------------------------------")
rep_url = job['project']['gitRepository']
rep_path = os.path.join(workdir, "repo")

rep = git.Repo.clone_from(rep_url, rep_path, depth=1)

head = rep.head.commit
date = datetime.datetime.fromtimestamp(head.committed_date)

print('Head:\t\t{}'.format(head.hexsha))
print('Date:\t\t{}'.format(date))
print('Author:\t\t{}'.format(head.committer.name))
print('Commit:\t\t{}'.format(head.message))

if step['number'] == 0:
    print()
    print("--------------------------------- Bootstrap Pipeline -------------------------------")
    cfg_path = os.path.join(rep_path, "pipeline.yml")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(cfg_path)

    cfg = None
    with open(cfg_path, 'r') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    if not cfg:
        raise NotImplementedError("invalid yaml file")

    if 'steps' not in cfg:
        raise ValueError("steps not defined in pipeline.yml")
    
    cfg_steps = cfg['steps']

    if len(cfg_steps) == 0:
        raise ValueError("no steps in pipeline.yml defined")

    if not cclient.Jobs.addSteps(jobId, cfg_steps):
        raise AssertionError("Steps could not be added")

    for s in cfg_steps:
        print("Step added:\t{}".format(s['name']))

    print()
    print("Total:\t\t{}".format(len(cfg_steps)))

else:
    cfg_docker = step['docker']

    volume_base = "/app"
    volume_workdir = os.path.join(volume_base, jobId, "repo")

    volumes = { volname: { 'bind': volume_base, 'mode': 'rw' }}

    command = None
    if 'command' in cfg_docker:
        command = cfg_docker['command']

    environment = {
        "CONTIFLOW_HOST": os.environ['CONTIFLOW_HOST'],
        "CONTIFLOW_PROJECT": os.environ['CONTIFLOW_PROJECT'],
        "CONTIFLOW_JOB": os.environ['CONTIFLOW_JOB'],
        "CONTIFLOW_STEP": os.environ['CONTIFLOW_STEP']
    }

    image = None
    if 'image' in cfg_docker:
        image = cfg_docker['image']
    elif 'buildConfiguration' in cfg_docker:
        print()
        print("------------------------------------- Build Image ----------------------------------")
        cfg_build = cfg_docker['buildConfiguration']

        build_context = rep_path
        if 'context' in cfg_build:
            build_context = os.path.join(build_context, cfg_build['context'])

        build_file = cfg_build['dockerfile']

        build_tag = job['project']['name'] + "/" + step['name']

        dimage, logs = dclient.images.build(path=build_context,
                                            rm=True,
                                            forcerm=True,
                                            dockerfile=build_file)

        for l in logs:
            if 'stream' in l:
                print(l['stream'], end='')

        image = dimage.id
        
    if image is None:
        raise ValueError("Neither an image nor a build configuration is configured")

    print()
    print("------------------------------------ Run Container ---------------------------------")

    print("Image:\t\t{}".format(image))
    print("Command:\t{}".format(command))
    print()


    container = dclient.containers.run(image, 
                                       command=command,
                                       detach=True,
                                       auto_remove=True, 
                                       environment=environment,
                                       volumes=volumes, 
                                       working_dir=volume_workdir)

    for line in container.logs(stream=True):
        print(line.decode('utf-8'), end='')

    result = container.wait()
    if result['StatusCode'] != 0:
        exit(result['StatusCode'])

print()
print("------------------------------------------------------------------------------------")
print("------------------------------ Step execution finished -----------------------------")
print("------------------------------------------------------------------------------------")