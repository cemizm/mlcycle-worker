# MLCycle Worker

The worker of the MLCycle platform can be run as a docker container using the `cemizm\mlcycle_worker` image from docker hub. For each MLCycle task, the worker spawns a container with the image defined in the pipeline.

## Requirements
* Docker > 19.03
* [Nvidia Docker runtime](https://github.com/NVIDIA/nvidia-docker/wiki/Installation-(Native-GPU-Support)) > 2.X

## Quick start
The following command runs the MLCycle Worker with default options. Please replace `{host}` with the full URL to the MLCycle backend. See the section below for detailed description of all possible options.

```bash
docker run -d --name worker1 --restart always \
-e MLCYCLE_HOST=https://{host}/api \
-v workdir:/tmp/mlcycle \
-v /var/run/docker.sock:/var/run/docker.sock \
cemizm/mlcycle_worker:latest
```

## Options
The configuration of the worker can be modified by setting the environment variables of the container. This section describes all possible options of the worker.

### Host
The option `host` is required and has to point to the backend server of MLCycle.
```bash
-e MLCYCLE_HOST={url}
```

### Working Directory Volume
The working directory is used to share the project folder with the newly spawned container. The default volume name is `worker_workdir`.
```bash
-e MLCYCLE_VOLUME={volume}
```

### Docker nvidia runtime 
This option controls the used docker runtime for the spawned containers. The default option is set to `nvidia`. If set to empty string no runtime will be used.
```bash
-e MLCYCLE_RUNTIME={runtime}
```

### Visible GPUs
Defines the gpus visible to the spawned containers. Default is set to all available gpus. For more information see the [nvidia plugin](https://github.com/NVIDIA/nvidia-docker/wiki/Installation-(Native-GPU-Support)#usage).
```bash
-e MLCYCLE_VISIBLE_GPUS={gpus}
```

## Private git repositories
If the worker needs to pull projects from a private git repository, it is required to mount the ssh keys for the git repository to the `/root/.ssh` folder of the container. 