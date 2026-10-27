#!/bin/bash
HF_HOME="./huggingface/" \
	vllm serve RedHatAI/gemma-4-31B-it-FP8-dynamic \
        --served-model-name local-coder \
        --host 0.0.0.0 \
        --port 8899 \
        --tensor-parallel-size 2 \
	--dtype bfloat16 \
	--kv-cache-dtype auto \
        --max-model-len 256000 \
	--max-num-seqs 6 \
	--enable-chunked-prefill \
        --gpu-memory-utilization 0.90 \
	--enforce-eager \
        --enable-auto-tool-choice \
        --tool-call-parser gemma4 \
        --reasoning-parser gemma4 \
	--chat-template examples/tool_chat_template_gemma4.jinja

