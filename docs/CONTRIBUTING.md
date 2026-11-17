# Contributing

## How to Contribute

Issues are welcome: bug reports, questions and ideas, including new snippets or improvements to existing ones. Pull requests from outside contributors are not accepted for now: the maintainers write all changes themselves, so every change is written and reviewed by the maintainers. A pull request from outside may be closed without review. Open an issue instead.

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
