import argparse


def minify(script: str):
    # currently ts does not seem to allow ''
    # (https://github.com/suchmememanyskill/TegraExplorer/blob/tsv3/source/script/parser.c#L173)
    # im fine with that, it makes doing this a lot easier
    minified = ""
    strings = script.split(sep='"')
    part = 0
    while part < len(strings):
        # done: clear all comments that don't have a REQUIRE
        # done: strip whitespace
        # TODO: shrink user defined names

        # in theory all the even numbered indexes should be outside quotes, so we ignore any parts with an odd index
        if part % 2 == 1:
            minified += f'"{strings[part]}"'

        else:
            for line in strings[part].split(sep='\n'):
                if '#' in line:
                    if "REQUIRE" in line:
                        minified += line + '\n'  # leave REQUIREs unmodified
                        # comments are terminated by a newline so we need to add one back in
                    else:
                        # the comment is just a comment and can be ignored
                        pass
                else:
                    line = line.replace(' ', '').replace('\t', '')  # newlines should already be taken care of



        part += 1

    return minified


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
