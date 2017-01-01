import random
import time

import math

import re
import sys
import os
import shlex
import struct
import shutil
import platform
import subprocess
import hashlib
import datetime

arg_synonyms = {}
arg_synonyms['--help'] = 'help'
arg_synonyms['-help'] = 'help'
arg_synonyms['probability'] = 'prob'
arg_synonyms['targs'] = 'targets'
arg_synonyms['hit_chance'] = 'chance'

def command_line(args):
    if 'help' in args:
        print('Utility:')
        print('Whenever arguments are listed, those are the names of the keywords that should be provided.')
        print('For example, if it says (v1, v2), that means that you should call "utility" as follows: "utility v1=2 v2=4"')
        print('intercept: Calculates a 2D interception. Takes the coordinates (x1, y1, x2, y2), the velocities (v1, v2), and the angle of the target (theta). Returns the time and direction of the interception.')
        print('titlecase: Combines all arguments, then titlecases them.')
        print('show: Shows how the arguments passed in have been parsed.')
        print('lines: Counts the number of lines of each file in the given (dir) and prints the sum.')
        print('cull: Removes any weird files that give an error when trying to read because they don\'t exist.')
        print('illegal_path_char: Finds the character, if any, in (path) that cannot be used in a filename.')
        print('md5: Uses md5 to hash the given (path).')
        print('prob: Contains probability functions.')
        print('\txiny: Calculates the chances of accomplish a task a number of times given a number of changes. Takes (targets, tries, chance), and optionally, (verbose, chance).')
    elif 'intercept' in args:
        x1, y1 = float(args['x1']), float(args['y1'])
        x2, y2 = float(args['x2']), float(args['y2'])
        v1, v2 = float(args['v1']), float(args['v2'])
        theta = float(args['theta'])

        print(calculate_interception(v1, v2, (x1, y1), (x2, y2), theta))
    elif 'prob' in args:
        if 'xiny' in args:
            targets = int(args['targets'])
            tries = int(args['tries'])
            hit_chance = float(args['chance'])

            verbose = int(args.get('verbose', 1))
            tests = int(args.get('tests', 10000))

            do_x_in_y_tries(targets, tries, hit_chance, verbose=verbose, tests=tests)
    elif 'titlecase' in args:
        args['argv'].remove('titlecase')
#finished client='0b792fb2-2aea-4a37-96a3-1a82ed226ff1' fname='index.php-title=Special-AllPages&from=%22%C2%A130-30%21%22.txt' results='[True]'
        print(titlecase(' '.join(args['argv'])))
    elif 'show' in args:
        print(args.args)
    elif 'illegal_path_char' in args:
        print(find_illegal_path_character(args['path']))
    elif 'lines' in args:
        lines_in_dir(dir_name=args['dir'], message=' total lines.')
    elif 'cull' in args:
        cull_invalid_files(args['dir'])
    elif 'md5' in args:
        print(md5(args['path']))
    elif 'cull_name' in args:
        cull_files_by_name(args['dir'], args['re'], 'recurse' in args)

# Fast inv norm approx.
def inv_norm(p):
    c1, c2, c3 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    if p < 0.5:
        t = math.sqrt(-2 * math.log(p))
        return -(t - ((c3*t + c2)*t + c1) / (((d3*t + d2)*t + d1)*t + 1.0))
    else:
        t = math.sqrt(-2 * math.log(1-p))
        return t - ((c3*t + c2)*t + c1) / (((d3*t + d2)*t + d1)*t + 1.0)

def cint(m, n, s, intsize):
    z = inv_norm(intsize + (1 - intsize) / 2)

    return (m - z * s / math.sqrt(n), m + z * s / math.sqrt(n))

def mean(l):
    return sum(l) / float(len(l))

def stddev(m, l):
    if len(l) == 1:
        return math.sqrt(sum(map(lambda i: (i - m)**2, l)) / (float(len(l))))
    else:
        return math.sqrt(sum(map(lambda i: (i - m)**2, l)) / (float(len(l)) - 1))

