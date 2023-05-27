import sys
import subprocess
import time
import stat
import os
import argparse
import logging

import psutil
#install psutil by using command "pip3 install psutil"

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FILE = "disk_cpu_load.log"
DEFAULT_DISK_DEVICE = "/dev/sda"
DEFAULT_MAX_LOAD = 30
DEFAULT_XFER = 4096

logger = logging.getLogger(__name__)


def setup_logging():
    logger.setLevel(logging.INFO)

    # Create the log file handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create the stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def get_params(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-load", type=int, default=DEFAULT_MAX_LOAD,
                        help="The maximum acceptable CPU load, as a percentage. (default: %(default)s)")
    parser.add_argument("--xfer", type=int, default=DEFAULT_XFER,
                        help="The amount of data to read from the disk, in mebibytes. (default: %(default)s)")
    parser.add_argument("--verbose", action="store_true", help="Produce more verbose output")
    parser.add_argument("device_file", nargs="?", default=DEFAULT_DISK_DEVICE,
                        help="The WHOLE-DISK device filename (default: %(default)s)")
    args = parser.parse_args(args)
    return args.device_file, args.verbose, args.max_load, args.xfer


def sum_array(array):
    total = sum(array)
    return total


def compute_cpu_load(start_use, end_use, verbose):
    diff_idle = end_use.idle - start_use.idle
    start_total = sum_array(start_use)
    end_total = sum_array(end_use)
    diff_total = end_total - start_total
    diff_used = diff_total - diff_idle

    if verbose:
        logger.info("Start CPU time = %s", start_total)
        logger.info("End CPU time = %s", end_total)
        logger.info("CPU time used = %s", diff_used)
        logger.info("Total elapsed time = %s", diff_total)

    cpu_load = (diff_used * 100) / diff_total if diff_total != 0 else 0
    return cpu_load


def validate_disk_device(disk_device):
    if not os.path.exists(disk_device) or not stat.S_ISBLK(os.stat(disk_device).st_mode):
        logger.error("Unknown block device: %s", disk_device)
        raise ValueError("Invalid disk device")


def perform_disk_read(disk_device, xfer):
    subprocess.run(["sudo", "blockdev", "--flushbufs", disk_device])
    logger.info("Beginning disk read....")
    subprocess.run(["sudo", "dd", "if=" + disk_device, "of=/dev/null",
                    "bs=1048576", "count=" + str(xfer)])
    logger.info("Disk read complete!")

def main(argv):
    setup_logging()

    disk_device, verbose, max_load, xfer = get_params(argv)
    try:
        validate_disk_device(disk_device)
    except ValueError:
        logger.error("Invalid disk device: %s", disk_device)
        sys.exit(1)

    logger.info("Testing CPU load when reading %s MiB from %s", xfer, disk_device)
    logger.info("Maximum acceptable CPU load is %s", max_load)

    start_use = psutil.cpu_times()
    perform_disk_read(disk_device, xfer)
    end_use = psutil.cpu_times()

    cpu_load = compute_cpu_load(start_use, end_use, verbose)
    logger.info("Detected disk read CPU load is %s", cpu_load)


if __name__ == "__main__":
    main(sys.argv[1:])
