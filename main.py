import argparse

stdlib_funcs = ['while', 'print', 'println', 'mountsys', 'mountemu', 'readsave', 'exit', 'break', 'dict',
                'setpixel', 'readdir', 'filecopy', 'mkdir', 'memory', 'ncatype', 'pause', 'color', 'menu',
                'emu', 'clear', 'timer', 'deldir', 'fsexists', 'delfile']  # if is not included on purpose
sub_funcs = {'while': "_h", 'print': "_p", 'println': "_l", 'mountsys': "_s", 'mountemu': "_e", 'readsave': "_r",
             'exit': "_q", 'break': "_b", 'dict': "_d", 'setpixel': "_y", 'readdir': "_i", 'filecopy': "_c",
             'mkdir': "_k",
             'memory': "_m", 'ncatype': "_n", 'pause': "_w", 'color': "_a", 'menu': "__", 'emu': "_u", 'clear': "_x",
             'timer': "_t", 'deldir': "_g", 'fsexists': "_f", 'delfile': "_z"}
replace_functions = True


def minify(script: str):
    # currently ts does not seem to allow 's to mark a quote
    # (https://github.com/suchmememanyskill/TegraExplorer/blob/tsv3/source/script/parser.c#L173)
    # im fine with that, it makes doing this a lot easier
    strings = script.split(sep='"')
    part = 0
    requires = ""
    mcode = ""
    stl_counts = {}.fromkeys(stdlib_funcs, 0)
    while part < len(strings):
        # maybe in future it'll shrink user defined names
        # dont hold out hope for that because `a.files.foreach("b") {println(b)}` is valid syntax
        # and i dont have the skill or patience to deal with that

        # in theory all the even numbered indexes should be outside quotes, so we ignore any parts with an odd index
        if part % 2 == 1:
            mcode += f'"{strings[part]}"'
        else:
            for line in strings[part].split(sep='\n'):
                if '#' in line:
                    if "REQUIRE" in line:
                        requires += line + '\n'  # leave REQUIREs unmodified
                        # comments are terminated by a newline so we need to add one back in
                    else:
                        # the comment is just a comment and can be ignored
                        pass
                else:
                    for s in stdlib_funcs:
                        stl_counts[s] += line.count(f'{s}(')
                    mcode += line.replace('\t', '') + ' '

        part += 1

    # tsv3 is still an absolute nightmare
    # so spaces have a couple edge cases
    # 1. the - operator which requires space between the right operand
    # yeah that's right only the right one
    # thanks meme
    # 2. between 2 letters
    inquote = False
    mmcode = ""
    index = 0
    newline = list(mcode)
    while index < (len(mcode) - 3):
        sec = mcode[index:index + 3]
        if not inquote and sec[1] == '"':
            inquote = True
        elif inquote and sec[1] == '"':
            inquote = False
        if (sec[1] == ' ') and not inquote:
            if sec[0].isalpha() and sec[2].isalpha():
                pass
            elif sec[0] == '-' and sec[2].isnumeric():
                pass
            else:
                newline[index + 1] = ''
        index += 1
    mmcode += ''.join(newline).strip()

    for func in stdlib_funcs:
        # space saved here is given by n * (len(func) - len(min_func)) - (len(min_func)+1 + len(func))
        # as such with one usage space is always lost (len(func)-2 is never > len(func)+3) so dont even try
        if stl_counts[func] >= 2:
            savings = stl_counts[func] * (len(func) - 2) - (len(func) + 3)
            print(f"Replacing all {stl_counts[func]} usages of {func} would save {savings}bytes")
            if (savings < 0) or not replace_functions:
                print("Savings negative or automatic replacement disabled, continuing")
                continue
            func_min = sub_funcs[func]  # now here we have to assume nobody is using any of our substitute vars
            # should be a pretty safe assumption but knowing for sure would require about the same amount of effort
            # as it would to replace all user defined variables
            mmcode = mmcode.replace(f"{func}(", f"{func_min}(")  # this will replace inside strings as well deal with it
            mmcode = f"{func_min}={func}\n" + mmcode
            # a space isn't any shorter than \n so why not use \n

    return requires + mmcode.strip()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Minify tsv3 scripts, useful for embedding")
    parser.add_argument("source", type=str, nargs='+', help="source files to minify")
    parser.add_argument("-d", type=str, nargs='?', help="destination folder for minified scripts"
                                                        "\ndefault: ./", default='./')
    parser.add_argument("--replace-functions", action=argparse.BooleanOptionalAction,
                        help="if false, warn if functions are reused instead of replacing them\ndefault: true")

    args = parser.parse_args()
    files = args.source
    dest = args.d[:-1] if args.d[-1] == '/' else args.d
    replace_functions = args.replace_functions if args.replace_functions is not None else True

    for file in files:
        print(f"Minifying {file}")
        with open(file, 'r') as f:
            r = minify(f.read())
        file = file.split(sep='.')[0]
        f = open(f"{dest}/{file}_min.te", 'w')
        f.write(r)
