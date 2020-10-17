# Markdown To Html

This is a simple markdown to html converter.

### Requirements

* Python3, that's it!

### (Optional) Configuration

Create your own `config.py` file, mimicking the format of `example_config.py` to use your preferred css, etc. The script will load the example configuration if no `config.py` is present.

### ToDo:

- [x] There's a bug currently where text inside inlined codeblocks aka `these` would still be processed by other filters...
- [ ] Need to more properly filter emphasis and bold (via looking for `['\n__', '\n**']` and then checking for `['__ ', '** ']`
