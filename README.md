# Software interface to Condor

This repository contains a software interface library to HTCondor job scheduler. This library allows users to submit jobs to HTCondor system from python script running on local system.

Author: Ayan Das

### Requirements:
1. Python package `paramiko` must be installed
2. Must have ssh-ing capability to the Condor login node.

### Setup:

Clone this repository anywhere (e.g. `<local/path/to/repo>`):

```
git clone https://github.com/dasayan05/condor.git <local/path/to/repo>
```

1. Install it with

```
cd local/path/to/repo
python setup.py install
```

OR

2. Put the following on your `.bashrc` (or whatever shell you use)

```
export PYTHONPATH=${PYTHONPATH}:local/path/to/repo
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

with condor('condor') as sess:
    # Open a session to condor login node with hostname 'condor'.
    # Set up password-less ssh, otherwise it will ask for password
    # everytime this 'with .. as' block is encountered.

    for bs in [8, 16, 32, 64]: # submit a bunch of jobs
        
        # It will autodetect the full path of your python executable
        j = Job('python', 'classifier.py',
            # all arguments to the executable should be in the dictionary as follows.
            # an entry 'epochs=30' in the dict will appear as 'python <file>.py --epochs 30'
            arguments=dict(
                base=os.getcwd(),
                root=os.environ['STORAGE'] + '/datasets/quickdraw',
                batch_size=bs, # Here's the looped variable 'bs'
                n_classes=3,
                epochs=30,
                tag='clsc3f7g10',
                modelname='clsc3f7g10'
            )
        )

        # finally submit it
        sess.submit(j, conf)
```

NOTE: It is recommended that you [set up password-less SSH](https://askubuntu.com/a/46935) to your condor login node. You may have to type password way too many times in case you don't.