def stats(l):
    m = mean(l)
    s = stddev(m, l)
    l, h = cint(m, float(len(l)), s, 0.95)
    return (m, s, (l, h))

def round_nearest(x, a):
    return round(x / a) * a

def median(vs, m=0):
    if len(vs) == 0:
        return m
    elif len(vs) == 1:
        return vs[0]

    vs = sorted(vs)
    if len(vs) % 2 == 0: # If it's even, average the center two values
        half = len(vs) / 2
        return (vs[half] + vs[half - 1]) / 2.0
    else:
        return float(vs[len(vs) // 2])

# Returns - (the five number summary, low_outliers, high_outliers)
# The five number summary is the lowest non-outlier value, the first quartile,
# the median, the third quartile, and then the highest non-outlier value
# An outlier is more than 1.5 interquartile ranges (third quartile - first quartile)
# away from the median.
def five_number_summary(vs):
    m = median(vs)
    q1 = median(filter(lambda i: i < m, vs), m=m)
    q3 = median(filter(lambda i: i > m, vs), m=m)
    iqr = q3 - q1

    lower_fence = m - 1.5 * iqr
    upper_fence = m + 1.5 * iqr

    lower_outliers = filter(lambda i: i < lower_fence, vs)
    upper_outliers = filter(lambda i: i > upper_fence, vs)

    non_outliers = filter(lambda i: i > lower_fence and i < upper_fence and (i < q1 or i > q3), vs)
    if len(non_outliers) > 0:
        smin = min(non_outliers)
        smax = max(non_outliers)
    else:
        smin = q1
        smax = q3

    return ([smin, q1, m, q3, smax], lower_outliers, upper_outliers)

def count_files(dir_name, recurse=True, f_re=None):
    if not recurse:
        return len(get_files(dir_name, search_re=f_re))
    else:
        dir_names = get_directories(dir_name)
        res = len(get_files(dir_name, search_re=f_re))

        for dname in dir_names:
            res += count_files(dname, recurse=recurse, f_re=f_re)

        return res

def cull_files_by_name(dir_name, f_re, recurse=False):
    if '.*' in f_re:
        print('Warning! This looks pretty general (it has a .*), are you sure? Type "yes" if you want to continue.')
        res = raw_input()
        if res != 'yes':
            return

    for fname in get_files(dir_name, search_re=f_re):
        os.remove(fname)

    if recurse:
        for dirname in get_directories(dir_name):
            cull_files_by_name(dirname, f_re=f_re, recurse=recurse)

def empty_dir(dir_name):
    shutil.rmtree(dir_name)
    os.mkdir(dir_name)

def group_by(f, l):
    return

def group_and_sort_by(f, l):
    groups = {}
    for v in l:
        val = f(v)

        if val in groups:
            groups[val].append(v)
        else:
            groups[val] = [v]

    for group in groups:
        groups[group] = sorted(groups[group])

    return map(snd, sorted(groups.items()))

def falseiferror(f):
    def test(v):
        try:
            f(v)

            return True
        except:
            return False

    return test

# From https://gist.github.com/jtriley/1108174
def get_terminal_size():
    """ getTerminalSize()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     originally retrieved from:
     http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    """
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            # needed for window's python in cygwin's xterm!
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None:
        print "default"
        tuple_xy = (80, 25)      # default value
    return tuple_xy

def _get_terminal_size_windows():
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except:
        pass


def _get_terminal_size_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return (cols, rows)
    except:
        pass


def _get_terminal_size_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack('hh',
                               fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            return cr
        except:
            pass
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])

def get_os():
    current_os = platform.system()
    if current_os == 'Windows':
        return 'windows'
    elif current_os == 'Darwin':
        return 'osx'
    elif current_os == 'Linux':
        return 'linux'

def is_windows():
    return get_os() == 'windows'

def is_osx():
    return get_os() == 'osx'

def is_linux():
    return get_os() == 'linux'

def md5(fname):
    return hashlib.md5(open(fname, 'rb').read()).hexdigest()

def find_illegal_path_character(path):
    working_paths = []

    possible_characters = []

    dir_len = len('/'.join(path.split('/')[:-1]))

    for i, c in enumerate(path):
        if i <= dir_len:
            continue
        try:
            test_path = path[:i] + path[i + 1:]
            with open(test_path, 'w') as f:
                f.write('test')
            possible_characters.append((i, c))
            working_paths.append(test_path)
        except IOError as e:
            print('Still an error if we remove {}'.format((i, c)))
            continue

    # We don't want to leave a bunch of crap lying around.
    for remove_path in working_paths:
        os.remove(remove_path)

    return possible_characters

def cull_invalid_files(dir_name, verbose=1):
    if not dir_name.endswith('/'):
        dir_name += '/'

    for fname in get_files(dir_name):
        try:
            contents = ''
            with open(fname, 'r') as f:
                contents = f.read()

            #This file is fine, do nothing
        except IOError as e: # Error, kill the file
            if e.errno == 2: # No such file
                if verbose > 0:
                    print('Removing: \'{}\''.format(dir_name + fname))

                os.remove(dir_name + fname)

def lines_in_dir(dir_name='.', message=None, progress=False):
    if not dir_name.endswith('/'):
        dir_name += '/'

    total = 0
    for fname in get_files(dir_name):
        try:
            with open(fname, 'r') as f:
                total += len(f.readlines())
        except Exception as e:
            pass

        if progress or message:
            sys.stdout.write('\r{} {}'.format(total, message))
            sys.stdout.flush()

    return total

def remove_illegal_path_characters(path, replacement='-'):
    path = path.replace('?', replacement).replace('/', replacement).replace(':', replacement)
    path = path.replace('+', replacement).replace('"', replacement).replace('\'', replacement)
    path = path.replace('*', replacement)

    return path

def get_directories(directory, search_re=None):
    directory = directory.replace('//', '/')
    for (dirpath, dirnames, filenames) in os.walk(directory):
        if search_re != None:
            res = []
            for dname in dirnames:
                if re.search(search_re, dname):
                    res.append(dname)
            return map(lambda i: dirpath + '/' + i, res)
        else:
            return map(lambda i: dirpath + '/' + i, dirnames)

def get_files(directory, search_re=None):
    directory = directory.replace('//', '/')
    for (dirpath, dirnames, filenames) in os.walk(directory):
        if search_re != None:
            res = []
            for fname in filenames:
                if re.search(search_re, fname):
                    res.append(fname)
            return map(lambda i: dirpath + '/' + i, res)
        else:
            return map(lambda i: dirpath + '/' + i, filenames)

def do_x_in_y_tries(targets, max_tries, hit_chance, verbose=1, tests=10000):
    successes = 0
    total_targets_destroyed = 0
    max_targets_destroyed = 0
    min_targets_destroyed = -1
    total_tries = 0

    inc = int(tests / 1000)

    for i in xrange(tests):
        tries = 0
        targets_destroyed = 0

        for target in xrange(targets):
            tries += 1
            while random.random() > hit_chance and tries < max_tries:
                tries += 1

            if tries >= max_tries:
                break
            else:
                targets_destroyed += 1

        if targets_destroyed < min_targets_destroyed or min_targets_destroyed == -1:
            min_targets_destroyed = targets_destroyed
        if targets_destroyed > max_targets_destroyed:
            max_targets_destroyed = targets_destroyed

        total_targets_destroyed += targets_destroyed
        total_tries += tries

        if targets_destroyed == targets:
            successes += 1

        if verbose > 1:
            sys.stdout.write('\r{} targets in {} tries. {} of {}. {} successes ({}%). Max: {}, Min: {}'.format(targets_destroyed, tries, i, tests, successes, float(successes) / float(i + 1) * 100.0, max_targets_destroyed, min_targets_destroyed))
            sys.stdout.flush()
        elif verbose > 0 and i % inc == 0:
            sys.stdout.write('\r{} targets in {} tries. {} of {}. {} successes ({}%). Max: {}, Min: {}'.format(targets_destroyed, tries, i, tests, successes, float(successes) / float(i + 1) * 100.0, max_targets_destroyed, min_targets_destroyed))
            sys.stdout.flush()

    print('')
    print('{} successes ({}%).'.format(successes, float(successes) / float(tests) * 100.0))
    print('{} targets on average in an average of {} tries.'.format(float(total_targets_destroyed) / float(tests), float(total_tries) / float(tests)))
    print('Destroyed a maximum of {} targets and a minimum of {} targets.'.format(max_targets_destroyed, min_targets_destroyed))

SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
def ordinal(num):
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        # the second parameter is a default.
        suffix = SUFFIXES.get(num % 10, 'th')
    return str(num) + suffix

def flip_dict(d):
    res = {}

    for k, v in d.items():
        res[v] = k

    return res

class CommandArgs:
    def __init__(self, args):
        self.args = args
        self.argv = args['argv']

    def get(self, key, default=None):
        return self.args.get(key, default)

    def __getitem__(self, v):
        return self.args[v]

    def __contains__(self, v):
        return v in self.args or v in self.argv

def command_line_args(args=None, arg_synonyms={}):
    if isinstance(args, str):
        args = shlex.split(args)

    if args == None:
        args = sys.argv
        args.pop(0) # The first argument is just the name of the file

    arg_values = {}

    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('-'):
            if '=' in arg:
                params = arg.split('=')

                if params[0] in arg_synonyms:
                    params[0] = arg_synonyms[params[0]]

                arg_values[params[0]] = params[1] == 'True'

                args.remove(arg)
            else:
                param = arg[1:]

                if param in arg_synonyms:
                    param = arg_synonyms[param]
                arg_values[param] = True

                args.remove(arg)
        elif '=' in arg:
            params = arg.split('=')

            if params[0] in arg_synonyms:
                params[0] = arg_synonyms[params[0]]
            # Jsut in case
            arg_values[params[0]] = '='.join(params[1:])

            args.remove(arg)
        else:
            i += 1

    # Store the rest of the plain arguments, just in case we need them
    arg_values['argv'] = []
    for arg in args:
        arg_values['argv'].append(arg)

    return CommandArgs(arg_values)

def get_dense_areas(ps, squared_radius, results=10, verbose=0):
    density = {}
    for i, p in enumerate(ps):
        density[p] = 0
        for p2 in ps[i:]:
            if distance_squared(p, p2) < squared_radius:
                density[p] += 1
                if p2 in density:
                    density[p2] += 1
                else:
                    density[p2] = 1

        if verbose > 0:
            show_bar(i, len(ps), number_limit=True, message='Getting density ({}): '.format(len(ps) - i))

    res = sorted(density.items(), key=snd, reverse=True)

    if verbose > 1:
        print('')
        print(res)

    final_res = []
    while len(final_res) < results and len(res) > 0:
        final_res.append(res.pop(0))

        oldlen = len(res)
        i = 0
        while i < len(res):
            if distance_squared(res[i][0], final_res[-1][0]) < squared_radius:
                res.pop(i)
            else:
                i += 1
        print(oldlen, len(res))

    return final_res

def identity(x):
    return x

def get_indices_where(f, ls):
    res = []
    for i, v in enumerate(ls):
        print(v)
        if isinstance(v, list):
            sub_res = get_indices_where(f, v)
            for r in sub_res:
                res.append([i] + r)
        else:
            if f(v):
                res.append([i])

    return res

def all_ratios(ls):
    res = []
    for a in ls:
        for b in ls:
            if a != b:
                res.append(float(a) / float(b))
    return res

def capitalize_first_letter(s):
    return s[0].upper() + s[1:]

def displayify_text(s):
    words = s.split('_')
    words = map(capitalize_first_letter, words)
    return ' '.join(words)

def show_dict(d, depth=1, recurse=True):
    for stat, v in sorted(d.items()):
        if isinstance(v, dict):
            if recurse:
                print('{}{}:'.format('\t' * depth, displayify_text(stat)))
                show_dict(v, depth=depth + 1, recurse=recurse)
        elif isinstance(v, list):
            if recurse:
                print('{}{}:'.format('\t' * depth, displayify_text(stat)))
                show_dict({str(i): lv for i,lv in enumerate(v)}, depth=depth + 1, recurse=recurse)
        else:
            print('{}{}: {}'.format('\t' * depth, displayify_text(stat), v))

def fst(t):
    return t[0]

def snd(t):
    return t[1]

# Finds the corresponding keys in a dictionary and applies the function to both, creating a new dictionary
# f_single is used if the key appears in only one of the dictionaries
def zip_dict_with(f, a, b, f_single=None):
    res = {}
    for k in a:
        if k in b:
            res[k] = f(a[k], b[k])
        else:
            if f_single != None:
                res[k] = f_single(a[k])

    if f_single != None:
        for k in b:
            if not k in res:
                res[k] = f_single(b[k])

    return res

def rgb_color(r, g, b):
    return '#{}{}{}'.format(hex(r)[2:].ljust(2, '0'), hex(g)[2:].ljust(2, '0'), hex(b)[2:].ljust(2, '0'))

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
    )

