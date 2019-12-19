# Software interface to Condor

This repository contains a software interface library to HTCondor job scheduler. This library allows users to submit jobs to HTCondor system from python script running on local system.

Author: Ayan Das

### Requirements:
1. Python package `paramiko` must be installed
2. Must have ssh-ing capability to the Condor login node.

### Setup:

Clone this repo anywhere (e.g. `/path/to/repo`) on the local system and put the following on your `.bashrc` (or whatever shell you use)

```
export PYTHONPATH=${PYTHONPATH}:/path/to/repo
```

### Usage:

Create a python file `<anything>.py` and keep it in the root of your own project.
The following example snippet shows the basic usage of the library:

```
import os
from condor import condor, Job, Configuration

# Provide required configuration of machine
conf = Configuration(request_CPUs=1, request_GPUs=1, gpu_memory_range=[8000,24000], cuda_capability=5.5)

# This is the (example) job to be submitted.
# python classifier.py --base ./ --root ${STORAGE}/datasets/quickdraw --batch_size 64 --n_classes 3 --epochs 5 --tag clsc3f7g10 --modelname clsc3f7g10

with condor() as sess:
    # open a session to condor login node

    for bs in [8, 16, 32, 64]: # submit a bunch of jobs
        j = Job('python', 'classifier.py',
            arguments=dict(
                base=os.getcwd(), root=os.environ['STORAGE'] + '/datasets/quickdraw',
                batch_size=bs, # Here's the variable 'bs'
                n_classes=3, epochs=30,
                tag='clsc3f7g10', modelname='clsc3f7g10'
            ))

        # finally submit it
        sess.submit(j, conf)
```

Note: You may have to type password (in case you don't have private keys set up)