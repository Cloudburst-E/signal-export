# signal-export
[![cicd](https://github.com/carderne/signal-export/actions/workflows/cicd.yml/badge.svg)](https://github.com/carderne/signal-export/actions/workflows/cicd.yml)
[![PyPI version](https://badge.fury.io/py/signal-export.svg)](https://pypi.org/project/signal-export/)

**⚠️ WARNING: Because the latest versions of Signal Desktop protect the database encryption key, this tool currently only works on macOS and Linux.
Solutions for Windows will hopefully come soon from the community.
Discussion happening in [this thread](https://github.com/carderne/signal-export/issues/133).**

Export chats from the [Signal](https://www.signal.org/) [Desktop app](https://www.signal.org/download/) to Markdown and HTML files with attachments. Each chat is exported as an individual .md/.html file and the attachments for each are stored in a separate folder. Attachments are linked from the Markdown files and displayed in the HTML (pictures, videos, voice notes).

Currently this seems to be the only way to get chat history out of Signal!

Adapted from [mattsta/signal-backup](https://github.com/mattsta/signal-backup), which I suspect will be hard to get working now.

## Example
An export for a group conversation looks as follows:
```markdown
[2019-05-29, 15:04] Me: How is everyone?
[2019-05-29, 15:10] Aya: We're great!
[2019-05-29, 15:20] Jim: I'm not.
```

Images are attached inline with `![name](path)` while other attachments (voice notes, videos, documents) are included as links like `[name](path)` so a click will take you to the file.

This is converted to HTML at the end so it can be opened with any web browser. The stylesheet `.css` is still very basic but I'll get to it sooner or later.

## 🐧 Installation
1. Make sure you have Python installed.

2. Install this package:
If you want files to be uploaded directly to GCS, fill in values for environmental variables in `.local.env`, then run:
```bash
export $(cat .local.env | xargs)
```
Then pip install the package
```bash
pip install .
```

3. Then run the script!
```bash
sigexport ~/chat --overwrite --to-gcs

# or for Windows:
python -m sigexport C:\Temp\SignalExport --overwrite --to-gcs
```

## 🪟 Installation: Windows
If you need step-by-step instructions on things like enabling WSL2, please see the dedicated [Windows Installation](./INSTALLATION.md) instructions.

## 🚀 Usage
Please fully exit your Signal app before proceeding, otherwise you will likely encounter an `I/O disk` error, due to the message database being made read-only, as it was being accessed by the app.

See the full help info:
```bash
sigexport --help
```

Disable pagination on HTML:
```bash
sigexport --paginate=0 ~/signal-chats
```

List available chats and exit:
```bash
sigexport --list-chats
```

Export only the selected chats:
```bash
sigexport --chats=Jim,Aya ~/signal-chats
```

You can add `--source /path/to/source/dir/` if the script doesn't manage to find the Signal config location.
Default locations per OS are below.
The directory should contain a folder called `sql` with `db.sqlite` inside it.
- Linux: `~/.config/Signal/`
- macOS: `~/Library/Application Support/Signal/`
- Windows: `~/AppData/Roaming/Signal/`

You can also use `--old /previously/exported/dir/` to merge the new export with a previous one.
_Nothing will be overwritten!_
It will put the combined results in whatever output directory you specified and leave your previos export untouched.
Exercise is left to the reader to verify that all went well before deleting the previous one.

## Development
```bash
git clone https://github.com/carderne/signal-export.git
cd signal-export
rye sync --no-lock
```

Various dev commands:
```bash
rye fmt         # format
rye lint        # lint
rye run check   # typecheck
rye run test    # test
rye run sig     # run signal-export
```

## Similar things
- [signal-backup-decode](https://github.com/pajowu/signal-backup-decode) might be easier if you use Android!
- [signal2html](https://github.com/GjjvdBurg/signal2html) also Android only
- [sigtop](https://github.com/tbvdm/sigtop)
