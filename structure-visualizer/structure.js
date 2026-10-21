// Codebase structure data for codebase-structure.html.
//
// This is the single place to edit when files, imports, or function signatures change.
// Loaded via <script src="structure.js"> so the page works from file:// without a server.
//
// node.kind   : "code" | "data" (paper emoji) | "doc" | "config" | "external"
// node.status : "exists" | "stub" (file exists, body not written) | "planned" (not created yet)
// edge        : {from, to, kind}  meaning  `from` imports / reads `to`.
//               kind: "import" (static import), "dynamic" (importlib at runtime), "reads" (data file)
//
// In the viewer, selecting a file shows its dependencies as red incoming arrows and the files
// that depend on it as green outgoing arrows.

window.CODEBASE = {
  groups: [
    { id: "grammar",    label: "src/grammar  (shared engine)" },
    { id: "experiment", label: "src/grammar/zapanese_zenglish_simple  (data-as-code)" },
    { id: "upload",     label: "src/upload" },
    { id: "tests",      label: "tests" },
    { id: "external",   label: "external packages" },
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
      path: "src/grammar/zapanese_zenglish_simple/cfg.py", group: "experiment", kind: "code", status: "planned",
      description: "NEXT STEP. Data only: the synchronous CFG as Rule instances (ternary flat rules; scrambling is one extra S rule) and the FRAME_IDS table mapping F01..F18 to metadata.",
      functions: [
        {
          signature: "RULES: tuple[Rule, ...]",
          description: "All rules. Scrambling = S -> NP_acc NP_nom V_t with perm (1, 2, 0).",
          example_input: "RULES[1]",
          example_output: 'Rule("S_trans_scr", "S", ("NP_acc", "NP_nom", "V_t"), (1, 2, 0), {"scrambled": True})',
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
      path: "src/grammar/zapanese_zenglish_simple/lexicon.py", group: "experiment", kind: "code", status: "planned",
      description: "NEXT STEP. Data only: N transitive verbs, N intransitive verbs, 2N nouns, case markers. Verb classes disjoint.",
      functions: [
        {
          signature: "LEXICON: Lexicon",
          description: "The word lists.",
          example_input: 'LEXICON.words["V_i"]',
          example_output: '("swims", "dances", ...)',
        },
      ],
    },
    {
      path: "src/grammar/zapanese_zenglish_simple/splits.py", group: "experiment", kind: "code", status: "planned",
      description: "NEXT STEP. Data only: the frame-level split (train / ood_level1 / ood_level2) and filling-level split (train/dev, select/report) from the research journal and README.",
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
      path: "src/grammar/zapanese_zenglish_simple/run.py", group: "experiment", kind: "code", status: "stub",
      description: "NEXT STEP. Thin argparse wrapper: generate CSVs for this experiment and upload them to HF.",
      functions: [
        {
          signature: "main() -> None",
          description: "Subcommands: generate --out DIR ; upload --dir DIR [--private].",
          example_input: "uv run python src/grammar/zapanese_zenglish_simple/run.py generate --out data/zapanese_zenglish_simple",
          example_output: "CSV files written; table of row counts printed",
        },
      ],
    },
    {
      path: "src/grammar/zapanese_zenglish_simple/stimuli_examples/Japanese RC Stimuli - RC Frames with Stimuli.csv", group: "experiment", kind: "data", status: "exists",
      description: "Hand-written reference: the 18 frames with example fillings. Ground truth the real cfg.py will be tested against (next step).",
      functions: [],
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
  ],
};
