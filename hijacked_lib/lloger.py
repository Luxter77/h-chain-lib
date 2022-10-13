from tqdm.auto import tqdm
from enum import Enum
import datetime as dt
import pprint
import sys
import os

# COLORS!
import colorama as col

col.deinit()                        # breaks some windows systems but fixes other windows systems
col.init(strip=False, convert=True) # see https://github.com/tartley/col/issues/217

class ProgrammingError(Exception):
    "Sos tonto, amigo"

class LogType(Enum):
    DBG_  = col.Fore.LIGHTMAGENTA_EX + 'DBG_:  '
    INFO  = col.Fore.WHITE + 'INFO:  '
    WARN  = col.Fore.YELLOW + 'WARN:  '
    ERR_  = col.Fore.RED + 'ERR_:  '
    FATAL = col.Back.RED + col.Fore.BLACK + 'FATAL: '

LOG_LEVELS = {
    LogType.DBG_:  0,
    LogType.INFO:  1,
    LogType.WARN:  2,
    LogType.ERR_:  3,
    LogType.FATAL: 4,
}

class Logger:
    def __init__(self, log_dir: os.PathLike = '.', run_time: dt.datetime = dt.datetime.now(), log_level: LogType = LogType.INFO) -> None:
        self.params = {
            'run_time': run_time,
            'log_dir': log_dir,
        }

        self.log_level = LOG_LEVELS[log_level]
        self.log_file = None

    def log(self, obj: object, do_print=True, do_pprint=True, logtype: LogType = LogType.INFO):
        if self.log_file is None:
            self.log_file = open(os.path.join(self.params['log_dir'], self.params['run_time'].strftime("%Y%m%d-%H%M%S")+'.LOG'), 'w', encoding='utf-8')
        if LOG_LEVELS[logtype] >= self.log_level:
            if do_pprint:
                obj = str(pprint.pformat(obj, indent=4, width=sys.maxsize))

            if do_print:
                for line in str(obj).splitlines():
                    tqdm.write(logtype.value + line + col.Fore.RESET + col.Back.RESET)

            self.log_file.write("[" + dt.datetime.now().isoformat() + "]: " + str(obj) + "\n")
            self.log_file.flush()
            os.fsync(self.log_file)

    def display_exception(self, _=None, ex: BaseException = ProgrammingError('You forgot to pass the exception to the exception handler you dummy'), tb=None, fatal: bool = False):
        self.log(('FATAL:' if fatal else 'ERR_:') + ''.join(tb.format_exception(ex)), do_pprint=False)

    def __bool__(self) -> bool:
        return True
