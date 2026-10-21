"""
Helper functions to run exact string match and token accuracy checks on model at intermediate checkpoints

functions should be of the form (model output, ground_truth) -> metric and be stored in a list of callables which the validation function can call
"""