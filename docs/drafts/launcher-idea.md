# Design notes for a more general launcher
Mon Nov 23 04:59:06 PM UTC 2026

## Verdict so far: 
The launcher is not the key focus at this moment. We can use custom launchers
for specific purpose and slowly extracting the features. 

Additionally, for individual programs, we can totally setup program launchers,
or wrap the program into a universal launcher for now. 

## Purpose of the Launcher
- Launch, monitor and terminate a program out in a host with optional hpc
  resource (slurm, qsub), containerization (podman)
- make it possible for processes launched in different systems communicate with
  each other even if they are not directly reachable to each other. (this might
  be extracted into a separate thing)

## Behavior
Concrete behavior: Controller, deployment launcher, application launcher, and
the program code are separate scripts connected through message passing. 

- User starts the controller, with the full configurations of the deployment
  launchers and the program. 
- For each deployment launcher, it needs to check that the environment has the
  sufficient dependencies, it has the necessary resources to run
- Communication between the outer launcher (OL) and inner launcher (IL) is done
  through message passing. Specifically, when the outer launcher launches the
  inner launcher, it has direct access to its stdout and stderr, from which OL
  can monitor and detect events from IL. IL therefore must present the correct
  log and event messages to the OL.  
  - [ ] Define event schema
- Application launcher is the last launcher that directly launch individual
  applications. Interface with each program must therefore be specifically
  defined.
  This is not necessary [could be a design decision here]: if the program code
  has a common interface, then application launcher no longer needs to be
  specialized. The problem is that external code will have their individual
  interface

What's already in the repo: 
- vllm launch script
    * `serve_vllm.py` is both a launcher and a program 
    * `serve_vllm.py` is a launcher script for vllm, because it calls the
      program code in a subprocess, monitors its stdout and stderr, and does
      cleanup
- `pi_tui` launche script

To prevent a massive input from user, Hydra helps with setting most of the
default configurations. It also makes command line argument input simple

## Minimum Startup Version
Needs those at first: 
- Controller
- Application launcher
- Dummy program code

Dummy program code: 
- `dummy_prog.py`
  * The dummy program can be used to test the launcher and controllers by
    mimicing real program behaviors

Dummy launcher code:
- `dummy_launcher.py`

Controller code:
- `controller.py`

~note: here we see a tension point: for each program, there needs to be a
launcher script, so for python apps, we will see a separated launcher script.
This can be somewhat trouble some especially when we can already define the
script behavior. Maybe somekind of base python class can be used to define those
behaviors, but we should put a pin on that for now. 

## Application launcher
program info:
- program name: hard-coded
- command: set after command is built
- endpoint: obtained after monitoring confirmed

launcher should maintain a program card for program status. This card will be
live status of the program, and each update will also be logged as event. 

```json
{}
```

Responsibilities of the application launcher
- Received the configuration for the program
- Perform preparations needed
- Construct the command for the target program
- Launch program
- monitor and record events
- send events to log for outer monitoring
- terminate program
- cleanup after program is closed


### Program Code
Properties
- access endpoint, e.g. port

Lifecycle of a program code: 
- startup
  - there should be a clear signal in stdout to detect for successful startup
  - when startup fails, program exited with non-zero code without stdout signal
    for successful startup
  - timeout in startup
- running
  - healthy running state throughout
  - encounter error of some sort and exited
- complete: cleanup required
  - program shutdown complete
  - cleanup complete
- interrupt to terminate program
  - interrupt signal reaches program correctly and clean complete
- cleanup
  - successful clean up
  - unsuccessful clean up

Scenarios when running vllm: 
1. there is no vllm installed
2. vllm successfully started, printing `startup_str`
3. vllm did not start successfully due to various issues including resources,
   jit compile or other unforeseeable issues. vllm is a complex program so there
   can be many reasons that it could fail to start. 
4. send signal interrupt to terminate the program. 
5. while it is running, there are useful log information we'd like to have, like
   tokens per second generated etc. 

## Failure modes 
1. At one level of deployment path, there is a startup issue even though the
   outer launchers already worked. Thus thus outer ones must also be closed. 
