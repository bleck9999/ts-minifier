import argparse
import re

# if is not included because it's already 2 characters
sub_funcs = {'while': "_h", 'print': "_p", 'println': "_l", 'mountsys': "_s", 'mountemu': "_e", 'readsave': "_r",
             'exit': "_q", 'break': "_b", 'dict': "_d", 'setpixel': "_y", 'readdir': "_i", 'copyfile': "_c",
             'mkdir': "_k", 'ncatype': "_n", 'pause': "_w", 'color': "_a", 'menu': "__", 'emu': "_u",
             'clear': "_x", 'timer': "_t", 'deldir': "_g", 'fsexists': "_f", 'delfile': "_z", "copydir": "c_",
             "movefile": "_v", "payload": "_j", "readfile": "_o", "writefile": "_W", "setpixels": "_Y", "printpos": "_P",
             "emmcread": "_E", "emmcwrite": "_F", "emummcread": "_R", "emummcwrite": "_S", "escapepath": "_X",
             "combinepath": "_A", "cwd": "_D", "power": "_O", "fuse_patched": "_M", "fuse_hwtype": "_N"}
replace_functions = False


class Code:
    def __init__(self, strings, comments, script):
        bounds = []
        counter = 0
        strings_comments = sorted(strings + comments)
        for val in strings_comments:
            if counter and (bounds[counter - 1] == val[0]):
                bounds[counter - 1] = val[1]
            else:
                bounds += [val[0], val[1]]
                counter += 2
        bounds.append(len(script))
        code = []
        i = 2
        while i < len(bounds):
            code.append((bounds[i - 1], bounds[i], script[bounds[i - 1]:bounds[i]]))
            i += 2
        self.sections = sorted(strings_comments + code)
        self.strings = strings
        self.comments = comments
        self.code = code
        self.string_comments = strings_comments

    def getafter(self, ch: int):
        for strcom in self.string_comments:
            if strcom[0] >= ch:
                return strcom
        return None

    def nextch(self, ch: int, reverse: bool):
        rawcontent = "".join([x[2] for x in self.sections])
        commented = False
        while x := ch or True:
            if reverse:
                x -= 1
            else:
                x += 1

            if rawcontent[x] not in [' ', '\n'] and not commented:
                return rawcontent[x]
            elif rawcontent[x] == '#':
                commented = True
            elif rawcontent[x] == '\n' and commented:
                commented = False


def isidentifier(s: str):
    for c in s:
        if not ((ord(c) >= 97) and (ord(c) <= 122)) or (ord(c) == 95):
            return False
    return True


def hascomment(s: str):
    quoted = False
    for c in range(len(s)):
        if s[c] == '"':
            quoted = not quoted
        if s[c] == '#' and not quoted:
            return c
    return None


def parser(script: str):
    # step 1: separate comments
    # step 2: separate strings
    # step 3: actually parse and shit
    comments = []  # [(start, end, content)]
    strings = []
    commented = False
    quoted = False
    strstart = -1
    commentstart = -1
    for c in range(len(script)):
        if script[c] == '#' and not quoted:
            commented = True
            commentstart = c
        elif (script[c] == '\n' and not quoted) and commented:
            comments.append((commentstart, c+1, script[commentstart:c+1]))
            commented = False
        elif script[c] == '"' and not commented:
            if not quoted:
                strstart = c
                quoted = True
            else:
                strings.append((strstart, c+1, script[strstart:c+1]))
                quoted = False

    script = Code(strings, comments, script)

    # guess i should do a breakdown of step 3
    # we need to be able to read:
    #    variable creation | a = 15, array.foreach("a")
    #    defining a function | funcname = {function body}
    #    calling a function | funcname(arguments) for stdlib functions, funcname(<optional> any valid ts) for user defined
    #    member calling | object.member(possible args)
    #        we don't need to check if it's valid syntax or not so we dont need to know the type of object that's nice
    #        this can actually be chained which is pretty annoying
    #    operators? i dont think it actually matters to us
    #
    # other notes:
    #   whitespace is only required between valid identifiers/numbers and between the minus operator and rvalue
    #   or the newline at the end of a comment thus it cannot reliably be used to separate statements

    userobjects = []
    usages = {}
    ismember = False
    for item in script.code:
        sec = item[2]
        start = len(sec)+1
        for ch in range(len(sec)):
            if isidentifier(sec[ch]) and start > ch and not ismember:
                start = ch
            elif sec[ch] == '=':
                identifier = sec[start:ch]
                if identifier in userobjects:
                    usages[identifier] += 1  # it's been declared before, so this is a usage
                else:
                    isfunc = script.nextch(ch+item[0], False) == '{'
                    userobjects.append((identifier, "func" if isfunc else "var"))
                    usages[identifier] = 0   # declaration is not a usage
                    start = len(sec)+1
            elif sec[ch] == '.':
                ismember = True




