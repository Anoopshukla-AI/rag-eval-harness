# AGENTS.md Addendum — Anti-Mocking Rules

Append this section to the top-level `AGENTS.md` in every project. It exists because agents default to creating mock/stub files when a real dependency isn't immediately found, and this can happen silently.

## Rule: No Silent Mocking

- **Never** create a mock, stub, dummy, or placeholder implementation of a dependency (a module, API, database, or function) without explicitly telling me you are doing so, in plain language, before or as you do it.
- If a required module or function cannot be found (e.g., `rag_pipeline`, a database connection, an external API), **stop and report it** rather than inventing a working-looking substitute. Say exactly: "I could not find X. Here are the options: [search further / ask you where it lives / create an explicit, clearly-labeled stub]."
- If you do create a stub because I've explicitly approved it, it must:
  1. Be placed in a clearly named location (e.g., `_stubs/` or a file with `_stub` in the name), never blended into files that look like production code.
  2. Contain a loud comment at the top: `# STUB — NOT REAL. Replace before using results for anything real.`
  3. Be listed in a `STUBS.md` file at the project root, one line per stub, describing what it fakes and what needs to replace it.
- Before reporting any test, eval, or run as "successful" or "passing," confirm out loud whether real dependencies were used or stubs were used. Never let a passing result imply real-system validation if it was actually run against a stub.

## Rule: Search Before You Stub

Before creating any mock, first:
1. Search the current workspace and any linked folders/repos for an existing implementation.
2. If working across multiple folders in one Antigravity Project, check every linked folder, not just the active one.
3. Ask me directly: "Where does your real RAG pipeline / API / database live? I couldn't find it in this workspace."

Only create a stub after this search comes up empty AND I've confirmed a stub is acceptable for now.

## Rule: Flag Divergence From Real Results

If a stub was used to get a script running, explicitly say: "This ran successfully, but against a stub, not your real system. These numbers are not real evaluation results — they only prove the harness code itself works." This distinction must never be left implicit.
