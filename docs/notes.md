
environment => resource allocation => model servers
  => agent clinet => task execution => saved evidence

for each stage: 
- which file controls it? 
- What does it assume about the machine? 
- What observable result proves it works? 


First step is to have a minimal working model on aurora first. 

check boundaries: what does the test have to achieve? 
- correct resouce detection / usage
- connects to the target model
- can respond to simple text request
- can work with tool use
- tracable configuration and logs

I want to run everything on aurora rather than have agent run locally. 
- This is important because tasks can use cluster CPUs rather than my local
machine. 
- Reproducible agent runs