def display_time(seconds, granularity=5):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])

terminal_width = -1
def show_bar(i, total, start_time=None, width=80, message='', number_limit = False):
    global terminal_width
    if terminal_width == -1:
        terminal_width,_ = get_terminal_size()
        terminal_width -= 1

    if terminal_width != -1:
        width = terminal_width

    if isinstance(total, int) or isinstance(total, float):
        number_limit = True

    # Because we start counting at 0
    i += 1

    # Just to make sure we don't get a ridiculously long bar
    i = min(total, i)

    time_message = ''
    if start_time != None:
        elapsed = time.time() - start_time
        if number_limit:
            estimated_remaining = elapsed / float(i) * float(total - i)
        else:
            estimated_remaining = elapsed / float(i) * float(len(total) - i)

        time_message = '{} seconds. '.format(round(estimated_remaining))

    message += time_message

    # The 2 is because of the []
    if not number_limit:
        bar_chunks = int(float(i) / float(len(total)) * (width - len(message) - 2))
    else:
        bar_chunks = int(float(i) / float(total) * (width - len(message) - 2))

    sys.stdout.write('\r{}'.format(message) + '[{}{}]'.format('=' * bar_chunks, ' ' * (width - bar_chunks - len(message) - 2)))
    sys.stdout.flush()

