# Contributing

## How to Contribute

Issues and pull requests are both welcome. For anything larger than a small fix,
open or comment on an issue first so we agree on the approach.

Sign off every commit with `git commit -s`. This adds a `Signed-off-by:` line
certifying the [Developer Certificate of Origin](https://developercertificate.org/):
you wrote the change or have the right to submit it under the licence in this
repository's `LICENSE` file, and your contribution comes under that licence. A
check confirms the sign-off on pull requests from outside contributors. Every
pull request gets review and must pass the required checks before a maintainer
merges it.

CodeRabbit (free open-source plan) may comment on pull requests. Its reviews are advice only and never required. On repositories with fewer than 10 stars it does not run on its own; comment `@coderabbitai review` to trigger it.

New snippets and improvements to existing ones are welcome as an issue or a pull request.

- **Proposing a snippet:** open an issue with the FileMaker function name, the trigger keyword you suggest and what the snippet should do, or edit the CSV file and open a pull request, following the guidelines below.
- **Writing a good issue:** see the [SureForgeTech contributing guide](https://github.com/SureForgeTech/.github/blob/main/CONTRIBUTING.md).
- **Security problems:** do not report them in a public issue; follow [SECURITY.md](../SECURITY.md).

## Guidelines for Snippets

### Keyword Naming Rules
- All snippet triggers **must** start with `;fm`.
- Keep the suffix short but descriptive (e.g., `;fmlet`, `;fmsub`).
- Use all lowercase for the trigger.

### Avoid Conflicts
- Before proposing a new snippet, check the existing list (or CSV) to ensure the trigger keyword isn't already in use.
- Avoid creating triggers that are extremely similar and might cause confusion.

### Prefer Canonical Syntax
- Snippets should use standard Claris FileMaker syntax exactly as it appears in the official documentation (e.g., matching capitalization and spacing).
- Include optional parameters enclosed in curly braces `{}` where appropriate, mimicking FileMaker's calculation dialog auto-complete format.

## Maintaining the Snippets & Bundle

All snippet data is maintained in the CSV file `data/FileMaker_Functions_Alfred_Snippets.csv`; make additions and changes there.

### Regenerating the Alfred Bundle
The `.alfredsnippets` bundle is generated directly from the source CSV using `tools/build-bundle.py`:

```bash
# Validate CSV and regenerate FileMaker_Functions.alfredsnippets:
python tools/build-bundle.py

# Verify CSV and bundle parity (enforced in CI):
python tools/build-bundle.py --check
```

Always stage and commit both `data/FileMaker_Functions_Alfred_Snippets.csv` and `FileMaker_Functions.alfredsnippets` together in your pull request so the CI parity check succeeds.

The script automatically:
- Validates that Name, Category, and Snippet are not empty.
- Verifies that trigger keywords start with `;fm`, are lowercase, and are unique.
- Preserves existing UIDs for unchanged snippets so Alfred snippet collections update cleanly in place without duplicates.
