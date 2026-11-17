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

New snippets and improvements to existing ones are welcome as an issue or a pull request.

- **Proposing a snippet:** open an issue with the FileMaker function name, the trigger keyword you suggest and what the snippet should do (not the snippet text itself), following the guidelines below.
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

## For Maintainers

All snippet data is maintained in the CSV file `data/FileMaker_Functions_Alfred_Snippets.csv`; make additions and changes there.

### Regenerating the Alfred Bundle
If you are a maintainer, you can generate a new `.alfredsnippets` file by importing the updated CSV into an Alfred collection, exporting the collection, and committing the new binary file to the repository.
