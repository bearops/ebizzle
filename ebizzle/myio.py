class Color(object):
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34


def _print(*messages, **kwargs):
    if not messages:
        print ''
        return

    elif len(messages) == 1:
        try:
            messages = messages[0].split('\n')
        except AttributeError:
            pass

    color = kwargs.get('color', None)

    for message in messages:
        if color:
            print "\033[00;%sm%s\033[0m" % (color, message)
        else:
            print message


def success(*messages):
    _print(*messages, color=Color.GREEN)


def error(*messages, **kwargs):
    _print(*messages, color=Color.RED)


def info(*messages):
    _print(*messages, color=Color.BLUE)


def echo(*messages):
    _print(*messages)
