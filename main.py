import argparse
import re

# if is not included because it's already 2 characters
sub_funcs = {'while': "_h", 'print': "_p", 'println': "_l", 'mountsys': "_s", 'mountemu': "_e", 'readsave': "_r",
             'exit': "_q", 'break': "_b", 'dict': "_d", 'setpixel': "_y", 'readdir': "_i", 'copyfile': "_c",
             'mkdir': "_k", 'ncatype': "_n", 'pause': "_w", 'color': "_a", 'menu': "__", 'emu': "_u",
             'clear': "_x", 'timer': "_t", 'deldir': "_g", 'fsexists': "_f", 'delfile': "_z", "copydir": "c_",
             "movefile": "_v", "payload": "_j", "readfile": "_o", "writefile": "w_", "setpixels": "y_",
             "printpos": "p_",
             "emmcread": "e_", "emmcwrite": "f_", "emummcread": "r_", "emummcwrite": "s_", "escapepath": "x_",
             "combinepath": "a_", "cwd": "d_", "power": "o_"}
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
        if ((ch+1 >= len(rawcontent)) and not reverse) or \
                ((ch-1 < 0) and reverse):
            return ''
        return rawcontent[ch-1] if reverse else rawcontent[ch+1]

    def calling(self, ch: int):
        rawcontent = "".join([x[2] for x in self.sections])
        caller = ""
        commented = False
        while (x := ch - 1) or True:
            if rawcontent[ch] in ['.', ')', '"', '}'] and not commented:
                return caller
            elif rawcontent[ch] == '\n':
                commented = True
            elif rawcontent[ch] == '#':
                commented = False
            else:
                caller = rawcontent[ch] + caller
        raise Exception("something that shouldnt happen has happened")


def isidentifier(s: str):
    for c in s:
        c = c.lower()
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
            comments.append((commentstart, c + 1, script[commentstart:c + 1]))
            commented = False
        elif script[c] == '"' and not commented:
            if not quoted:
                strstart = c
                quoted = True
            else:
                strings.append((strstart, c + 1, script[strstart:c + 1]))
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
    #   we are assuming the input script is valid syntax

    userobjects = {}
    usages = {}
    ismember = False
    for item in script.code:
        sec = item[2]
        start = len(sec) + 1
        for ch in range(len(sec)):
            if isidentifier(sec[ch]):
                if start > ch:
                    start = ch
                else:
                    pass
            elif sec[ch] == '=':
                identifier = sec[start:ch]
                if identifier in userobjects:
                    usages[identifier] += 1  # it's been declared before, so this is a usage
                else:
                    isfunc = script.nextch(ch + item[0], False) == '{'
                    userobjects[identifier] = "func" if isfunc else "var"
                    usages[identifier] = 0  # declaration is not a usage
                start = len(sec) + 1
            elif sec[ch] == '.':
                if ismember:  # we check if there's a . after a ), if there is we know that there's nothing to do here
                    continue
                x = ch+item[0]
                while prev := script.nextch(x, True):
                    if prev == '.':
                        break
                    elif not isidentifier(prev):
                        usages[sec[start:ch]] += 1
                        break
                    x -= 1
                start = len(sec) + 1
                # we don't really care about anything else
            elif sec[ch] == '(':
                if ismember:
                    if sec[start:ch] == "foreach":  # array.foreach takes a variable name as an arg (blame meme)
                        name = script.getafter(ch+item[0])[2]
                        usages[name] = 0
                        userobjects[name] = "var"
                    else:
                        pass
                else:
                    identifier = sec[start:ch]
                    if identifier in usages:
                        usages[identifier] += 1
                    else:
                        usages[identifier] = 1  # this should only be happen for stdlib functions
                start = len(sec) + 1
            elif sec[ch] == ')':
                ismember = script.nextch(ch+item[0], False) == '.'
                start = len(sec) + 1

    print("")


def preminify(script: str):
    requires = ""
    mcode = ""
    for line in script.split(sep='\n'):
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
                mcode += line[part].replace('\t', '') + ' '
            else:
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
            if (isidentifier(sec[0]) or sec[0].isnumeric()) and (isidentifier(sec[2]) or sec[2].isnumeric()):
                pass
            elif sec[0] == '-' and sec[2].isnumeric():
                pass
            else:
                newline[index + 1] = ''
        index += 1
    mmcode += ''.join(newline).strip()

    return requires + mmcode.strip().replace('\n', ' ')


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
            r = parser(preminify(f.read()))
        file = file.split(sep='.')[0].split(sep='/')[-1]
        if dest != '.':
            f = open(f"{dest}/{file}.te", 'w')
        else:
            f = open(f"{dest}/{file}_min.te", 'w')
        f.write(r)
