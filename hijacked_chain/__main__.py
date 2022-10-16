from .chain import Logger, LogTypes, Chain
from typing import Tuple

from glob import glob
import os

def main() -> Tuple[Chain, Logger]:
    "This one is for demo/testing porpuses :P"
    l = Logger(log_dir='LOGs', log_level=LogTypes.DBG_)
    c = Chain(5, [], object(), False, l, None)
    files = list(glob(os.path.join("TXTs", "*.txt")))
    c.parallel_add_files(files)
    c.prune_chain()
    c.freeze_chain()
    print(c.generate(lenght=15))
    return (c, l)

if __name__ == '__main__':
    (c_, l_) = main()
