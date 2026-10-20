# Experiment Setup - Zapanese --> Zenglish CFG

## Research Question
1. [RQ1](../../../README.md) "Do LLMs use hierarchical representations?"

## Hypothesis
Behavioral Analysis: If a model can translate OOD frames where the (1) training data minimally requires using linear heuristics, then (2) the model has likely learned a hierarchical algorithm.

- Note: what may seem "easy" to humans may be different for language models, however we will make assumptions that linear "Reverse string" is easier than a hierarchical pattern say "building a complex variable binding/pointer system"

- Link to [results](RESULTS.md)

## Risks

1. Even if a model cannot generalize unseen frames does not guarantee that the model did not learn a hierarchical rule. 

2. Similarly, generalizing to unseen frames is a strong indicator but not guarantee of a hiearchical algorithm

3. The resutls from small models may not generalize to larger models

## Methods

1. Use a CFG to generate the distribution of Zapanese sentences with a single relative clause that allow for scrambling

2. Each Zapanese rule corresponds to a Zenglish rule. For a CFG written in Chomsky Normal Form, an example of the Zapanese rule being `VP -> NP V` would be `VP -> V NP`. 

TODO: Note, it is unclear to me how to make the CFG also allow for scrambling (Object may occur before the Subject)

### Deliverable
1. 3 .csv files, {train, val, test}, which will later be uploaded to HF Hub containing the frames for each partition

## Stimuli

An example of each stimuli is in [Japanese RC Stimuli - RC Frames with Stimuli.csv](src/grammar/zapanese_zenglish_simple/stimuli_examples/Japanese RC Stimuli - RC Frames with Stimuli.csv) with the filled in frames with Dog always used as Subject, Cat used as Object, Bird as the embedded noun, chases or swims as the matrix verb, sees and swims as the embedded verb.

