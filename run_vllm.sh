#!/bin/bash
HF_HOME="./huggingface/" vllm serve cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit \
        --served-model-name local-coder \
        --host 0.0.0.0 \
        --port 8899 \
        --tensor-parallel-size 1 \
        --gpu-memory-utilization 0.90 \
        --max-model-len 65536 \
        --language-model-only \
        --enable-auto-tool-choice \
        --tool-call-parser qwen3_coder \
        --reasoning-parser qwen3

