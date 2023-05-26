import sys
import subprocess
import time
import stat
import os

import psutil
#To install psutil, run the following command: pip install psutil

def get_params(args):
    disk_device = "/dev/sda"
    verbose = False
    max_load = 30
    xfer = 4096

    while len(args) > 0:
        if args[0] == "--max-load":
            max_load = int(args[1])
            args = args[2:]
        elif args[0] == "--xfer":
            xfer = int(args[1])
            args = args[2:]
        elif args[0] == "--verbose":
            verbose = True
            args = args[1:]
        else:
            disk_device = "/dev/" + args[0]
            disk_device = disk_device.replace("/dev//dev", "/dev")
            args = args[1:]

    return disk_device, verbose, max_load, xfer


def sum_array(array):
    total = sum(array)
    return total


def compute_cpu_load(start_use, end_use, verbose):
    diff_idle = end_use[3] - start_use[3]
    start_total = sum_array(start_use)
    end_total = sum_array(end_use)
    diff_total = end_total - start_total
    diff_used = diff_total - diff_idle

    if verbose:
        print("Start CPU time =", start_total)
        print("End CPU time =", end_total)
        print("CPU time used =", diff_used)
        print("Total elapsed time =", diff_total)

    if diff_total != 0:
        cpu_load = (diff_used * 100) / diff_total
    else:
        cpu_load = 0

    return cpu_load


def main(argv):
    disk_device, verbose, max_load, xfer = get_params(argv[1:])
    if not os.path.exists(disk_device) or not stat.S_ISBLK(os.stat(disk_device).st_mode):
        print("Unknown block device", "\"{}\"".format(disk_device))
        print("Usage:", "{} [ --max-load <load> ] [ --xfer <mebibytes> ] [ device-file ]".format(sys.argv[0]))
        sys.exit(1)
    print("Testing CPU load when reading", xfer, "MiB from", disk_device)
    print("Maximum acceptable CPU load is", max_load)
    subprocess.run(["sudo", "blockdev", "--flushbufs", disk_device])

    start_use = psutil.cpu_times()
    print("Beginning disk read....")
    subprocess.run(["sudo", "dd", "if=" + disk_device, "of=/dev/null",
                    "bs=1048576", "count=" + str(xfer)])
    print("Disk read complete!")
    end_use = psutil.cpu_times()

    cpu_load = compute_cpu_load(start_use, end_use, verbose)
    print("Detected disk read CPU load is", cpu_load)
    if cpu_load > max_load:
        print("*** DISK CPU LOAD TEST HAS FAILED! ***")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