def calculate_interception(v_e, v_p, (x_e, y_e), (x_p, y_p), theta_e):
    t1 = -(v_e*x_e*math.cos(theta_e) - v_e*x_p*math.cos(theta_e) + v_e*y_e*math.sin(theta_e) - v_e*y_p*math.sin(theta_e) + math.sqrt(-(v_e**2*math.sin(theta_e)**2 - v_p**2)*x_e**2 + 2*(v_e**2*math.sin(theta_e)**2 - v_p**2)*x_e*x_p - (v_e**2*math.sin(theta_e)**2 - v_p**2)*x_p**2 - (v_e**2*math.cos(theta_e)**2 - v_p**2)*y_e**2 - (v_e**2*math.cos(theta_e)**2 - v_p**2)*y_p**2 + 2*(v_e**2*x_e*math.cos(theta_e)*math.sin(theta_e) - v_e**2*x_p*math.cos(theta_e)*math.sin(theta_e))*y_e - 2*(v_e**2*x_e*math.cos(theta_e)*math.sin(theta_e) - v_e**2*x_p*math.cos(theta_e)*math.sin(theta_e) - (v_e**2*math.cos(theta_e)**2 - v_p**2)*y_e)*y_p))/((math.cos(theta_e)**2 + math.sin(theta_e)**2)*v_e**2 - v_p**2)
    t2 = -(v_e*x_e*math.cos(theta_e) - v_e*x_p*math.cos(theta_e) + v_e*y_e*math.sin(theta_e) - v_e*y_p*math.sin(theta_e) - math.sqrt(-(v_e**2*math.sin(theta_e)**2 - v_p**2)*x_e**2 + 2*(v_e**2*math.sin(theta_e)**2 - v_p**2)*x_e*x_p - (v_e**2*math.sin(theta_e)**2 - v_p**2)*x_p**2 - (v_e**2*math.cos(theta_e)**2 - v_p**2)*y_e**2 - (v_e**2*math.cos(theta_e)**2 - v_p**2)*y_p**2 + 2*(v_e**2*x_e*math.cos(theta_e)*math.sin(theta_e) - v_e**2*x_p*math.cos(theta_e)*math.sin(theta_e))*y_e - 2*(v_e**2*x_e*math.cos(theta_e)*math.sin(theta_e) - v_e**2*x_p*math.cos(theta_e)*math.sin(theta_e) - (v_e**2*math.cos(theta_e)**2 - v_p**2)*y_e)*y_p))/((math.cos(theta_e)**2 + math.sin(theta_e)**2)*v_e**2 - v_p**2)

    if t1 > 0:
        n = x_e-x_p+v_e*t1*math.cos(theta_e)
        d = v_p * t1
        if n > d:
            n = d - 1 * 10^-10
        theta_p1 = math.amath.cos(n / d)

        return (t1, theta_p1)
    else:
        n = x_e-x_p+v_e*t2*math.cos(theta_e)
        d = v_p * t2
        if n > d:
            n = d - 1 * 10^-10
        theta_p1 = math.amath.cos(n / d)

        return (t2, theta_p2)

