# Local LLM Inference Setup

This repo is a collection of scripts to help with: 
- Set up LLM inference engine on Gilbreth
- Install Pi as local open-source coding agent
- Connect to the remote LLM inference engine

`conda` should be sufficient for the full setpu. LLM hosting is achieved with
`vllm` which can be installed with pip, and the agent harness `pi` is installed
with `npm`, which can be installed with `conda`

## Instructions of Getting started 

1. Create local conda environment: `conda create -p ./llmenv python=3.14`
2. Activate environment: `conda activate ./llmenv`
3. Install nodejs: `conda install nodejs=26.12.1`
4. Install pi coding agent: `npm install -g --ignore-scripts @earendil-works/pi-coding-agent`
4. Install vllm: `pip install vllm`
5. Get an interactive session with GPU, and get host name with `hostname` and
   get first item, e.g. `gilbreth-n001` if `hostname` gives
`gilbreth-n001.rcac.purdue.edu`
6. Start `vllm` with `bash run_vllm.sh`
7. Modify `providers/vllm/baseUrl` in `pi/models.json` with get host name from
   step 5
8. Run pi coding agent with `PI_CODING_AGENT=./pi pi`, and you should be ready
   to go.

