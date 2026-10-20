# TBD Syntax
The TBD here stands for the methods and findings. While we hope to find syntactic hierarchy potentially captured using a unifying framework like Tensor Product Representations, analyzing syntactic computation in LLMs can be messily beautiful. We want to be flexible in our analysis and theoretical assumptions.

## How to Navigate the Codebase
- Before the age of AI Agents, writing code (similar to writing proofs in mathematics) were proxies for understanding. However, the goal was never to write out every line by hand, but to derive deeper understanding that we can share with the world and further discussions in the scientific community.

- Thus, rather than keeping the strict no AI Coding Agent policy I have, my goal for this project is to learn how to use AI *and* still maintain organization and understanding of the code.

The file [codebase-structure.html](structure-visualizer/codebase-structure.html) is a visualizer which shows:
1. How does each file connect with every other file (includes extension). When you click on a node (file)
    a. Incoming red arrows show what this file requires/imports
    b. Outoing green arrows show what this file provides to others

2. The top right button has a toggle which allows you to expand the node in the right hand side toolbar to see every functions signature and a high level description of what it does. The toggle underneat the description of the function shows sample inputs and outputs

3. For files which are not code (e.g. CSVs, YAML, or JSON), those files are indicated with a paper emoji

### Pull Requests
- Pull Requests are meant to be hand written, almost as if it is a test to the human developers that the changes made by AI Agents are correctly interpreted. The Pull Requests are the source of truth which will potentially be used later to re-derive the codebase by hand for the final research product

## Research Questions

Overarching Research Question (RQ):
| What causal mechanisms allow LLMs to realize discrete and symbolic algorithms in continuous and distributed architectures

Specifically, we probe these causal mechanisms through the lens of translation between Head Final and Head Intial Languages. Currently, we use only the toy languages Zapanese (Japanese ordering with English words) and Zenglish (a head initial ordering of Zapanese).

In this investigation of Zapanese --> Zenglish, we ask:

1. When translating between Head Final to Head Initial Languages which require both local and global dependencies between all words in a sentence, do LLMs use a hierarchical representation of the sentence's syntactic structure?

2. If so, how is this hierarchical structure (a) distributed across the residual stream and (b) deployed at translation time

3. What training pressures, lead the model to develop its translation algorithm (e.g. linear vs. hierarchical)?

- One potential answer to these questions is understanding how LLMs can mathematically bind and unbind Tensor Product Representations (TPRs) though this understanding is not clear at the moment.

## Pipeline and Goals

1. Train toy models on toy Context Free Grammar (CFG) to generate hypotheses on larger models
    a. Toy models have increased control over the type of structures the model sees and is a faster test bed for iteration which can take advantage of the multi-node GPU cluster setup

2. Run Residual Stream and Path Patching experiments with original and counterfactuals to generate hypotheses on the causal mechanisms used for translation

3. Scale up experiments to larger models like [Olmo-3-7B-Instruct](allenai/Olmo-3-7B-Instruct)

4. Run additional experiments using experimental hypotheses like Tensor Product Representations and QK Decomposition

## Design Principles
1. Use Markdown files as faithful and accessible human readable documentation to understand what is going on in the codebase

2. Use infrastructure as code (e.g. Python files with constants, Grammar definitions, lexicons) over static files like .md which cannot be used programmatically (even over JSON which cannot support comments)

## Attribution
The CLAUDE.md and structure are heavily inspired by Johnny Wei's [Allegro Project setup](https://github.com/johntzwei/allegro-project)