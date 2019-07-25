import mlcycle
import os

import yaml
import git
import docker
import datetime

print("------------------------------------------------------------------------------------")
print("------------------------------ Step execution started ------------------------------")
print("------------------------------------------------------------------------------------")

print()
print("------------------------------ Initialize Environment ------------------------------")

workdir = os.environ.get('MLCYCLE_WORKDIR')
volname = os.environ.get('MLCYCLE_VOLUME')
runtime = os.environ.get('MLCYCLE_RUNTIME')
visible_gpus = os.environ.get('MLCYCLE_VISIBLE_GPUS')
host = os.environ.get('MLCYCLE_HOST')
jobId = os.environ.get('MLCYCLE_JOB')
stepnr = os.environ.get('MLCYCLE_STEP')

if not workdir:
    raise ValueError("Configuration Error: MLCYCLE_WORKDIR is not set")

if not volname:
    raise ValueError("Configuration Error: MLCYCLE_VOLUME is not set")

if not host:
    raise ValueError("Configuration Error: MLCYCLE_HOST is not set")

if not jobId:
    raise ValueError("MLCYCLE_JOB is not set")

if not stepnr or not stepnr.isdigit():
    raise TypeError("MLCYCLE_STEP is either not set or is not an integer")

stepnr = int(stepnr)

print("Working dir:\t{}".format(workdir))
print("Volume:\t\t{}".format(volname))
print("Runtime:\t{}".format(runtime))
print("Visible GPUS:\t{}".format(visible_gpus))
print("Host:\t\t{}".format(host))
print("Job Id:\t\t{}".format(jobId))
print("Step Nr:\t{}".format(stepnr))

cclient = mlcycle.init_with(host)
dclient = docker.from_env()

print()
print("------------------------------- Load job information -------------------------------")
job = cclient.Jobs.getById(jobId)
if not job:
    raise ValueError("MLCYCLE_JOB is not in environment variables")

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

    volumes = { 
        volname: { 'bind': volume_base, 'mode': 'rw' }
    }

    command = None
    if 'command' in cfg_docker:
        command = cfg_docker['command']

    environment = {
        "MLCYCLE_HOST": os.environ['MLCYCLE_HOST'],
        "MLCYCLE_PROJECT": os.environ['MLCYCLE_PROJECT'],
        "MLCYCLE_JOB": os.environ['MLCYCLE_JOB'],
        "MLCYCLE_STEP": os.environ['MLCYCLE_STEP']
    }

    if visible_gpus:
        environment['NVIDIA_VISIBLE_DEVICES'] = visible_gpus

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
                                       runtime=runtime,
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