// Codebase structure data for codebase-structure.html.
//
// This is the single place to edit when files, imports, or function signatures change.
// Loaded via <script src="structure.js"> so the page works from file:// without a server.
//
// node.kind   : "code" | "data" (paper emoji) | "doc" | "config" | "external"
// node.status : "exists" | "stub" (file exists, body not written) | "planned" (not created yet)
// node.files  : optional [{name, description}] for folder nodes; listed in the side panel.
// rows        : [{id, label}] top-to-bottom bands of the drawing; group.row says which band a column
//               belongs to (default: the first row). A labelled divider is drawn between rows.
// edge        : {from, to, kind}  meaning  `from` imports / reads `to`.
//               kind: "import" (static import), "dynamic" (importlib at runtime), "reads" (data file)
//
// In the viewer, selecting a file shows its dependencies as red incoming arrows and the files
// that depend on it as green outgoing arrows.

window.CODEBASE = {
  rows: [
    { id: "generation", label: "grammar generation  (implemented: src/grammar, src/upload, tests)" },
    { id: "training",   label: "training  (PLANNED: src/training/DESIGN.md; dashed = not yet written)" },
  ],

  groups: [
    // row 1: grammar generation (implemented)
    { id: "grammar",    row: "generation", label: "src/grammar  (shared engine)" },
    { id: "experiment", row: "generation", label: "src/grammar/zapanese_zenglish_simple  (data-as-code)" },
    { id: "upload",     row: "generation", label: "src/upload" },
    { id: "tests",      row: "generation", label: "tests" },
    { id: "external",   row: "generation", label: "external packages" },
    // row 2: training (planned; mirrors the engine / experiment split above)
    { id: "training",            row: "training", label: "src/training  (shared engine, PLANNED)" },
    { id: "training_experiment", row: "training", label: "src/training/exp_zapanese_zenglish_simple  (data-as-code, PLANNED)" },
    { id: "training_external",   row: "training", label: "external packages  (uv sync --extra train, PLANNED)" },
  ],

  nodes: [
    // ---------------------------------------------------------------- src/grammar (engine)
    {
      path: "src/grammar/grammar.py", group: "grammar", kind: "code", status: "exists",
      description: "Synchronous-CFG engine (rename of abstract_grammar.py). Concrete dataclasses, no ABCs. Rules may have any arity (ternary rules are used for the matrix clause and RC). Validates finiteness, unambiguity, and the frame-id bijection at construction / enumeration time.",
      functions: [
        {
          signature: "Rule(name: str, lhs: str, rhs: tuple[str, ...], target_perm: tuple[int, ...], tags: Mapping[str, Any] = {})",
          description: "One synchronous rewrite rule. rhs is source (Zapanese) order; target_perm gives target (Zenglish) order as indices into rhs. tags are merged across a derivation into frame metadata.",
          example_input: 'Rule("S_scr", "S", ("NP_acc", "NP_nom", "V_t"), (1, 2, 0), {"scrambled": True})',
          example_output: 'rule.target_rhs == ("NP_nom", "V_t", "NP_acc")',
        },
        {
          signature: "Rule.target_rhs -> tuple[str, ...]",
          description: "Right-hand side reordered by target_perm.",
          example_input: 'Rule("RC_subj_gap", "RC", ("N", "ACC", "V_t"), (2, 0, 1)).target_rhs',
          example_output: '("V_t", "N", "ACC")',
        },
        {
          signature: "Lexicon(words: Mapping[str, tuple[str, ...]])",
          description: "Preterminal category -> words. Raises on an empty category or a word listed under two categories (needed so frame-level unambiguity implies sentence-level).",
          example_input: 'Lexicon({"N": ("dog", "cat"), "V_t": ("chases",), "V_i": ("swims",), "NOM": ("NOM",), "ACC": ("ACC",)})',
          example_output: 'lex.categories == frozenset({"N", "V_t", "V_i", "NOM", "ACC"})',
        },
        {
          signature: "Frame(frame_id: str, derivation: tuple[Rule, ...], source_yield: tuple[str, ...], target_yield: tuple[str, ...], alignment: tuple[int, ...], metadata: Mapping[str, Any])",
          description: "An unfilled sentence: the rules applied (preorder), both preterminal yields, and alignment[j] = source slot copied to target position j (so filling the source fills the target).",
          example_input: 'grammar.enumerate_frames()[1]',
          example_output: 'Frame(frame_id="F01", source_yield=("N","NOM","N","ACC","V_t"), target_yield=("N","NOM","V_t","N","ACC"), alignment=(0,1,4,2,3), metadata={"matrix": "trans", "scrambled": False, ...})',
        },
        {
          signature: "Frame.fill(self, lexicon: Lexicon, n: int, rng: random.Random) -> list[Filled]",
          description: "n distinct fillings sampled WITHOUT replacement: draws indices from range(product_size) and un-ranks each (mixed radix) into one word per slot, so the Cartesian product is never materialised. Caps at product_size with a warning. Repeated words across slots are allowed.",
          example_input: 'frame_F01.fill(lex, n=2, rng=random.Random(0))',
          example_output: '[Filled("F01", "dog NOM dog ACC chases", "dog NOM chases dog ACC"), Filled("F01", "cat NOM dog ACC chases", "cat NOM chases dog ACC")]',
        },
        {
          signature: "Filled(frame_id: str, source: str, target: str)",
          description: "A filled sentence pair, tokens space-joined.",
          example_input: 'Filled("F02", "cat ACC dog NOM chases", "dog NOM chases cat ACC")',
          example_output: "(dataclass instance)",
        },
        {
          signature: "Grammar(rules: tuple[Rule, ...], start: str, preterminals: frozenset[str], frame_ids: Mapping[str, Mapping[str, Any]])",
          description: "Validates: every RHS symbol is a LHS or preterminal; start is a LHS; no category reaches itself (finite language); rule names unique.",
          example_input: 'Grammar(RULES, start="S", preterminals=frozenset({"N","NOM","ACC","V_t","V_i"}), frame_ids=FRAME_IDS)',
          example_output: "Grammar instance, or ValueError naming the offending rule / cycle",
        },
        {
          signature: "Grammar.enumerate_frames(self) -> list[Frame]",
          description: "Exhaustive DFS over all derivations. Raises if two derivations share a source yield (translation would not be a function) or if frame_ids is not a bijection with the enumerated frames. Sorted by frame_id.",
          example_input: "grammar.enumerate_frames()",
          example_output: "[Frame(F01), Frame(F02), ..., Frame(F18)]  # 18 frames for zapanese_zenglish_simple",
        },
        {
          signature: "Grammar.validate_lexicon(self, lexicon: Lexicon) -> None",
          description: "Raises unless lexicon.categories == self.preterminals.",
          example_input: "grammar.validate_lexicon(lex)",
          example_output: "None, or ValueError listing missing / extra categories",
        },
      ],
    },
    {
      path: "src/grammar/splits.py", group: "grammar", kind: "code", status: "exists",
      description: "Shared split types. An experiment's splits.py only instantiates these.",
      functions: [
        {
          signature: "FrameSplit(name: str, description: str, frames: frozenset[str])",
          description: "A named set of frame IDs.",
          example_input: 'FrameSplit("ood_level1", "object-gap RC on first noun", frozenset({"F10", "F05", "F17"}))',
          example_output: "(dataclass instance)",
        },
        {
          signature: "FillingSplit(frame_split: str, subsets: Mapping[str, float])",
          description: "How the fillings of one frame split are divided. Fractions must sum to 1.",
          example_input: 'FillingSplit("train", {"train": 0.9, "dev": 0.1})',
          example_output: "(dataclass instance)",
        },
        {
          signature: "SplitSpec(frame_splits: tuple[FrameSplit, ...], filling_splits: tuple[FillingSplit, ...], repeat: int, seed: int)",
          description: "Full split specification: frames -> splits, fillings -> subsets, samples per frame, RNG seed.",
          example_input: "SplitSpec(frame_splits=(...), filling_splits=(...), repeat=1000, seed=0)",
          example_output: "(dataclass instance)",
        },
        {
          signature: "SplitSpec.validate(self, frame_ids: frozenset[str]) -> None",
          description: "Raises unless frame_splits exactly partition frame_ids and every frame split has one FillingSplit.",
          example_input: 'spec.validate(frozenset(f.frame_id for f in grammar.enumerate_frames()))',
          example_output: "None, or ValueError naming unassigned / unknown / duplicated frame IDs",
        },
        {
          signature: "FillingSplit.cut(self, n: int) -> dict[str, int]",
          description: "How many of n fillings each subset gets (cumulative rounding, always sums to n).",
          example_input: 'FillingSplit("train", {"train": 0.9, "dev": 0.1}).cut(7)',
          example_output: '{"train": 6, "dev": 1}',
        },
        {
          signature: "SplitSpec.frame_split_of(self, frame_id: str) -> str  /  SplitSpec.filling_split_of(self, frame_split: str) -> FillingSplit",
          description: "Lookups used by generate_frames.",
          example_input: 'SPLITS.frame_split_of("F10")',
          example_output: '"ood_level1"',
        },
      ],
    },
    {
      path: "src/grammar/generate_frames.py", group: "grammar", kind: "code", status: "exists",
      description: "Library + CLI that turns (Grammar, Lexicon, SplitSpec) into CSVs. No grammar logic. stdlib csv only.",
      functions: [
        {
          signature: "generate(grammar: Grammar, lexicon: Lexicon, spec: SplitSpec, out_dir: Path) -> dict[str, Path]",
          description: "Writes out_dir/frames.csv (one row per frame + metadata columns) and out_dir/filled/<subset>.csv, where subset names come from the experiment's FillingSplit and must be unique across the spec. Per frame: fill(repeat) with rng seeded by f\"{seed}:{frame_id}\", shuffle, cut by subset fractions. Returns {subset_name: path}.",
          example_input: 'generate(GRAMMAR, LEXICON, SPLITS, Path("data/zapanese_zenglish_simple"))',
          example_output: '{"frames": .../frames.csv, "train": .../filled/train.csv, "dev": .../filled/dev.csv, "ood_level1_select": ..., "ood_level1_report": ..., "ood_level2_select": ..., "ood_level2_report": ...}',
        },
        {
          signature: "frame_rows(frames: list[Frame], spec: SplitSpec) -> tuple[list[str], list[dict[str, str]]]",
          description: "Columns and rows for frames.csv: FRAME_COLUMNS (frame_id, split, source_frame, target_frame, alignment, derivation) + one column per metadata key.",
          example_input: "frame_rows(GRAMMAR.enumerate_frames(), SPLITS)",
          example_output: '(["frame_id", "split", ..., "gap", "matrix", "rc_on", "scrambled"], [{"frame_id": "F01", "split": "train", ...}, ...])',
        },
        {
          signature: "load_experiment(module: str) -> tuple[Grammar, Lexicon, SplitSpec]",
          description: "importlib-imports <module>.cfg, .lexicon, .splits and returns their GRAMMAR, LEXICON, SPLITS constants. This is the contract an experiment package must meet.",
          example_input: 'load_experiment("grammar.zapanese_zenglish_simple")',
          example_output: "(Grammar, Lexicon, SplitSpec)",
        },
        {
          signature: "main(argv: list[str] | None = None) -> None",
          description: "argparse entry point; prints a row-count table per output file.",
          example_input: "uv run python -m grammar.generate_frames --experiment grammar.zapanese_zenglish_simple --out data/zapanese_zenglish_simple",
          example_output: "Prints a table of files written and row counts per subset",
        },
      ],
    },

    // ---------------------------------------------------------------- experiment (next step)
    {
      path: "src/grammar/zapanese_zenglish_simple/cfg.py", group: "experiment", kind: "code", status: "exists",
      description: "Data only: 15 Rule instances (8 matrix S variants enforcing one RC, 4 NP rules, 3 RC rules; ternary flat rules, scrambling = S_scr*) and FRAME_IDS mapping F01..F18 to metadata. Tested against the stimuli CSV.",
      functions: [
        {
          signature: "RULES: tuple[Rule, ...]",
          description: "All rules. Scrambling = S_scr: S -> NP_acc NP_nom V_t with perm (1, 2, 0); S_scr_rcS / S_scr_rcO put the RC on the subject / object.",
          example_input: "RULES[5]",
          example_output: 'Rule("S_scr", "S", ("NP_acc", "NP_nom", "V_t"), (1, 2, 0), {"matrix": "trans", "scrambled": True, "rc_on": "none"})',
        },
        {
          signature: "FRAME_IDS: dict[str, dict[str, Any]]",
          description: "Spreadsheet F-number -> metadata that uniquely identifies the frame. Validated as a bijection with enumerate_frames().",
          example_input: 'FRAME_IDS["F03"]',
          example_output: '{"matrix": "trans", "scrambled": False, "rc_on": "subj", "gap": "subj", "rc_verb": "trans"}',
        },
        {
          signature: "GRAMMAR: Grammar",
          description: "Grammar(RULES, 'S', PRETERMINALS, FRAME_IDS).",
          example_input: "len(GRAMMAR.enumerate_frames())",
          example_output: "18",
        },
      ],
    },
    {
      path: "src/grammar/zapanese_zenglish_simple/lexicon.py", group: "experiment", kind: "code", status: "exists",
      description: "Data only: N_VERBS = 13 transitive, 13 intransitive, 26 nouns (one animal per letter A-Z), case markers NOM / ACC. Verb classes disjoint (asserted).",
      functions: [
        {
          signature: "LEXICON: Lexicon",
          description: "The word lists.",
          example_input: 'LEXICON.words["V_i"]',
          example_output: '("swims", "dances", "sleeps", "runs", "jumps", "sits", "laughs", "waits", "flies", "hides", "sings", "walks", "crawls")',
        },
      ],
    },
    {
      path: "src/grammar/zapanese_zenglish_simple/splits.py", group: "experiment", kind: "code", status: "exists",
      description: "Data only: frame-level split (train / ood_level1 / ood_level2) and filling-level split (train/dev 0.9/0.1, *_select/*_report 0.5/0.5), REPEAT = 1000, SEED = 0.",
      functions: [
        {
          signature: "SPLITS: SplitSpec",
          description: "train = F11 F01 F02 F03 F12 F16 F18 F08 F15; ood_level1 = F10 F05 F17; ood_level2 = F04 F13 F06 F07 F09 F14.",
          example_input: "SPLITS.frame_splits[1].frames",
          example_output: 'frozenset({"F10", "F05", "F17"})',
        },
      ],
    },
    {
      path: "src/grammar/zapanese_zenglish_simple/run.py", group: "experiment", kind: "code", status: "exists",
      description: "Thin argparse wrapper. `generate` writes frames/ (default) via generate_frames.generate; `upload` pushes frames.csv and filled/ as two HF datasets in one collection.",
      functions: [
        {
          signature: "cmd_generate(out: Path) -> dict[str, Path]  /  cmd_upload(out: Path, private: bool) -> list[str]  /  main(argv: list[str] | None = None) -> None",
          description: "Subcommands: generate [--out DIR] ; upload [--out DIR] [--private]. Default DIR is this folder's frames/.",
          example_input: "uv run python src/grammar/zapanese_zenglish_simple/run.py generate",
          example_output: "frames 18 rows, train 7504, dev 834, ood_level1_select 1500, ood_level1_report 1500, ood_level2_select 3000, ood_level2_report 3000",
        },
      ],
    },
    {
      path: "src/grammar/zapanese_zenglish_simple/stimuli_examples/Japanese RC Stimuli - RC Frames with Stimuli.csv", group: "experiment", kind: "data", status: "exists",
      description: "Hand-written reference: the 18 frames with example fillings. Ground truth cfg.py is tested against.",
      functions: [],
    },

    {
      path: "src/grammar/zapanese_zenglish_simple/frames/", group: "experiment", kind: "data", status: "exists",
      description: "regenerated by run.py generate, published on the Hub",
      functions: [],
      files: [
        { name: "frames.csv",                   description: "All 18 unfilled frames (preterminal yields, alignment, derivation, metadata) with their frame-level split; 18 rows." },
        { name: "filled/train.csv",             description: "Training fillings: 90% of each train frame's fillings (no RC, or first-noun subject-gap RC); 7504 rows." },
        { name: "filled/dev.csv",               description: "In-distribution held-out fillings of the train frames (other 10%), for checkpoint selection; 834 rows." },
        { name: "filled/ood_level1_select.csv", description: "OOD level 1 (first-noun object-gap RC: F05, F10, F17), half used to select analysis checkpoints; 1500 rows." },
        { name: "filled/ood_level1_report.csv", description: "OOD level 1, other half: the published accuracy; 1500 rows." },
        { name: "filled/ood_level2_select.csv", description: "OOD level 2 (RC on the second noun: F04, F06, F07, F09, F13, F14), half used to select analysis checkpoints; 3000 rows." },
        { name: "filled/ood_level2_report.csv", description: "OOD level 2, other half: the published accuracy; 3000 rows." },
      ],
    },
    {
      path: "hf://datasets/kylelovesllms/zapanese_zenglish_simple-filled", group: "experiment", kind: "data", status: "exists",
      description: "The HF Hub copy of frames/filled/ (pushed by run.py upload via upload_hf.upload_dataset; collection translation-syntax-datasets-zapanese_zenglish_simple). This is the data input of the training row: training reads the Hub dataset, never the local CSVs, and derives the repo id from the grammar experiment's constants.",
      functions: [],
      files: [
        { name: "train / dev / ood_level1_select / ood_level1_report / ood_level2_select / ood_level2_report", description: "One split per filled/*.csv, columns frame_id, source, target. Subset names are exactly the FillingSplit subset names in splits.py." },
      ],
    },

    // ---------------------------------------------------------------- src/upload
    {
      path: "src/upload/upload_hf.py", group: "upload", kind: "code", status: "exists",
      description: "Push a local dataset folder to the HF Hub and add it to a collection. Token from HF_TOKEN env var via huggingface_hub defaults; never read or printed.",
      functions: [
        {
          signature: "upload_dataset(local_dir: Path, repo_id: str, readme_path: Path, collection_title: str, private: bool = False, api: HfApi | None = None) -> str",
          description: "create_repo(exist_ok) -> upload_folder(*.csv) -> upload README.md -> create_collection(exists_ok) -> add_collection_item. Returns the repo URL. `api` is injectable for tests.",
          example_input: 'upload_dataset(Path("data/zapanese_zenglish_simple/filled"), "kylelovesllms/zapanese_zenglish_simple-filled", Path(".../Filled.md"), "translation-syntax-datasets-zapanese_zenglish_simple")',
          example_output: '"https://huggingface.co/datasets/kylelovesllms/zapanese_zenglish_simple-filled"',
        },
        {
          signature: "upload_model(*args, **kwargs) -> str  [stub]",
          description: "Documented stub for model checkpoints; implemented when the first training experiment lands.",
          example_input: "-",
          example_output: "NotImplementedError",
        },
      ],
    },

    // ---------------------------------------------------------------- tests
    {
      path: "tests/test_grammar.py", group: "tests", kind: "code", status: "exists",
      description: "Rule/Lexicon/Grammar validation errors (bad perm, cycle, ambiguity, tag conflicts, frame-id bijection), toy enumeration incl. alignment, scrambled == unscrambled target, fill without replacement / cap / determinism.",
      functions: [],
    },
    {
      path: "tests/test_splits.py", group: "tests", kind: "code", status: "exists",
      description: "Partition check and fraction-sum check raise correctly.",
      functions: [],
    },
    {
      path: "tests/test_generate_frames.py", group: "tests", kind: "code", status: "exists",
      description: "generate() into a tmp dir: files exist, row counts, subsets disjoint and deterministic; load_experiment contract; CLI main().",
      functions: [],
    },

    {
      path: "tests/test_zapanese_zenglish_simple.py", group: "tests", kind: "code", status: "exists",
      description: "Conformance: the enumerated frames equal the stimuli CSV row by row (both yields + metadata), the 14 same-Zenglish pairs hold, splits partition the 18 frames and match the README, lexicon shape.",
      functions: [],
    },
    {
      path: "tests/test_upload_hf.py", group: "tests", kind: "code", status: "exists",
      description: "upload_dataset call sequence against a fake HfApi; input validation; upload_model stub.",
      functions: [],
    },
    {
      path: "tests/toy_experiment/", group: "tests", kind: "code", status: "exists",
      description: "Smallest working experiment package (cfg.py, lexicon.py, splits.py): 5 frames, one scrambled rule, one subject-gap RC. Fixtures in conftest.py import it; also the template for the real experiment's files.",
      functions: [
        { signature: "cfg.GRAMMAR: Grammar  /  lexicon.LEXICON: Lexicon  /  splits.SPLITS: SplitSpec",
          description: "The data-as-code contract load_experiment() reads.",
          example_input: 'load_experiment("toy_experiment")',
          example_output: "(Grammar, Lexicon, SplitSpec)" },
      ],
    },

    // ---------------------------------------------------------------- external
    {
      path: "huggingface_hub", group: "external", kind: "external", status: "exists",
      description: "HfApi: create_repo, upload_folder, add_collection_item.",
      functions: [],
    },

    // ================================================================ ROW 2: src/training (PLANNED)
    // Design: src/training/DESIGN.md. Engine = classes with no experiment knowledge; experiment
    // package = one UPPERCASE instance per file; contract the engine relies on: <pkg>.experiment.EXPERIMENT.
    // ---------------------------------------------------------------- src/training (engine)
    {
      path: "src/training/model.py", group: "training", kind: "code", status: "planned",
      description: "Architecture and optimisation configs as frozen dataclasses validated in __post_init__, so a bad grid fails at import time, before a GPU is allocated. No torch here. Replaces the modelconfigs/ directory: the ModelConfig class lives in the engine, the grid lives in the experiment's models.py.",
      functions: [
        {
          signature: "ModelConfig(n_layer: int, n_head: int, d_model: int, d_ff: int, dropout: float, tie_embeddings: bool = False)",
          description: "Architecture only. Raises unless d_model % n_head == 0 (HF requirement; this is why the grid uses {2, 4, 8} heads at d_model 256, not {2, 4, 6}).",
          example_input: "ModelConfig(n_layer=2, n_head=6, d_model=256, d_ff=1024, dropout=0.0)",
          example_output: "ValueError: d_model=256 is not divisible by n_head=6",
        },
        {
          signature: "ModelConfig.to_hf(self, vocab_size: int, max_len: int) -> GPT2Config",
          description: "Derive the HuggingFace config. config.json is written by save_pretrained from this and never hand-edited.",
          example_input: "ModelConfig(2, 4, 256, 1024, 0.0).to_hf(vocab_size=60, max_len=20)",
          example_output: "GPT2Config(n_layer=2, n_head=4, n_embd=256, n_inner=1024, vocab_size=60, n_positions=20, resid_pdrop=0.0, tie_word_embeddings=False)",
        },
        {
          signature: 'TrainConfig(optimizer: Literal["adamw"], lr: float, warmup_steps: int, weight_decay: float, lr_schedule: Literal["constant_after_warmup", "cosine"], total_steps: int, batch_size: int, seq_len: int, examples_per_epoch: int, eval_every: int, checkpoint_every: int, loss_segments: frozenset[Segment]) / TrainConfig.tokens_per_step: int / TrainConfig.tokens_per_epoch: int / TrainConfig.total_token_budget: int / TrainConfig.epochs: float',
          description: "Optimisation only (AdamW); varies independently of the model. Raises unless eval_every and checkpoint_every divide total_steps.",
          example_input: 'TrainConfig(optimizer="adamw", lr=1e-3, warmup_steps=1000, weight_decay=0.0, lr_schedule="constant_after_warmup", total_steps=125_000, batch_size=256, seq_len=20, examples_per_epoch=15_008, eval_every=1000, checkpoint_every=10_000, loss_segments=frozenset({Segment.SOURCE, Segment.SEP, Segment.OUTPUT, Segment.EOS}))',
          example_output: "tokens_per_step=5120, tokens_per_epoch=300160, total_token_budget=640000000, epochs=2132.2  # derived in __post_init__; 125 evals, 13 checkpoints incl. final",
        },
      ],
    },
    {
      path: "src/training/data.py", group: "training", kind: "code", status: "planned",
      description: "Turns the Hub dataset of a grammar experiment into token sequences. Pure data: enums, frozen dataclasses, a word-level Vocab and build_examples. Subset names come from the grammar's SplitSpec and the vocabulary from its Lexicon; nothing is retyped. Two seeds: the data seed here fixes the dataset for every run; the run seed lives in RunSpec.",
      functions: [
        {
          signature: "Task(Enum)  /  Role(Enum)",
          description: "Task: TRANSLATE = \"translate\", COPY = \"copy\". Role: TRAIN (seen in the loss), SELECT (may inform checkpoint choice), REPORT (evaluated every eval, never consulted, never seen as copy).",
          example_input: "Task.COPY.value, list(Role)",
          example_output: '"copy", [Role.TRAIN, Role.SELECT, Role.REPORT]',
        },
        {
          signature: "SubsetUse(subset: str, task: Task, role: Role)",
          description: "One (subset, task, role) triple; subset must exist in the grammar's SPLITS.",
          example_input: 'SubsetUse("ood_level1_select", Task.TRANSLATE, Role.SELECT)',
          example_output: "(dataclass instance)",
        },
        {
          signature: 'CopyBudget(match: Literal["translate"], spread: Literal["even_per_frame"])',
          description: "How many copy examples to build (n_copy == number of TRAIN translate examples) and how to spread them over frames (water-fill: equal share per frame, capped by each frame's pool, the remainder redistributed).",
          example_input: 'CopyBudget("translate", "even_per_frame")',
          example_output: "(dataclass instance)",
        },
        {
          signature: "CopyBudget.allocate(self, n_total: int, pools: Mapping[str, int]) -> dict[str, int]  (proposed name)",
          description: "The water-fill. Even share 7,504 / 18 = 416.9; F11's copy pool is only 338 (train + dev sources), so it is capped and its remainder spreads over the other 17 frames.",
          example_input: 'budget.allocate(7504, {"F01": 1000, ..., "F11": 338, ..., "F04": 500, ...})  # 1000 per train frame, 500 per OOD frame',
          example_output: '{"F11": 338, "F01": 422, "F02": 422, ..., "F18": 421}  # 17 frames get 421 or 422; sums to 7504',
        },
        {
          signature: "DatasetSetup(hf_repo: str, splits: SplitSpec, uses: tuple[SubsetUse, ...], copy_budget: CopyBudget, data_seed: int)",
          description: "Validates: every subset exists in splits; a (subset, TRANSLATE) pair is never both TRAIN and SELECT/REPORT; no REPORT subset is used for COPY; at least one TRAIN use.",
          example_input: 'DatasetSetup("kylelovesllms/zapanese_zenglish_simple-filled", SPLITS, uses=(SubsetUse("ood_level1_report", Task.COPY, Role.TRAIN), ...), copy_budget=..., data_seed=0)',
          example_output: "ValueError: REPORT subset 'ood_level1_report' may not be used for COPY",
        },
        {
          signature: 'SequenceFormat(bos: str = "<bos>", eos: str = "<eos>", pad: str = "<pad>", task_tokens: Mapping[Task, str], max_len: int)',
          description: "<bos> SOURCE <sep> <task> OUTPUT <eos>, padded to max_len. The task token follows the source so the model must parse the sentence before it knows the task; <sep> is a real prediction target (is the string complete?). max_len is derived from the grammar's longest frame (8 + 8 + 4 = 20), not a magic number.",
          example_input: 'FORMAT.render(source="cat ACC dog NOM chases", task=Task.TRANSLATE, output="dog NOM chases cat ACC")',
          example_output: '"<bos> cat ACC dog NOM chases <sep> <translate> dog NOM chases cat ACC <eos> <pad> ... <pad>"  # 20 tokens',
        },
        {
          signature: "Vocab(tokens: tuple[str, ...])  /  Vocab.from_lexicon(lexicon: Lexicon, fmt: SequenceFormat) -> Vocab  /  Vocab.encode(self, words: Sequence[str]) -> list[int]  /  Vocab.decode(self, ids: Sequence[int]) -> list[str]",
          description: "Word-level vocabulary: every lexicon word + case markers + the 5 special tokens, in a fixed order; written once per experiment as HF tokenizer.json so collaborators can from_pretrained it.",
          example_input: "len(Vocab.from_lexicon(LEXICON, FORMAT))",
          example_output: "60  # 26 nouns + 13 + 13 verbs + NOM ACC + <bos> <sep> <eos> <pad> <translate> <copy>",
        },
        {
          signature: "build_examples(setup: DatasetSetup, fmt: SequenceFormat, vocab: Vocab, rows: Mapping[str, list[Filled]]) -> dict[Role, list[Example]]",
          description: "Translate examples from TRANSLATE uses; copy examples from the source side of every COPY use, water-filled over frames by copy_budget; sampled without replacement with data_seed so all 36 runs see the identical dataset. Each Example keeps (subset, task, frame_id) for the metrics group-by.",
          example_input: "build_examples(DATASET, FORMAT, vocab, rows)",
          example_output: "{Role.TRAIN: 15,008 examples (7,504 translate + 7,504 copy), Role.SELECT: 5,334, Role.REPORT: 4,500}",
        },
      ],
    },
    {
      path: "src/training/metrics.py", group: "training", kind: "code", status: "planned",
      description: "Metric protocol, the two metrics, per-segment loss and the (step, subset, task, frame_id) aggregation that metrics.csv and RESULTS.md are built from. Replaces the eval_helpers.py stub.",
      functions: [
        {
          signature: "Metric(Protocol)  /  Metric.__call__(self, prediction: Sequence[str], reference: Sequence[str]) -> float",
          description: "A named callable (model output tokens, ground-truth tokens) -> score in [0, 1]; Experiment.metrics is a tuple of these.",
          example_input: "TOKEN_ACCURACY.name",
          example_output: '"token_accuracy"',
        },
        {
          signature: "TOKEN_ACCURACY: Metric  /  EXACT_MATCH: Metric",
          description: "Position-wise accuracy over the reference length (missing tokens count as wrong), and 1.0 iff the decoded output equals the reference exactly.",
          example_input: 'TOKEN_ACCURACY(["dog", "NOM", "chases", "dog", "ACC"], ["dog", "NOM", "chases", "cat", "ACC"]), EXACT_MATCH(same)',
          example_output: "0.8, 0.0",
        },
        {
          signature: 'segment_losses(logits: Float[Tensor, "batch seq vocab"], targets: Int[Tensor, "batch seq"], segment: Int[Tensor, "batch seq"]) -> dict[str, float]',
          description: "Mean cross-entropy per segment (source, sep, task, output, eos), all logged even though <task> is masked from the training loss. <sep> loss is not expected to reach 0: three train frames are proper prefixes of level-2 frames (F01/F04, F02/F09, F11/F13), a feature of head-final grammar, not a bug.",
          example_input: "segment_losses(logits, targets, segment)  # segment ids 0 = source, 1 = sep, 2 = task, 3 = output, 4 = eos; pad ignored",
          example_output: '{"source": 1.92, "sep": 0.04, "task": 0.69, "output": 0.01, "eos": 0.00}  # task logged but unscored; sep > 0 from the prefix frames',
        },
        {
          signature: "EvalRecord(step: int, subset: str, task: Task, frame_id: str, prediction: tuple[str, ...], reference: tuple[str, ...])  /  aggregate(records: Iterable[EvalRecord], metrics: tuple[Metric, ...]) -> list[dict[str, Any]]",
          description: "One record per decoded prompt; aggregate() groups by (step, subset, task, frame_id) and averages each metric, so the per-frame error analysis in RESULTS.md is a group-by, not a second pass. Rows are appended to artifacts/<slug>/metrics.csv and logged to wandb.",
          example_input: "aggregate(records, (TOKEN_ACCURACY, EXACT_MATCH))[0]",
          example_output: '{"step": 50000, "subset": "ood_level1_report", "task": "translate", "frame_id": "F10", "n": 500, "token_accuracy": 0.71, "exact_match": 0.12}',
        },
      ],
    },
    {
      path: "src/training/experiment.py", group: "training", kind: "code", status: "planned",
      description: "The grid as pure data: RunSpec (one point) and Experiment (the whole design). Doctestable, holds no torch state. The analogue of Grammar: it describes, train.py runs.",
      functions: [
        {
          signature: "RunSpec(experiment: str, model: ModelConfig, train: TrainConfig, seed: int)",
          description: "One run of the grid. seed is the RUN seed (parameter init, batch shuffling, dropout masks); the data seed lives in DatasetSetup.",
          example_input: 'RunSpec("exp_zapanese_zenglish_simple", ModelConfig(2, 4, 256, 1024, 0.0), TRAIN, seed=42)',
          example_output: "(dataclass instance)",
        },
        {
          signature: "RunSpec.slug -> str",
          description: "Derived run name, never typed by hand: gpt2-<n_layer>l<n_head>h<d_model>d-s<seed>. Names the artifacts/ folder, the wandb run, and the HF model repo.",
          example_input: 'RunSpec("exp_zapanese_zenglish_simple", ModelConfig(2, 4, 256, 1024, 0.0), TRAIN, seed=42).slug',
          example_output: '"gpt2-2l4h256d-s42"',
        },
        {
          signature: "Experiment(name: str, dataset: DatasetSetup, format: SequenceFormat, models: tuple[ModelConfig, ...], train: TrainConfig, seeds: tuple[int, ...], metrics: tuple[Metric, ...])",
          description: "Everything a run needs, as data. Validates that format.task_tokens covers every Task used in dataset.uses and that model/seed tuples are non-empty and duplicate-free.",
          example_input: "Experiment(name=\"exp_zapanese_zenglish_simple\", dataset=DATASET, format=FORMAT, models=MODELS, train=TRAIN, seeds=SEEDS, metrics=(TOKEN_ACCURACY, EXACT_MATCH))",
          example_output: "(dataclass instance)",
        },
        {
          signature: "Experiment.runs(self) -> list[RunSpec]",
          description: "Seed-major order: indices 0-8 are seed 42 across all nine architectures, 9-17 seed 43, ... so the first nine array jobs give one reading per architecture. Index = SLURM_ARRAY_TASK_ID.",
          example_input: "[r.slug for r in EXPERIMENT.runs()][:3], len(EXPERIMENT.runs())",
          example_output: '["gpt2-2l2h256d-s42", "gpt2-2l4h256d-s42", "gpt2-2l8h256d-s42"], 36',
        },
        {
          signature: "Experiment.wandb_project(self, run: RunSpec) -> str  /  Experiment.wandb_group(self, run: RunSpec) -> str",
          description: "Project <dataset>-<steps>; group = model slug without the seed; job_type seed<N>; run name = slug. The config logged is the full run_config.json plus its path.",
          example_input: "EXPERIMENT.wandb_project(run), EXPERIMENT.wandb_group(run)",
          example_output: '"zapanese_zenglish_simple-125000", "gpt2-2l4h256d"',
        },
      ],
    },
    {
      path: "src/training/train.py", group: "training", kind: "code", status: "planned",
      description: "The only module that owns torch state: the training loop, checkpoints, eval hooks and wandb logging for one RunSpec. Nothing here holds both a config and a live model for longer than train_run's frame. Replaces the train_model.py stub.",
      functions: [
        {
          signature: "train_run(run: RunSpec, out_dir: Path) -> Path",
          description: "Writes out_dir/<slug>/run_config.json first (the launch record), seeds torch with run.seed, builds GPT2LMHeadModel from run.model.to_hf, AdamW + linear warmup then run.train.lr_schedule, loss over positions whose target segment is in run.train.loss_segments (<task> masked), every eval_every steps calls evaluate() on SELECT + REPORT examples and logs to wandb, every checkpoint_every steps save_pretrained into checkpoints/step<N>/. Returns the run folder.",
          example_input: 'train_run(EXPERIMENT.runs()[1], Path("src/training/exp_zapanese_zenglish_simple/artifacts"))',
          example_output: "Path(\".../artifacts/gpt2-2l4h256d-s42\")  # run_config.json, checkpoints/step010000 ... step125000, decodes/step001000.csv ..., metrics.csv",
        },
        {
          signature: 'evaluate(model: GPT2LMHeadModel, examples: Sequence[Example], fmt: SequenceFormat, vocab: Vocab, step: int) -> list[EvalRecord]',
          description: "Greedy decoding from the prompt <bos> SOURCE <sep> <task> until <eos> or max_len, batched; one EvalRecord per example. Decodes are also written to decodes/step<N>.csv.",
          example_input: 'prompt "<bos> cat ACC dog NOM chases <translate>"',
          example_output: 'prediction ("dog", "NOM", "chases", "cat", "ACC")',
        },
      ],
    },

    // ---------------------------------------------------------------- src/training/exp_zapanese_zenglish_simple (data-as-code)
    {
      path: "src/training/exp_zapanese_zenglish_simple/models.py", group: "training_experiment", kind: "code", status: "planned",
      description: "Data only: the architecture grid as a comprehension, because the grid IS the experimental manipulation. GPT-2, d_model 256, d_ff 1024, untied embeddings, dropout 0; {2, 4, 6} layers x {2, 4, 8} heads.",
      functions: [
        {
          signature: "MODELS: tuple[ModelConfig, ...]",
          description: "9 configs, layer-major.",
          example_input: "[(m.n_layer, m.n_head) for m in MODELS]",
          example_output: "[(2, 2), (2, 4), (2, 6), (4, 2), (4, 4), (4, 6), (6, 2), (6, 4), (6, 6)]",
        },
      ],
    },
    {
      path: "src/training/exp_zapanese_zenglish_simple/dataset.py", group: "training_experiment", kind: "code", status: "planned",
      description: "Data only, and the single-source-of-truth link to the grammar row: imports grammar.zapanese_zenglish_simple.splits.SPLITS (subset names), .lexicon.LEXICON (vocabulary) and .cfg.GRAMMAR (max_len from the longest frame). Nothing about the dataset is restated here.",
      functions: [
        {
          signature: "DATASET: DatasetSetup",
          description: "hf_repo = kylelovesllms/zapanese_zenglish_simple-filled; translate: train TRAIN, dev / ood_level1_select / ood_level2_select SELECT, ood_level1_report / ood_level2_report REPORT; copy TRAIN from every subset except *_report; CopyBudget(\"translate\", \"even_per_frame\"); data_seed = 0.",
          example_input: "[u for u in DATASET.uses if u.task is Task.COPY]",
          example_output: '[SubsetUse("train", COPY, TRAIN), SubsetUse("dev", COPY, TRAIN), SubsetUse("ood_level1_select", COPY, TRAIN), SubsetUse("ood_level2_select", COPY, TRAIN)]',
        },
        {
          signature: "FORMAT: SequenceFormat",
          description: "task_tokens {TRANSLATE: \"<translate>\", COPY: \"<copy>\"}; max_len = max(len(f.source_yield) + len(f.target_yield) for f in GRAMMAR.enumerate_frames()) + 3.",
          example_input: "FORMAT.max_len",
          example_output: "20  # 8 + 8 + <bos> <sep> <task> <eos>",
        },
      ],
    },
    {
      path: "src/training/exp_zapanese_zenglish_simple/training.py", group: "training_experiment", kind: "code", status: "planned",
      description: "Data only: the optimisation recipe shared by every run and the run seeds: AdamW lr 1e-3, 1,000-step linear warmup then constant, no weight decay, eval every 1,000 steps, checkpoint every 10,000.",
      functions: [
        {
          signature: "TRAIN: TrainConfig  /  SEEDS: tuple[int, ...]",
          description: "TRAIN: 125,000 steps, batch 256, lr 1e-3, warmup 1,000, weight decay 0.1, constant after warmup, eval every 1,000, checkpoint every 10,000, loss on all tokens. SEEDS: run seeds.",
          example_input: "TRAIN.total_steps * TRAIN.batch_size * FORMAT.max_len, SEEDS",
          example_output: "640_000_000, (42, 43, 44, 45)  # 2,132.2 epochs over 15,008 unique training examples",
        },
      ],
    },
    {
      path: "src/training/exp_zapanese_zenglish_simple/experiment.py", group: "training_experiment", kind: "code", status: "stub",
      description: "Binds MODELS, DATASET, FORMAT, TRAIN, SEEDS and the metrics into one Experiment. This is the contract run.py and tests rely on: <pkg>.experiment.EXPERIMENT. Currently a 2-line docstring, nothing else.",
      functions: [
        {
          signature: "EXPERIMENT: Experiment",
          description: "Experiment(name=\"exp_zapanese_zenglish_simple\", dataset=DATASET, format=FORMAT, models=MODELS, train=TRAIN, seeds=SEEDS, metrics=(TOKEN_ACCURACY, EXACT_MATCH)).",
          example_input: "len(EXPERIMENT.runs()), EXPERIMENT.runs()[9].slug",
          example_output: '36, "gpt2-2l2h256d-s43"',
        },
      ],
    },
    {
      path: "src/training/exp_zapanese_zenglish_simple/run.py", group: "training_experiment", kind: "code", status: "planned",
      description: "Thin argparse wrapper around EXPERIMENT, the mirror of the grammar experiment's run.py. One array task = one index into EXPERIMENT.runs().",
      functions: [
        {
          signature: "cmd_list() -> None  /  cmd_train(index: int, out: Path) -> Path  /  cmd_eval(slug: str, step: int, out: Path) -> list[dict]  /  cmd_upload(slug: str, private: bool) -> list[str]  /  main(argv: list[str] | None = None) -> None",
          description: "Subcommands: list (index -> slug); train --index N [--out DIR] (calls train.train_run); eval --slug S --step N (re-runs evaluate + aggregate on a saved checkpoint); upload --slug S [--private] (upload_hf.upload_model into collection translation-syntax-exp_zapanese_zenglish_simple-125000). Default DIR is this folder's artifacts/.",
          example_input: "sbatch --array=0-35 slurm/run_array.sbatch src/training/exp_zapanese_zenglish_simple/run.py train --index $SLURM_ARRAY_TASK_ID",
          example_output: "36 jobs; job 0 writes artifacts/gpt2-2l2h256d-s42/, job 35 writes artifacts/gpt2-6l8h256d-s45/",
        },
      ],
    },
    {
      path: "src/training/exp_zapanese_zenglish_simple/README.md", group: "training_experiment", kind: "doc", status: "exists",
      description: "Research question, hypothesis (OOD frame generalisation implies a hierarchical algorithm), risks and methods for this experiment. Human-readable mirror of what experiment.py binds; src/training/DESIGN.md section 3 is the normative spec.",
      functions: [],
    },
    {
      path: "src/training/exp_zapanese_zenglish_simple/RESULTS.md", group: "training_experiment", kind: "doc", status: "stub",
      description: "Empty until the grid has run. To be filled from artifacts/*/metrics.csv: the checkpoint where dev saturates, per-frame OOD accuracy, and an error taxonomy per frame (a group-by over the (step, subset, task, frame_id) rows).",
      functions: [],
    },
    {
      path: "src/training/exp_zapanese_zenglish_simple/artifacts/", group: "training_experiment", kind: "data", status: "planned",
      description: "gitignored outputs, one folder per run slug, written by train.train_run; staged here before upload to the HF collection translation-syntax-exp_zapanese_zenglish_simple-125000. About 20 MB per checkpoint x 13 x 36 runs = ~9.5 GB.",
      functions: [],
      files: [
        { name: "<slug>/run_config.json",                       description: "The launch record: full RunSpec (model, train, seed, experiment name) plus the dataset setup; also the wandb config." },
        { name: "<slug>/checkpoints/step010000/ ... step125000/", description: "HF save_pretrained directories (config.json from ModelConfig.to_hf, weights, tokenizer.json); 13 per run including the final step." },
        { name: "<slug>/decodes/step001000.csv ...",             description: "Greedy decodes of every SELECT and REPORT prompt at each eval: subset, task, frame_id, source, reference, prediction." },
        { name: "<slug>/metrics.csv",                           description: "aggregate() rows keyed by (step, subset, task, frame_id): n, token_accuracy, exact_match, and per-segment losses." },
      ],
    },

    // ---------------------------------------------------------------- external (train extra)
    {
      path: "torch", group: "training_external", kind: "external", status: "planned",
      description: "Tensors, AdamW, LR schedulers, manual_seed. Installed by uv sync --extra train (extra not yet declared in pyproject.toml).",
      functions: [],
    },
    {
      path: "transformers", group: "training_external", kind: "external", status: "planned",
      description: "GPT2Config (from ModelConfig.to_hf), GPT2LMHeadModel, save_pretrained / from_pretrained, PreTrainedTokenizerFast for the word-level tokenizer.json.",
      functions: [],
    },
    {
      path: "wandb", group: "training_external", kind: "external", status: "planned",
      description: "wandb.init(project, group, job_type, name, config=run_config.json + its path); one log call per eval.",
      functions: [],
    },
  ],

  edges: [
    // engine
    { from: "src/grammar/generate_frames.py", to: "src/grammar/grammar.py", kind: "import" },
    { from: "src/grammar/generate_frames.py", to: "src/grammar/splits.py", kind: "import" },
    { from: "src/grammar/generate_frames.py", to: "src/grammar/zapanese_zenglish_simple/cfg.py", kind: "dynamic" },
    { from: "src/grammar/generate_frames.py", to: "src/grammar/zapanese_zenglish_simple/lexicon.py", kind: "dynamic" },
    { from: "src/grammar/generate_frames.py", to: "src/grammar/zapanese_zenglish_simple/splits.py", kind: "dynamic" },
    // experiment data-as-code
    { from: "src/grammar/zapanese_zenglish_simple/cfg.py", to: "src/grammar/grammar.py", kind: "import" },
    { from: "src/grammar/zapanese_zenglish_simple/lexicon.py", to: "src/grammar/grammar.py", kind: "import" },
    { from: "src/grammar/zapanese_zenglish_simple/splits.py", to: "src/grammar/splits.py", kind: "import" },
    { from: "src/grammar/zapanese_zenglish_simple/run.py", to: "src/grammar/generate_frames.py", kind: "import" },
    { from: "src/grammar/zapanese_zenglish_simple/run.py", to: "src/upload/upload_hf.py", kind: "import" },
    { from: "src/grammar/zapanese_zenglish_simple/run.py", to: "src/grammar/zapanese_zenglish_simple/cfg.py", kind: "import" },
    { from: "src/grammar/zapanese_zenglish_simple/run.py", to: "src/grammar/zapanese_zenglish_simple/lexicon.py", kind: "import" },
    { from: "src/grammar/zapanese_zenglish_simple/run.py", to: "src/grammar/zapanese_zenglish_simple/splits.py", kind: "import" },
    { from: "src/grammar/zapanese_zenglish_simple/frames/", to: "src/grammar/zapanese_zenglish_simple/run.py", kind: "reads" },
    { from: "tests/test_zapanese_zenglish_simple.py", to: "src/grammar/zapanese_zenglish_simple/cfg.py", kind: "import" },
    { from: "tests/test_zapanese_zenglish_simple.py", to: "src/grammar/zapanese_zenglish_simple/stimuli_examples/Japanese RC Stimuli - RC Frames with Stimuli.csv", kind: "reads" },
    // upload
    { from: "src/upload/upload_hf.py", to: "huggingface_hub", kind: "import" },
    // tests
    { from: "tests/test_grammar.py", to: "src/grammar/grammar.py", kind: "import" },
    { from: "tests/test_splits.py", to: "src/grammar/splits.py", kind: "import" },
    { from: "tests/test_generate_frames.py", to: "src/grammar/generate_frames.py", kind: "import" },
    { from: "tests/test_generate_frames.py", to: "src/grammar/grammar.py", kind: "import" },
    { from: "tests/test_generate_frames.py", to: "src/grammar/splits.py", kind: "import" },
    { from: "tests/test_upload_hf.py", to: "src/upload/upload_hf.py", kind: "import" },
    { from: "tests/toy_experiment/", to: "src/grammar/grammar.py", kind: "import" },
    { from: "tests/toy_experiment/", to: "src/grammar/splits.py", kind: "import" },
    { from: "tests/test_grammar.py", to: "tests/toy_experiment/", kind: "import" },
    { from: "tests/test_generate_frames.py", to: "tests/toy_experiment/", kind: "dynamic" },
    // Hub dataset = the uploaded frames/filled/
    { from: "hf://datasets/kylelovesllms/zapanese_zenglish_simple-filled", to: "src/grammar/zapanese_zenglish_simple/frames/", kind: "reads" },

    // ================================================================ ROW 2: src/training (PLANNED)
    // engine
    { from: "src/training/model.py", to: "transformers", kind: "import" },
    { from: "src/training/data.py", to: "src/grammar/splits.py", kind: "import" },
    { from: "src/training/data.py", to: "src/grammar/grammar.py", kind: "import" },
    { from: "src/training/data.py", to: "huggingface_hub", kind: "import" },
    { from: "src/training/metrics.py", to: "src/training/data.py", kind: "import" },
    { from: "src/training/metrics.py", to: "torch", kind: "import" },
    { from: "src/training/experiment.py", to: "src/training/model.py", kind: "import" },
    { from: "src/training/experiment.py", to: "src/training/data.py", kind: "import" },
    { from: "src/training/experiment.py", to: "src/training/metrics.py", kind: "import" },
    { from: "src/training/train.py", to: "src/training/model.py", kind: "import" },
    { from: "src/training/train.py", to: "src/training/data.py", kind: "import" },
    { from: "src/training/train.py", to: "src/training/metrics.py", kind: "import" },
    { from: "src/training/train.py", to: "src/training/experiment.py", kind: "import" },
    { from: "src/training/train.py", to: "torch", kind: "import" },
    { from: "src/training/train.py", to: "transformers", kind: "import" },
    { from: "src/training/train.py", to: "wandb", kind: "import" },
    // experiment data-as-code
    { from: "src/training/exp_zapanese_zenglish_simple/models.py", to: "src/training/model.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/dataset.py", to: "src/training/data.py", kind: "import" },
    // the single-source-of-truth dependency: training imports the grammar experiment, never restates it
    { from: "src/training/exp_zapanese_zenglish_simple/dataset.py", to: "src/grammar/zapanese_zenglish_simple/splits.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/dataset.py", to: "src/grammar/zapanese_zenglish_simple/lexicon.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/dataset.py", to: "src/grammar/zapanese_zenglish_simple/cfg.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/dataset.py", to: "hf://datasets/kylelovesllms/zapanese_zenglish_simple-filled", kind: "reads" },
    { from: "src/training/exp_zapanese_zenglish_simple/training.py", to: "src/training/model.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/experiment.py", to: "src/training/experiment.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/experiment.py", to: "src/training/metrics.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/experiment.py", to: "src/training/exp_zapanese_zenglish_simple/models.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/experiment.py", to: "src/training/exp_zapanese_zenglish_simple/dataset.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/experiment.py", to: "src/training/exp_zapanese_zenglish_simple/training.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/run.py", to: "src/training/exp_zapanese_zenglish_simple/experiment.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/run.py", to: "src/training/train.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/run.py", to: "src/training/metrics.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/run.py", to: "src/upload/upload_hf.py", kind: "import" },
    { from: "src/training/exp_zapanese_zenglish_simple/artifacts/", to: "src/training/exp_zapanese_zenglish_simple/run.py", kind: "reads" },
    { from: "src/training/exp_zapanese_zenglish_simple/RESULTS.md", to: "src/training/exp_zapanese_zenglish_simple/artifacts/", kind: "reads" },
  ],
};