def minify(script: str):
    # currently ts does not seem to allow 's to mark a quote
    # (https://github.com/suchmememanyskill/TegraExplorer/blob/tsv3/source/script/parser.c#L173)
    # im fine with that, it makes doing this a lot easier
    # strings = script.split(sep='"')
    str_reuse = {}
    requires = ""
    mcode = ""
    stl_counts = {}.fromkeys(sub_funcs, 0)
    # while part < len(strings):
    for line in script.split(sep='\n'):
        # maybe in future it'll shrink user defined names
        # dont hold out hope for that because `a.files.foreach("b") {println(b)}` is valid syntax
        # and i dont have the skill or patience to deal with that

        # # in theory all the even numbered indexes should be outside quotes, so we ignore any parts with an odd index
        # if part % 2 == 1:
        #     if strings[part] not in str_reuse:
        #         str_reuse[strings[part]] = 0
        #     else:
        #         str_reuse[strings[part]] += 1
        #     mcode += f'"{strings[part]}"'
        start = hascomment(line)
        if start is None:
            start = -1

        if "REQUIRE " in line[start:]:
            requires += line[start:] + '\n'  # leave REQUIREs unmodified
            # comments are terminated by a newline so we need to add one back in

        # *deep breath*
        # slicing is exclusive on the right side of the colon so the "no comment" value of start=-1 would cut off
        # the last character of the line which would lead to several issues
        # however this is desirable when there *is* a comment, since it being exclusive means there isn't a trailing #
        # and if you're wondering about the above check that uses line[start:] this doesn't matter,
        # one character cant contain an 8 character substring
        if start != -1:
            line = line[:start]
        line = line.split(sep='"')

        if len(line) % 2 == 0:
            print("You appear to have string literals spanning multiple lines. Please seek professional help")
            raise Exception("Too much hatred")
        part = 0
        while part < len(line):
            # all the odd numbered indexes should be inside quotes
            if part % 2 == 0:
                if not line[part]:
                    break
                for s in sub_funcs:
                    stl_counts[s] += len(re.findall("(?<!\\.)%s\\(" % s, line[part]))
                mcode += line[part].replace('\t', '') + ' '
            else:
                if line[part] not in str_reuse:
                    str_reuse[line[part]] = 0
                else:
                    str_reuse[line[part]] += 1
                mcode += f'"{line[part]}"'

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
            if wantsumspace(sec[0]) and wantsumspace(sec[2]):
                pass
            elif sec[0] == '-' and sec[2].isnumeric():
                pass
            else:
                newline[index + 1] = ''
        index += 1
    mmcode += ''.join(newline).strip()

    for func in sub_funcs:
        # space saved here is given by n * (len(func) - len(min_func)) - (len(min_func)+1 + len(func))
        # as such with one usage space is always lost (len(func)-2 is never > len(func)+3) so dont even try
        if stl_counts[func] >= 2:
            savings = stl_counts[func] * (len(func) - 2) - (len(func) + 3)
            print(f"Replacing all {stl_counts[func]} usages of {func} would save {savings}byte{'s' if savings != 1 else ''}")
            if (savings < 0) or not replace_functions:
                print("Savings negative or automatic replacement disabled, continuing")
                continue
            func_min = sub_funcs[func]  # now here we have to assume nobody is using any of our substitute vars
            # should be a pretty safe assumption but knowing for sure would require about the same amount of effort
            # as it would to replace all user defined variables
            ucode = ""  # this is rather hacky
            sections = [0]
            for m in re.finditer(r"(?<!\.)%s\(" % func, mmcode):
                sections.append(m.span()[0])
                sections.append(m.span()[1])
            sections.append(len(mmcode))
            i = 2       # change rather to very
            while i < len(sections):
                ucode += mmcode[sections[i-2]:sections[i-1]] + func_min + '('
                i += 2
            ucode += mmcode[sections[i-2]:]

            ucode = f"{func_min}={func}\n" + ucode
            mmcode = ucode
            # a space isn't any shorter than \n so why not use \n

    for string, count in str_reuse.items():
        if count >= 2:
            # we can't auto replace strings without a full parser
            # unlike with the stdlib functions we cant make a lookup table ahead of time
            # and generating shorter names on the fly sounds like an absolute nightmare no thanks
            print(f'Warning: string "{string}" of len {len(string)} reused {count} times')

    return requires + mmcode.strip()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description="Minify tsv3 scripts, useful for embedding",
                                        formatter_class=argparse.RawTextHelpFormatter)
    argparser.add_argument("source", type=str, nargs='+', help="source files to minify")
    argparser.add_argument("-d", type=str, nargs='?', help="destination folder for minified scripts"
                                                        "\ndefault: ./", default='./')
    argparser.add_argument("--replace-functions", action="store_true", default=False,
                           help="automatically replace reused functions instead of just warning\ndefault: false")

    args = argparser.parse_args()
    files = args.source
    dest = args.d[:-1] if args.d[-1] == '/' else args.d
    replace_functions = args.replace_functions if args.replace_functions is not None else False

    for file in files:
        print(f"Minifying {file}")
        with open(file, 'r') as f:
            r = parser(f.read())
        file = file.split(sep='.')[0].split(sep='/')[-1]
        if dest != '.':
            f = open(f"{dest}/{file}.te", 'w')
        else:
            f = open(f"{dest}/{file}_min.te", 'w')
        f.write(r)