def calculate_xy_vector((magnitude, angle)):
    return (magnitude * math.cos(angle), magnitude * math.sin(angle))

def calculate_polar_vector((dx, dy)):
    magnitude = math.sqrt(dx**2 + dy**2)

    return (magnitude, math.atan2(dy, dx))

def count(l):
    res = {}
    for i in l:
        if i in res:
            res[i] += 1
        else:
            res[i] = 1

    return res

def tuplize(l):
    res = l

    for i in xrange(len(res)):
        if isinstance(res[i], list):
            res[i] = tuplize(res[i])

    return tuple(res)

# If nested is true, will return all nested containers separately
def get_containers(s, start, end, nested=False):
    res = []

    start_poss = []

    level = 0
    for i in xrange(len(s)):
        # print(level)
        if s[i] == start:
            level += 1

            start_poss.append(i)
        elif s[i] == end:
            level -= 1

            level = max(level, 0)

            if len(start_poss) > 0:
                if level == 0:
                    res.append(s[start_poss.pop(0):i + 1])

                    start_poss = []
                elif nested:
                    res.append(s[start_poss.pop(-1):i + 1])

    return res

def is_contained(s, start, end, start_pos):
    level = 0

    for i in xrange(start_pos, -1, -1):
        if s[i] == end:
            level -= 1
        elif s[i] == start:
            level += 1

            if level == 1:
                return True

    return False

