takes tsv3 scripts and makes them smaller  
mainly useful for embedding them at compile time into te

currently the optimisations performed are:
- removing excess whitespace
- removing comments (except REQUIRE statements)
- detecting reused string literals
- detecting (or automatically aliasing) reused standard library functions
- detecting (or automatically renaming) long variable or user function names

as a side note: i consider the automatic replacement *mostly* stable. 
however, mostly is not always and tegrascript is a very cursed language so 
if you do end up using it and experiencing issues i'd appreciate it if you either
opened an issue on this repository with details of what went wrong or pinging me
(bleck9999#9797) in [meme's server](https://discord.gg/nhvWK2Q)
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
