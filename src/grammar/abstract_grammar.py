"""
Contains two abstract classes: (1) Lexicon and (2) Grammar

The abstract classes are implemented in this file. 

Lexicon supports a mapping of each syntactic category (e.g. transitive verb, intransitive verb, noun, case marking) to a list of lexical items (e.g. chases, swims, bird, ACC)

Grammar supports "generate_frames()" which exhaustively generates all frames based on the CFG rules

Outlines

class Lexicon:
    def get_mappings() -> dict[str, list[str]]

class Grammar:
    def __init__():
       self.lex: Lexicon
       self.rules: str (NLTK style)
    
    def generate_frames() -> list[Frames]:

    def convert_frames_to_csv(frames: list[Frames], out: Path) -> None:
        

class Frames:
    length: int
    flat_str: str
    matrix_verb: str
    matrix_subj: str        
    matrix_obj: str | None
    rc: list[Frames] # empty if no RCs

class RcRame(Frames):
    attached_to: {subj, obj}
    gap_type: {Subj, Obj, None}
    rc: list[Frames] # empty if no RCs
"""