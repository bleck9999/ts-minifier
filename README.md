takes tsv3 scripts and makes them smaller  
mainly useful for embedding them at compile time into te

currently the optimisations performed are:
- removing excess whitespace
- removing comments (except REQUIRE statements)
- detecting reused string literals
- detecting (or automatically aliasing) reused standard library functions
- detecting (or automatically renaming) long variable or user function names
```
usage: main.py [-h] [-d [D]] [--auto-replace] source [source ...]

positional arguments:
  source          source files to minify

optional arguments:
  -h, --help      show this help message and exit
  -d [D]          destination folder for minified scripts
                  default: ./
  --auto-replace  automatically replace reused functions and variables instead of just warning
                  and attempt to generate shorter names for reused variables 
                  default: false
```
