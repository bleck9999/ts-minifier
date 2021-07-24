import argparse


def minify(script: str):
    # currently ts does not seem to allow ''
    # (https://github.com/suchmememanyskill/TegraExplorer/blob/tsv3/source/script/parser.c#L173)
    # im fine with that, it makes doing this a lot easier
    strings = script.split(sep='"')
    part = 0
    while part < len(strings):


        # in theory all the even numbered indexes should be outside quotes, so we can ignore any parts with an odd index
        part += 2



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
