
## Mon Nov 23 04:59:06 PM UTC 2026
Design decision needed here. 

Concrete behavior: 
Controller, deployment launcher, application launcher, and the program code are
separate scripts connected through message passing. 

- User starts the controller, with the full configurations of the deployment
  launchers and the program. 
- For each deployment launcher, it needs to check that the environment has the
  sufficient dependencies, it has the necessary resources to run
- Communication between the outer launcher (OL) and inner launcher (IL) is done
  through message passing. Specifically, when the outer launcher launches the
  inner launcher, it has direct access to its stdout and stderr, from which OL
  can monitor and detect events from IL. IL therefore must present the correct
  log and event messages to the OL.  
  [ ] Define event schema
- Application launcher is the last launcher that directly launch individual
  applications. Interface with each program must therefore be specifically
  defined.

What's already in the repo: 
- vllm launch script
    * `serve_vllm.py` is both a launcher and a program 
    * `serve_vllm.py` is a launcher script for vllm, because it calls the
      program code in a subprocess, monitors its stdout and stderr, and does
      cleanup
- `pi_tui` launche script

To prevent a massive input from user, Hydra helps with setting most of the
default configurations. It also makes command line argument input simple

