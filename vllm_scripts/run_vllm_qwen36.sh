#!/bin/bash
HF_HOME="./huggingface/" \
	vllm serve cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit \
        --served-model-name local-coder \
        --host 0.0.0.0 \
        --port 8899 \
        --tensor-parallel-size 2 \
	--dtype half \
	--kv-cache-dtype auto \
        --max-model-len 262144 \
	--max-num-seqs 6 \
	--enable-chunked-prefill \
	--max-num-batched-tokens 2048 \
        --gpu-memory-utilization 0.90 \
	--enforce-eager \
        --enable-auto-tool-choice \
        --tool-call-parser qwen3_coder \
        --reasoning-parser qwen3

