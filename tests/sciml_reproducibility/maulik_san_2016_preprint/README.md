# Replicating Maulik & San, 2016 Preprint with agentic workflows

## Paper
[Maulik & San 2016](https://arxiv.org/abs/1604.08646)

## Models

- GPT-6-Astra
- MiniMax M2.7
- Qwen3.6-35B-A3B-AWQ-4bit
- Google Gemma 4 31B
    - Gemma 4 did not generate a report.
    - The reason for failure to generate a report is that Gemma 4 did not implement the
      numerical solver correctly, and the solver would run for very long time (at least 2
      hours). Gemma 4 did not set proper safeguard or checks or monitoring, and simply
      kept waiting. 
