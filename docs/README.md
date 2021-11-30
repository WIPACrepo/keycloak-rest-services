# Documentation

## Editing

After cloning the repo, you should set up a local environment:

```bash
./setupenv.sh
. env/bin/activate
pip install mkdocs mkdocs-material
mkdocs serve
```

This should start a live preview at [http://localhost:8000](http://localhost:8000).
It should automatically update whenever you save any file in the `docs`
directory.

The Markdown source exists in `docs` and uses [mkdocs](https://www.mkdocs.org/).

### Adding a Page

Add your page in [markdown format](https://www.mkdocs.org/user-guide/writing-your-docs/#writing-with-markdown)
inside the `docs` directory. If adding an image, the url should be relative.

## Publishing

There is a GitHub action configured to deploy any changes.
Either commit directly to `master` or go through the PR process and your
changes will appear a minute or two after the merge.
