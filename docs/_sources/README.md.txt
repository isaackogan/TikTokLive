## How To Build

1. Complete commands:

```shell
**cd docs

sphinx-apidoc --ext-autodoc --force -o  . ../TikTokLive ../TikTokLive/proto/tiktok_schema_pb2.py

.\make html
```

3. Move generated sphinx `/sphinx/_build/html` folder to root, rename to "docs"
4. Add `.nojekyll` file to new docs folder

Alernatively: sphinx-apidoc --ext-autodoc --force -o "." "../TikTokLive" "../TikTokLive/proto/tiktok_schema_pb2.py" ; Remove-Item ".\_build" -Recurse ; .\make html ; Remove-Item -Path "..\docs" -Recurse ; Rename-Item "
.\_build\html" "docs"; Move-Item -Path ".\_build\docs" -Destination "..\"