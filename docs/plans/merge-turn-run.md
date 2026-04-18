# Plan: Merge `Turn` into `Run`

## Background

`Turn` is a thin container dataclass with two fields:

```python
@dataclass
class Turn:
    run: Run | None
    function_calls: list[FunctionCall]
```

`Run` is the substantive entity (~25 fields) that tracks the full lifecycle of an LLM interaction. The 1:1 relationship (each `Turn` holds 0 or 1 `Run`) makes the wrapper feel redundant — `Turn` mostly exists to carry `function_calls` alongside a `Run`.

---

## Proposed Changes

### 1. Move `function_calls` into `Run`

Add `function_calls: list[FunctionCall]` to `Run` in `src/margarita/agent/entities/run.py`.

```python
# Before (Turn held this)
function_calls: list[FunctionCall] = field(default_factory=list)
```

This is the only unique data `Turn` carries that `Run` does not.

### 2. Handle the "empty slot" case

Currently a `Turn` is created with `run=None` before an LLM query begins. With the merge, `ExecutionModel` needs an equivalent placeholder. Two options:

**Option A — Allow pending `Run`:** A `Run` starts with `status=RunStatus.PENDING` and no prompt. This already exists on `Run`.

**Option B — Optional sentinel:** `ExecutionModel.current_run` returns `None` until a run is started (same behavior as now, just without a wrapping `Turn`).

Option B is cleaner — the `None` case already exists in `current_run`'s return type.

### 3. Rename `ExecutionModel.turns` → `runs`

```python
# Before
self.turns: list[Turn] = []

# After
self.runs: list[Run] = []
```

Update all properties and callers:

| Before | After |
|--------|-------|
| `self.turns` | `self.runs` |
| `self.turns_with_runs` | `self.runs` (all runs; property removed) |
| `self.current_turn` | `self.current_run` (already exists) |
| `turn.run` | the `Run` directly |

### 4. Update `start_turn` / `start_run`

Collapse two methods into one:

```python
def start_run(self, name: str, prompt: str, ...) -> Run:
    run = Run(name=name, prompt=prompt, function_calls=[], ...)
    self.runs.append(run)
    return run
```

The old `start_turn()` call sites that created an empty `Turn` are removed.

### 5. Update sub-execution mirroring

`_MirroredTurnList` in `exec.py` mirrors child turns into the parent's `turns` list. Replace with `_MirroredRunList` pointing at `runs`.

### 6. Update UI

`app.py` iterates `turns_with_runs` to mount `RunWidget`s. After the merge it iterates `runs` directly — no filter needed.

`run_widget/` components already receive a `Run` object; no changes needed inside them.

---

## Files Affected

| File | Change |
|------|--------|
| `src/margarita/agent/entities/run.py` | Add `function_calls` field |
| `src/margarita/agent/core/agents/models.py` | Remove `Turn`, merge `start_turn`/`start_run`, rename `turns` → `runs` |
| `src/margarita/agent/core/agents/operations/execute_agent_operation.py` | Update call sites |
| `src/margarita/agent/libs/copilot/copilot_agent.py` | Update call sites |
| `src/margarita/agent/core/agents/plugins/exec.py` | Replace `_MirroredTurnList` |
| `src/margarita/agent/core/agents/plugins/console.py` | Update references |
| `src/margarita/agent/core/agents/plugins/run_agent.py` | Update references |
| `src/margarita/agent/app/ui/app.py` | Replace `turns_with_runs` with `runs` |
| `src/margarita/agent/core/interfaces/query_service.py` | Update if `Turn` appears in interface |
| `tests/` | Update any `Turn` references |

---

## Devil's Advocate: Reasons NOT to Merge

### 1. `function_calls` and `tool_calls` are genuinely different things

`Turn.function_calls` are **local Python function calls** from `@effect func` template execution — they happen *outside* of any LLM interaction. `Run.tool_calls` are **LLM-issued tool invocations** that occur *inside* an LLM interaction.

Merging them into `Run` blurs the boundary between "what the template engine did" and "what the LLM decided to do." If a `function_call` happens before or after a `Run` starts, attaching it to a `Run` is semantically wrong — it implies the LLM caused it.

### 2. The empty-Turn pattern exists for a reason

`Turn` is created before `start_run` is called. This "slot reservation" lets the system track that *something is about to happen* — useful for the UI to reserve space and for plugins to attach pre-run metadata. Collapsing this means the first thing that exists is a fully-started `Run`, which removes the staging window.

### 3. One Turn could legitimately hold multiple Runs in the future

Right now it's 1:1, but the design leaves room for a Turn to represent one user interaction that triggers multiple LLM sub-calls (e.g., retry on error, or parallel calls). The field is `run: Run | None`, not a list — but the Turn/Run split keeps the option open without structural surgery. Merging now forecloses that evolution path.

### 4. `Run` is already large; adding more makes it worse

At ~25 fields, `Run` is already a god object. Adding `function_calls` (plus whatever else `Turn` implicitly anchors) makes it larger. The merge solves a naming/indirection problem but trades it for a cohesion problem.

### 5. `turn_id` on `Run` suggests intentional separation

`Run` already has a `turn_id: str | None` field (currently unused). This was added deliberately to let a `Run` reference its parent `Turn` — indicating the author intended them to remain distinct and relatable by ID, not merged.

### 6. Sub-execution mirroring is coupled to the Turn boundary

`_MirroredTurnList` in `exec.py` uses Turn as the unit of mirroring between parent and child `ExecutionModel`s. This works cleanly because a Turn is a discrete, stable wrapper. Mirroring `Run` objects directly is equivalent in theory, but `Run` mutates heavily during its lifecycle (status, tokens, content blocks), making the mirroring semantics more fragile.

### 7. The rename is noisy, the benefit is small

The practical gain is removing one level of `.run` indirection (`turn.run.field` → `run.field`) and deleting ~10 lines of `Turn` dataclass code. The cost is touching ~10 files and rewriting the sub-execution mirroring logic. The risk/reward ratio is unfavorable unless `Turn` is actively causing bugs or confusion.

---

## Verdict

The merge is conceptually clean but the **`function_calls` semantic mismatch** (item 1) and the **sub-execution mirroring coupling** (item 6) are real concerns. A lighter alternative: keep `Turn` but give it a clearer name (`ExecutionSlot`, `TurnSlot`) and document the Turn/Run distinction explicitly. This preserves the design intent without a risky refactor.
