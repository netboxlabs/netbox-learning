# Learning repo dev

The README.md in the root of this repo is generated from a Jinja2 template, this is to allow for inclusion of dynamic elements. Such as  blog posts and OSS releases.

To setup up your dev environment;

```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r .learning-meta/requirements.txt
```

Generate the README manually locally:

```python
.learning-meta/regenerate.py
```

The README is auto-committed by Github when...

- A push is made to `.learning-meta/**` on the `develop` branch
- Once a day at 3am.