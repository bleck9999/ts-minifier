takes tsv3 scripts and makes them smaller  
mainly useful for embedding them at compile time into te

```
usage: main.py [-h] [-d [D]] [--replace-functions | --no-replace-functions] source [source ...]

positional arguments:
  source                source files to minify

optional arguments:
  -h, --help            show this help message and exit
  -d [D]                destination folder for minified scripts default: ./
  --replace-functions, --no-replace-functions
                        if false, warn if functions are reused instead of replacing them default: true
```
