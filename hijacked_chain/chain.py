from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Iterable, List, Tuple, Union
from collections import defaultdict, Counter
from collections.abc import Sequence
from unicodedata import normalize
from hijacked_log import Logger, LogTypes
from tqdm.auto import tqdm
from threading import Lock
from random import choice
import numpy as np
import gc
import os

from .patterns import PUNCTUATIONS, SIDED

def sliding_window(iterable: Iterable, size: int = 2) -> Iterable[Tuple[int]]:
    parent = iter(iterable)

    window = [START_OF_WINDOW.int] * size

    yield window

    while True:
        window.pop(0)
        try:
            window.append(next(parent))
        except StopIteration:
            window.append(END___OF_WINDOW.int)
            yield tuple(window)
            break

        yield tuple(window)

def join_prompt(prompt: Iterable, sep: str = ' ') -> str:
    res = ''

    for item in prompt:
        res += str(item) + sep

    return res

class NotThisOne():
    def __init__(self, value: str, nvalue: int) -> None:
        self.str: str = value
        self.int: int = nvalue
    def __bool__(self) -> bool:
        return False
    def __str__(self) -> str:
        # return self.str
        return ''
    def __repr__(self) -> str:
        return '<' + self.str + f': {id(self)}>'
    def __add__(self, other: object) -> str:
        return str(other)
    def lower(self) -> str:
        # return self.str.lower()
        return ''
    def __int__(self) -> int:
        return self.int

class NotYetFrozenError(Exception):
    "Chain has not yet been frozen with the freeze_chain method"

WORD_NOT__FOUND = NotThisOne('__WORD_NOT__FOUND__', 0)
START_OF_WINDOW = NotThisOne('__START_OF_WINDOW__', 1)
END___OF_WINDOW = NotThisOne('__END___OF_WINDOW__', 2)