def get_container(s, start, end, start_pos):
    level = 1

    i = start_pos
    while i < len(s):
        if s[i] == start:
            level += 1
        elif s[i] ==end:
            level -= 1
            if level == 0:
                break

        i += 1

    return s[start_pos:i]

def find_container_of(s, start, end, char):
    # Start here, and go back until we find the starting bracket
    level = 0

    start_pos = 0
    while start_pos < len(s):
        if s[start_pos] == start:
            level += 1
        elif s[start_pos] == end:
            level -= 1
        elif s[start_pos] == char and level == 1:
            break
        start_pos += 1

    if start_pos >= len(s) - 1:
        raise Exception('\'{}\' not found in {}.'.format(char, s))
    while start_pos > 0:
        if s[start_pos] == end:
            level += 1
        elif s[start_pos] == start:
            level -= 1
            if level == 0:
                break

        start_pos -= 1

    level = 1
    end_pos = start_pos + 1
    while end_pos < len(s):
        if s[end_pos] == start:
            level += 1
        elif s[end_pos] == end:
            level -= 1
            if level == 0:
                break

        end_pos += 1

    return start_pos, end_pos

# So that if an inner section is detected, its entire contents are ignored
# For example, separate_container('<test|test1>|test2', '<', '>', '|') will return ['<test|test1>', 'test2']
def separate_container(s, start, end, char):
    result = []
    level = 0

    i = 0
    while len(s) > 0 and i < len(s):
        if s[i] == char and level == 0:
            result.append(s[:i])
            s = s[i + 1:]
            i = 0
        else:
            if s[i] == start:
                level += 1
            elif s[i] == end:
                level -= 1
            i += 1

    if len(s) > 0:
        result.append(s)

    return result

