'''
A software interface to Condor, written in Python.
Author: Ayan Das

Copyright (c) 2019-2020 Ayan Das

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to
do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

try:
   # 'Paramiko' is the software-ssh library used in
   # eshtablishing connection to 'HTCondor' system.
   # It is a mandatory dependency. So, get it.
   import paramiko as pmk
except ImportError:
   print("Can\'t import paramiko. If not installed, install it with \'pip install paramiko\'.")

# standard library imports
import getpass, os, tempfile

class Job(object):
   
   # Some pre-defined flags
   IF_NEEDED = 'IF_NEEDED'
   YES = 'YES'
   NO = 'NO'
   ON_EXIT = 'ON_EXIT'
   ON_EXIT_OR_EVICT = 'ON_EXIT_OR_EVICT'

   def __init__(self,
         executable = None, # The executable to run. E.g.: 'bash', 'python' etc.
         program_file = None, # The file to run. If 'None', it is basically a command invocation
         should_transfer_files = 'IF_NEEDED',
         when_to_transfer_output = 'ON_EXIT',
         stream_output = True,
         tag=None,
         *,
         arguments = dict(), # Arguments. dict(p=4, gpu=None)
         pos_arguments = [],
      ):

      # Track parameters
      assert should_transfer_files in [Job.IF_NEEDED, Job.YES, Job.NO], 'Illegal value for "should_transfer_files"'
      self.should_transfer_files = should_transfer_files
      assert when_to_transfer_output in [Job.ON_EXIT, Job.ON_EXIT_OR_EVICT], 'Illegal value for "when_to_transfer_output"'
      self.when_to_transfer_output = when_to_transfer_output
      self.stream_output = 'True' if bool(stream_output) else 'False'
      self.tag = '$(cluster).$(process)' if tag is None else str(tag)
      self.executable = executable if os.path.isabs(executable) \
                                 else os.popen(f'which {executable}').read()[:-1]
      if program_file != None:
         self.program_file = program_file if os.path.isabs(program_file) \
                                        else os.path.abspath(program_file)
      else:
         self.program_file = '' # Empty string helps constructing the full command
      
      if isinstance(pos_arguments, str):
         self.pos_arguments = pos_arguments
      else:
         # construct the position argument sub-string from the list
         pos_arglist = [str(a) for a in pos_arguments]
         self.pos_arguments = ' '.join(pos_arglist)

      if isinstance(arguments, str):
         self.arguments = arguments
      else:
         # construct the argument line from dict. e.g. '-p3 -q1 --gpu --batch 32'
         arglist = [ '-' + str(k) + str(v) if len(k) == 1 \
                else '--' + str(k) + ' ' + str(v)
                for k, v in arguments.items() ]
         self.arguments = ' '.join(arglist)

      # construct full argument string
      self.arguments = ' '.join([self.program_file, self.pos_arguments, self.arguments])

   def get_attributes(self):
      return [
         f'executable = {self.executable}',
         f'arguments = {self.arguments}',
         
         f'should_transfer_files = {self.should_transfer_files}',
         f'when_to_transfer_output = {self.when_to_transfer_output}',
         f'stream_output = {self.stream_output}',

         # logging files
         f'log = {self.tag}.log',
         f'error = {self.tag}.err',
         f'output = {self.tag}.out'
      ]

class Configuration(object):
   def __init__(self, *,
         request_CPUs = 1, # No. of CPUs required
         request_GPUs = 0, # No. of GPUs required
         request_memory = 4096, # Amount of RAM required
         has_storenext = True,
         gpu_memory_range = [0, 24000],
         cuda_capability = 2.0,
         no_priority = True
      ):
      
      # Track the parameters
      self.request_CPUs = request_CPUs
      self.request_GPUs = request_GPUs
      self.request_memory = request_memory
      self.has_storenext = has_storenext
      self.gpu_memory_min = gpu_memory_range[0] # separate these ..
      self.gpu_memory_max = gpu_memory_range[1] # .. two parameters
      self.cuda_capability = cuda_capability
      self.no_priority = no_priority # do not allocate priority machine

   def get_attributes(self):
      requirements = [
         # Requirement list separated by '&&' in 'requirement' attribute
         f'(HasStornext)'                                if self.has_storenext     else None,
         f'(CUDAGlobalMemoryMb > {self.gpu_memory_min})' if self.request_GPUs != 0 else None,
         f'(CUDAGlobalMemoryMb < {self.gpu_memory_max})' if self.request_GPUs != 0 else None,
         f'(CUDACapability > {self.cuda_capability})'    if self.request_GPUs != 0 else None,
         f'(NotProjectOwned)'                            if self.no_priority       else None
      ]
      requirements = ' && '.join([r for r in requirements if r != None])
      
      return [
         f'request_CPUs = {self.request_CPUs}',
         f'request_GPUs = {self.request_GPUs}',
         f'request_memory = {self.request_memory}',
         f'requirements = {requirements}'
      ]

def env_string(env_list):
   # Gets a list of ENV vars; expands them and creates the
   # 'environment = * entry for the condor submit script
   if len(env_list) == 0:
      return ''
   else:
      joined_envs = ' '.join([f'{e}={os.environ[e]}' for e in env_list])
      return f'environment = \"{joined_envs}\"'

class condor(object):
   def __init__(self,
         master_hostname = 'condor', # The old one was 'cvssp-condor-master'
         username = None,
         export_envs = [],

         # All keys inside options are optional
         # 'options.known_hosts' contain the filepath for unconventional 'known_hosts' file
         options = dict()
      ):
      
      # Track the parameters
      self.master_hostname = master_hostname
      self.username = getpass.getuser() if (username == None) else username
      self.envs = env_string(export_envs)
      self.options = options

      # The central 'client' object
      self.client = pmk.SSHClient()

      # Load system hostkeys and set policy for unknown servers
      self.client.load_system_host_keys(filename = None if 'known_hosts' not in self.options else self.options['known_hosts'])
      self.client.set_missing_host_key_policy(pmk.AutoAddPolicy()) # add automatically if not known

   def __enter__(self):
      try:
         self.client.connect(hostname=self.master_hostname,
                             username=self.username,
                             # first try with private-key (password-less ssh), if found of given
                             pkey=None if 'pkey' not in self.options else self.options['pkey'])
      except pmk.AuthenticationException:
         print('No valid public-private key found. Setting up password-less ssh is recommended.')
         print('Trying with password ...')
         try:
            self.client.connect(hostname=self.master_hostname,
                                username=self.username,
                                pkey=None,
                                password=getpass.getpass(f'Password for {self.username}@{self.master_hostname}:'))
         except pmk.AuthenticationException:
            print('Password didn\'t work either.')

      return self
   
   def __exit__(self, exc_type, exc_value, exc_traceback):
      self.client.close()

   def execute(self, command):
      _, out, err = self.client.exec_command(command, get_pty=True)
      out, err = out.readlines(), err.readlines()

      if len(err) == 0:
         for line in out:
            print(line, end='')
      else:
         for line in err:
            print(line, end='')

   def submit(self, job, config, keep_condor_file=False, dry_run=False):
      # full attributes list (job and system configurations)
      attributes = [
         '## HTCondor submit file',
         '#######################',

         '# Job configurations',
         self.envs,
         *job.get_attributes(),

         '# System configurations',
         *config.get_attributes(),

         '# Queueing',
         'queue'
      ]

      with open(tempfile.mktemp(suffix='.submit_file', prefix='condor', dir='.'), 'w') as submitfile:
         for attr in attributes:
            submitfile.write(attr + '\n')

         # get the full filename
         submit_filename = os.path.abspath(submitfile.name)

      pwd = os.path.abspath('.')
      if not dry_run:
         self.execute(f'cd {pwd}; condor_submit {submit_filename}')

      keep_condor_file = keep_condor_file or dry_run
      if not keep_condor_file:
         os.remove(submit_filename)