# Release plan for Margarita

1. Make sure that all tests are passing format an linting are run
   ```bash
    make format
    make lint
    make test
   ```

2. Update the version number in pyproject.toml. Follow semantic versioning. Ask for clarification if you are unsure.
3. Update RELEASE_NOTES.md with the new version and changes in the following format:

# Release Notes - Margarita v<new_version>

**Release Date:** <date>

## 🎉 Overview

4. run mike to create a new versioned docs site:
   ```bash
   uv run mike deploy v<new_version> latest --update-aliases
   ```
5. Update the version number in all the install scripts
6. Commit all changes with a message like "Release vX.Y.Z".
7. Push the gh-pages branch to update the docs site:
   ```bash
   git checkout gh-pages
   git push origin gh-pages
   ```
8. Push the changes to the main branch with all tags:
   ```bash
   git push --follow-tags origin main
   ```