def titlecase(s):
    new_words = []
    for word in s.split():
        if not word in ['of', 'by', 'a', 'the']:
            word = word[0].upper() + word[1:]

        new_words.append(word)

    # First word is always capitalized
    if len(new_words) > 0 and len(new_words[0]) > 0:
        new_words[0] = new_words[0][0].upper() + new_words[0][1:]

    return ' '.join(new_words)

# If reverse is false, then it selects heigher weights, if it's true, then it selects lower ones.
def weighted_random_choice(col, weight=None, reverse=True):
    if weight == None:
        weight = lambda i, _: i #Makes it more likely to select early indexes.

    col = list(col)
    random.shuffle(col)

    accum = 0
    total = sum(map(lambda i: weight(i[0], i[1]), enumerate(col)))
    goal = random.random() * total

    for i, v in enumerate(col):
        weight_value = weight(i, v)
        weight_value = weight(i, v)
        # print(weight_value)
        if weight_value > 0: #If its not, we'll get an error for an empty randrange
            accum += weight_value

            if accum > goal:
                return v

    return col[0]

def rough_match(a, b, tolerance):
    return a + tolerance >= b and a - tolerance <= b

def clamp(a, minv, maxv):
    if a > maxv:
        return maxv
    elif a < minv:
        return minv
    else:
        return a

def product(l):
    return reduce(lambda a, b: a * b, l)

def flatten(l):
    result = []

    for sub_l in l:
        result += sub_l

    return result

def mutate(l, amount, base="qwertyuiopasdfghjklzxcvbnm"):
    result = []

    for i in xrange(random.randint(1, len(l) / amount + 1)):
        l.remove(random.choice(l))

    for i in xrange(random.randint(1, len(l) / amount + 1)):
        l.append(random.choice(l) if random.randint(0, 2) == 0 else random.choice(base))

    return l

def distance((x1, y1), (x2, y2)):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def distance_squared((x1, y1), (x2, y2)):
    return (x1 - x2)**2 + (y1 - y2)**2

def average(ls):
    return float(sum(ls)) / float(len(ls))

#This is faster than just do a distance check because we only have to calculate half of it sometimes.
#Full calculation is slower, but it's faster on average.
def collided((x1, y1, r1), (x2, y2, r2)):
    x_dist = (x1 - x2)**2
    length = (r1 + r2)**2
    if x_dist < length:
        y_dist = (y1 - y2)**2
        if y_dist < length:
            return y_dist + x_dist < length
        else:
            return False
    else:
        return False

def intersect((x, y), check, radius=1, ignore_exact=False):
    for index,((cx, cy), cradius) in enumerate(check):
        if collided((x, y, radius), (cx, cy, cradius)):
            if ignore_exact and x == cx and y == cy:
                return -1
            else:
                return index

    return -1

if __name__ == '__main__':
    command_line(command_line_args(arg_synonyms=arg_synonyms))
