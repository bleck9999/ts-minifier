import argparse


def minify(script: str):
    # currently ts does not seem to allow 's to mark a quote
    # (https://github.com/suchmememanyskill/TegraExplorer/blob/tsv3/source/script/parser.c#L173)
    # im fine with that, it makes doing this a lot easier
    strings = script.split(sep='"')
    part = 0
    requires = ""
    mcode = ""
    while part < len(strings):
        # maybe in future it'll shrink user defined names
        # dont hold out hope for that because `a.files.foreach("b") {println(b)}` is valid syntax
        # and i dont have the skill or patience to deal with that
        # though a suggestion that should be easier is aliasing functions that are used multiple times
        # like in firmwaredump.te

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
    while index < (len(mcode)-3):
        sec = mcode[index:index+3]
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
                newline[index+1] = ''
        index += 1
    mmcode += ''.join(newline)

    return requires + mmcode.strip()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Minify tsv3 scripts, useful for embedding")
    parser.add_argument("source", type=str, nargs='+', help="source files to minify")
    parser.add_argument("-d", type=str, nargs='?', help="destination folder for minified scripts", default='./')

    args = parser.parse_args()
    files = args.source
    dest = args.d[:-1] if args.d[-1] == '/' else args.d

    for file in files:
        print(f"Minifying {file}")
        with open(file, 'r') as f:
            r = minify(f.read())
        file = file.split(sep='.')[0]
        f = open(f"{dest}/{file}_min.te", 'w')
        f.write(r)
