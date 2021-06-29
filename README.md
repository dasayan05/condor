# Software interface to Condor

This repository contains a software interface library to HTCondor job scheduler. This library allows users to submit jobs to HTCondor system from python script running on local system.

Author: Ayan Das

### Requirements:
1. Python package `paramiko` must be installed
2. Must have ssh-ing capability to the Condor login node.

### Setup:

1. Install the git repo as `pip` package

```bash
pip install git+https://github.com/dasayan05/condor.git
```

OR

2. Clone this repository anywhere (e.g. `<local/path/to/repo>`):

```bash
git clone https://github.com/dasayan05/condor.git <local/path/to/repo>
```

.. then put the following on your `.bashrc` (or whatever shell you use)

```bash
export PYTHONPATH=${PYTHONPATH}:<local/path/to/repo>
```

OR

3. Build and Install it manually with

```bash
cd <local/path/to/repo>
python setup.py install
```

### Usage:

Create a python file `<anything>.py` and keep it in the root of your own project.
The following example snippet shows the basic usage of the library:

```bash
import os
from condor import condor, Job, Configuration

# Provide required configuration of machine
conf = Configuration(universe='docker', # OR 'vanilla'
    # full container tag from DockerHub or 'registry.eps.surrey.ac.uk'
    docker_image='pytorch/pytorch:1.7.0-cuda11.0-cudnn8-runtime',
    # any extra folder to mount in docker; project space will be auto mounted :)
    extra_mounts=['/vol/vssp'],
    request_CPUs=1,
    request_GPUs=1,
    gpu_memory_range=[8000,24000],
    cuda_capability=5.5)

# This is the (example) job to be submitted.
# python classifier.py --base ./ --root ${STORAGE}/datasets/quickdraw --batch_size 64 --n_classes 3 --epochs 5 --modelname clsc3f7g10

with condor('condor', project_space='myProject') as sess:
    # Open a session to condor login node with hostname 'condor'.
    # Set up password-less ssh, otherwise it will ask for password
    # everytime this 'with .. as' block is encountered.
    # Also, provide the name of your projec space folder. It is required.

    for bs in [8, 16, 32, 64]: # submit a bunch of jobs

        tag = f'MyAwesomeJob_batch_{bs}'

        # It will autodetect the full path of your python executable
        j = Job('/opt/conda/bin/python', # if docker, use absolute path to specify executables inside container
            'classifier.py',
            # all arguments to the executable should be in the dictionary as follows.
            # an entry 'epochs=30' in the dict will appear as 'python <file>.py --epochs 30'
            arguments=dict(
                base=os.getcwd(),
                root=os.environ['STORAGE'] + '/datasets/quickdraw',
                batch_size=bs, # Here's the looped variable 'bs'
                n_classes=3,
                epochs=30,
                modelname='clsc3f7g10'
            ),
            # some extra arguments for Job()
            can_checkpoint=True,
            approx_runtime=2, # in hours
            tag=tag, # give a cool name
            # puts all log files inside this directory (will be created if doesn't exists)
            # for job specific directory use job-specific parameters to create the path;
            # otherwise, use a job-agnostic directory e.g. './junk'
            artifact_dir=f'./junk/{tag}'
        )

        # finally submit it
        sess.submit(j, conf)
```

NOTE: It is recommended that you [set up password-less SSH](https://askubuntu.com/a/46935) to your condor login node. You may have to type password way too many times in case you don't.
