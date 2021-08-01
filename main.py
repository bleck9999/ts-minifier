import argparse
import itertools
from string import ascii_letters

auto_replace = False


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
        self.rawcode = "".join([x[2] for x in self.sections])

    def getafter(self, ch: int):
        for strcom in self.string_comments:
            if strcom[0] >= ch:
                return strcom
        return None

    def nextch(self, ch: int, reverse: bool):
        rawcontent = self.rawcode
        if ((ch+1 >= len(rawcontent)) and not reverse) or \
                ((ch-1 < 0) and reverse):
            return ''
        return rawcontent[ch-1] if reverse else rawcontent[ch+1]

    def calling(self, ch: int):
        rawcontent = self.rawcode
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
        if c not in (ascii_letters + '_'):
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
                    usages[identifier].append(start+item[0])  # it's been declared before, so this is a usage
                else:
                    isfunc = script.nextch(ch + item[0], False) == '{'
                    userobjects[identifier] = "func" if isfunc else "var"
                    usages[identifier] = []  # declaration is not a usage
                start = len(sec) + 1
            elif sec[ch] == '.':
                if ismember:  # we check if there's a . after a ), if there is we know that there's nothing to do here
                    continue
                x = ch+item[0]
                while prev := script.nextch(x, True):
                    if prev == '.':
                        break
                    elif not isidentifier(prev):
                        usages[sec[start:ch]].append(start+item[0])
                        break
                    x -= 1
                ismember = True
                start = len(sec) + 1
                # we don't really care about anything else
            elif sec[ch] == '(':
                if ismember:
                    if "foreach" in sec[start:ch]:  # array.foreach takes a variable name as an arg (blame meme)
                        name = script.getafter(ch+item[0])[2].replace('"', '')
                        usages[name] = []
                        userobjects[name] = "var"
                    else:
                        pass
                else:
                    identifier = sec[start:ch]
                    if identifier in usages:
                        usages[identifier].append(start+item[0])
                    else:
                        usages[identifier] = [start+item[0]]  # this should only be happen for stdlib functions
                start = len(sec) + 1
            elif sec[ch] == ')':
                if start != len(sec)+1 and not ismember:
                    usages[sec[start:ch]].append(start+item[0])
                ismember = script.nextch(ch+item[0], False) == '.'
                start = len(sec) + 1

    return minify(script, userobjects, usages)


def minify(script: Code, userobjects, usages):
    # the space saved by an alias is the amount of characters currently used by calling the function (uses*len(func))
    # minus the amount of characters it would take to define an alias (len(alias)+len(func)+2), with the 2 being the
    # equals and the whitespace needed for a definition
    # obviously for a rename you're already defining it so it's just the difference between lengths multiplied by uses
    short_idents = [x for x in (ascii_letters+'_')] + [x[0]+x[1] for x in itertools.permutations(ascii_letters+'_', 2)]
    for uo in userobjects:
        otype = userobjects[uo]
        uses = len(usages[uo])
        if uses == 0:
            print(f"{'Function' if otype == 'func' else 'Variable'} {uo} assigned to but never used")
        elif len(uo) > 1:
            candidates = short_idents
            minName = ''
            if len(uo) == 2:
                candidates = short_idents[:53]
            for i in candidates:
                if i not in userobjects:
                    minName = i
            if not minName:
                print(f"{'Function' if otype == 'func' else 'Variable'} name {uo} could be shortened but no available "
                      f"names found (would save {uses*len(uo)-1}bytes)")
                continue
                # we assume that nobody is insane enough to exhaust all *2,756* 2 character names,
                # instead that uo is len 1 and all the 1 character names are in use
            if not auto_replace:
                print(f"{'Function' if otype == 'func' else 'Variable'} name {uo} could be shortened ({uo}->{minName}, "
                      f"would save {uses*(len(uo)-len(minName))} bytes")
                continue
            else:
                print(f"Renaming {'Function' if otype == 'func' else 'Variable'} {uo} to {minName} "
                      f"(saving {uses*(len(uo)-len(minName))}bytes)")
                # todo: actually do that
    for func in usages:
        candidates = short_idents
        minName = ''
        savings = 0
        uses = len(usages[func])
        if func in userobjects or uses < 2:  # we only want stdlib functions used more than once
            continue
        elif func == "if":
            candidates = short_idents[:53]
            savings = uses * 2 - 5  # the 5 is how many characters an alias declaration would use (a=if<space>)
        for i in candidates:
            if i not in userobjects:
                minName = i
        if not minName:
            print(f"Standard library function {func} could be aliased but no available names found")
        else:
            if not savings:
                savings = uses*len(func) - (len(func)+len(minName)+2)
            if savings <= 0 or not auto_replace:
                print(f"Not aliasing standard library function {func} (would save {savings}bytes)")
            else:
                print(f"Aliasing standard library function {func} to {minName} (saving {savings}bytes)")
                # todo: actually do that part 2


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
    argparser.add_argument("--auto-replace", action="store_true", default=False,
                           help="""automatically replace reused functions and variables instead of just warning
                           and attempt to generate shorter names for reused variables \ndefault: false""")

    args = argparser.parse_args()
    files = args.source
    dest = args.d[:-1] if args.d[-1] == '/' else args.d
    auto_replace = args.auto_replace if args.auto_replace is not None else False

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