class Chain:
    def __init__(self, depth: int = 2, ignores: List[str] = None, obs: object = object(), prune_on_add: bool = False, logger: Logger = None, treads: ThreadPoolExecutor = None) -> None:
        if (depth < 1): raise(ValueError('Chain depth must be positive.'))

        self.ignores    = (ignores if ignores else list())

        self.logger         = (logger if logger else Logger())
        self.treads         = (treads if treads else ThreadPoolExecutor(max_workers=2, thread_name_prefix='chain_multipoc_'))
        self.prune_on_add   = prune_on_add
        self.depth          = depth
        self.observer       = obs

        self.all_words  = set([
            WORD_NOT__FOUND.int,
            START_OF_WINDOW.int,
            END___OF_WINDOW.int,
        ])

        self._trans     = {
            'int2str': [WORD_NOT__FOUND, START_OF_WINDOW, END___OF_WINDOW],
            'str2int': {
                WORD_NOT__FOUND:  WORD_NOT__FOUND.int,
                START_OF_WINDOW:  START_OF_WINDOW.int,
                END___OF_WINDOW:  END___OF_WINDOW.int,
            },
        }

        self._trans_lock = Lock()
        self.chain_lock  = Lock()

        self.frozen = None
        self.chain = None

        self._init_chain()

    def _init_chain(self):
        with self.chain_lock, self._trans_lock:
            self.chain: Dict[Tuple[int], List[int]] = defaultdict(list)
            for v in self._trans['str2int']:
                self.chain[tuple([v] * self.depth)].append(v)

    @property
    def hot_entrypoint(self) -> Tuple[int]:
        with self.chain_lock:
            return tuple(self.chain[tuple([START_OF_WINDOW.int] * self.depth)])

    @property
    def frozen_entrypoint(self) -> Tuple[int]:
        if self.frozen:
            return tuple(int(w) for w in self.frozen[tuple([START_OF_WINDOW.int] * self.depth)][:, 0])
        else:
            raise(NotYetFrozenError())

    def preprocessor(self, text: str) -> str:
        text = (' ' + normalize('NFKC', text) + ' ')

        for punct in PUNCTUATIONS:
            text = text.replace(punct, f" {punct}")

        for side in SIDED:
            text = text.replace(f"{side} ", f" _{side} ").replace(f" {side}", f" {side}_ ")

        text = ' '.join(text.split())

        return text.lower()

    def posprocessor(self, text: str) -> str:
        text = normalize('NFKC', text).replace('  ', ' ')

        for punct in PUNCTUATIONS:
            text = text.replace(f" {punct}", punct)

        for side in SIDED:
            text = text.replace(f" _{side} ", f"{side} ").replace(f" {side}_ ", f" {side}")

        return ' '.join(text.split())

    def _add_id_seq(self, text: List[int]):
        with self.chain_lock:
            for window in sliding_window(iterable=text, size=(self.depth + 1)):
                self.chain[tuple(window[:-1])].append(window[-1:][0])

    def _register_seq_ids(self, text: List[str]):
        for word in text:
            with self._trans_lock:
                if word not in self._trans['str2int']:
                    _id = len(self._trans['int2str'])
                    self._trans['str2int'][word] = _id
                    self._trans['int2str'].append(word)
                    self.all_words.add(_id)

    def add_text(self, text: str, sep: str = None):
        text = self.preprocessor(text).split(sep)
        self._register_seq_ids(text)
        self._add_id_seq(self.trans(tuple(text)))
        if self.prune_on_add:
            self.prune_chain()

    def add_lines_from_file(self, file: os.PathLike, pos: int, sep: str = None):
        nt = 0
        for line in tqdm(open(file, "r", encoding="utf-8").readlines(), leave=False, position=pos, desc=f"Chaining from [ {file} ]"):
            self.add_text(line, sep)
            nt += 1
            if nt == 100:
                nt = 0
                gc.collect()

    def parallel_add_files(self, files: Sequence):
        with self.treads as pool:
            tqdm.get_lock() # threading fun
            pos = -1
            for file in tqdm(files, desc="Chaining from file contents", leave=True, position=0):
                pos += 1
                pool.submit(self.add_lines_from_file, file, pos)
            try:
                pool.shutdown(wait=True, cancel_futures=False)
            except KeyboardInterrupt:
                pool.shutdown(wait=False, cancel_futures=True)

    def prune_chain(self):
        with self.chain_lock:
            for item in tqdm(tuple(self.chain.keys()), desc="Pruning chain", leave=False):
                for i in range(len(self.chain[item]) - 1, -1, -1):
                    if self.chain[item][i] in ([START_OF_WINDOW.int, WORD_NOT__FOUND.int] + self.trans(self.ignores)):
                        del self.chain[item][i]

            for item in tqdm(tuple(SIDED + PUNCTUATIONS), desc="Polishing entrypoint", leave=False):
                item = self.trans((f'_{item}',))
                tpl = tuple([START_OF_WINDOW.int]*self.depth)
                if tpl in self.chain:
                    for i in range(len(self.chain[tpl]) - 1, -1, -1):
                        if self.chain[tpl][i] == item:
                            del self.chain[tpl][i]

    def freeze_chain(self):
        frozen = dict()
        with self.chain_lock:
            for key, value in tqdm(tuple(self.chain.items()), desc="Freezing chain", leave=False):
                c_ = Counter(value)
                frozen[key] = np.array(list([int(i), float(c_[i] / len(value))] for i in c_))
        self.frozen = frozen
        self._init_chain()
        gc.collect()

    def generate(self, prompt: str = '', lenght: int = 8, stop_on_end: bool = True, raw: bool = False, use_hot: bool = False) -> Union[str, List[int]]:
        prompt = prompt.lower().split()

        buff = self.trans(tuple(([START_OF_WINDOW] * (max([lenght, (self.depth + 1)]) - len(prompt))) + prompt))

        while buff[0] == START_OF_WINDOW.int:
            buff.pop(0)
            buff.append(self.next_word(tuple(buff[-self.depth:]), stop_on_end=stop_on_end, use_hot=use_hot))

        if raw:
            return buff

        return self.posprocessor(join_prompt(self.trans(buff)))

    def next_word(self, ids: Tuple[int], stop_on_end: bool = True, use_hot: bool = False):
        if stop_on_end and (ids[-1] in (WORD_NOT__FOUND.int, END___OF_WINDOW.int)):
            return WORD_NOT__FOUND.int
        elif self.frozen and (not use_hot):
            return self._next_frozen_word(ids, stop_on_end)
        else:
            return self._next_hot_word(ids, stop_on_end)

    def _next_hot_word(self, ids: Tuple[int], stop_on_end: bool) -> int:
        pick = START_OF_WINDOW.int
        while (pick == START_OF_WINDOW.int):
            with self.chain_lock:
                if ids in self.chain:
                    pick = choice(self.chain[ids])
                    self.logger.log([self.trans(self.chain[ids]), self.trans((pick,))], logtype=LogTypes.DBG_)
                elif stop_on_end:
                    self.logger.log([ids, WORD_NOT__FOUND.int, START_OF_WINDOW.int], logtype=LogTypes.DBG_)
                    return WORD_NOT__FOUND.int
                else:
                    pick = choice(self.hot_entrypoint)
        return pick

    def _next_frozen_word(self, ids: Tuple[int], stop_on_end: bool) -> int:
        pick = START_OF_WINDOW.int

        while (pick == START_OF_WINDOW.int):
            if ids in self.frozen:
                pick = int(np.random.choice(self.frozen[ids][:, 0], p=self.frozen[ids][:, 1]))
                self.logger.log([self.trans(self.frozen[ids][:, 0]), self.trans((pick,))], logtype=LogTypes.DBG_)
            elif stop_on_end:
                self.logger.log([ids, WORD_NOT__FOUND.int, START_OF_WINDOW.int], logtype=LogTypes.DBG_)
                return WORD_NOT__FOUND.int
            else:
                pick = choice(self.frozen_entrypoint)

        return int(pick)

    def trans(self, val: Iterable[Union[Union[int, float], str]]) -> Iterable[Union[str, int]]:
        o = []
        for item in val:
            if isinstance(item, (int, float)):
                try:
                    with self._trans_lock:
                        o.append(self._trans['int2str'][int(item)])
                except KeyError:
                    o.append(WORD_NOT__FOUND)
            elif isinstance(item, str) or (item is START_OF_WINDOW):
                try:
                    with self._trans_lock:
                        o.append(self._trans['str2int'][item])
                except KeyError:
                    o.append(WORD_NOT__FOUND.int)
        return o
