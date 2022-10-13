from .chain import Logger, Chain

import psutil
import glob
import os

PID = os.getpid()

def main():
    logger = Logger(log_dir='LOGs')

    process = psutil.Process(PID)

    logger.log('PID: ' + str(PID))
    logger.log('process: ' + str(process))

    logger.log('before chain instance:')
    logger.log(process.memory_info())
    c = Chain(5, [], object(), False, logger, None)

    files = list(glob.glob(os.path.join("TXTs", "*.txt")))

    logger.log('before files add:')
    logger.log(process.memory_info())
    c.parallel_add_files(files)

    logger.log('before prune:')
    logger.log(process.memory_info())
    c.prune_chain()

    logger.log('before freeze:')
    logger.log(process.memory_info())
    c.freeze_chain()

    logger.log('before generate:')
    logger.log(process.memory_info())
    print(c.generate(lenght=15))

    return c


if __name__ == '__main__':
    main()
