#!/usr/bin/python

'''
Run Trinity
Author Byoungnam Min on Nov 18, 2015
'''

# Import modules
import sys
import os
from glob import glob
from argparse import ArgumentParser

# Get Logging
this_path = os.path.realpath(__file__)
this_dir = os.path.dirname(this_path)
sys.path.append(this_dir)
from set_logging import set_logging

# Parameters
max_intron = 2000
max_memory = '10G'


# Main function
def main(argv):
    argparse_usage = (
        'run_trinity.py -b <bam_files> -o <output_dir> -l <log_dir> '
        '-p <project_name> -c <num_cores> -C <config_file>'
    )
    parser = ArgumentParser(usage=argparse_usage)
    parser.add_argument(
        "-b", "--bam_files", dest="bam_files", nargs='+',
        help="Sorted BAM files generated by HISAT2"
    )
    parser.add_argument(
        "-o", "--output_dir", dest="output_dir", nargs=1,
        help="Root directory where resulting files would be written"
    )
    parser.add_argument(
        "-l", "--log_dir", dest="log_dir", nargs=1,
        help="Log directory"
    )
    parser.add_argument(
        "-p", "--project_name", dest="project_name", nargs=1,
        help="Output prefix for resulting files without space"
    )
    parser.add_argument(
        "-c", "--num_cores", dest="num_cores", nargs=1,
        help="Number of cores to be used"
    )
    parser.add_argument(
        "-C", "--config_file", dest="config_file", nargs=1,
        help="Config file generated by check_dependencies.py"
    )

    args = parser.parse_args()
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir[0])
    else:
        print '[ERROR] Please provide OUTPUT DIRECTORY'
        sys.exit(2)

    if args.log_dir:
        log_dir = os.path.abspath(args.log_dir[0])
    else:
        print '[ERROR] Please provide LOG DIRECTORY'
        sys.exit(2)

    if args.bam_files:
        bam_files = [os.path.abspath(x) for x in args.bam_files]
    else:
        print '[ERROR] Please provide BAM FILES'
        sys.exit(2)

    if args.project_name:
        project_name = args.project_name[0]
    else:
        print '[ERROR] Please provide PROJECT NAME'
        sys.exit(2)

    if args.num_cores:
        num_cores = args.num_cores[0]
    else:
        print '[ERROR] Please provide NUMBER OF CORES'
        sys.exit(2)

    if args.config_file:
        config_file = os.path.abspath(args.config_file[0])
    else:
        print '[ERROR] Please provide CONFIG FILE'
        sys.exit(2)

    # Create necessary dirs
    create_dir(output_dir, log_dir)

    # Set logging
    log_file = os.path.join(log_dir, 'pipeline', 'run_trinity.log')
    global logger_time, logger_txt
    logger_time, logger_txt = set_logging(log_file)

    # Check bamfile
    bam_files = [x for x in bam_files if glob(x)]
    if not bam_files:
        logger_txt.debug('[ERROR] You provided wrong BAM FILES. Please check')
        sys.exit(2)

    # Run functions :)
    trinity_bin = parse_config(config_file)
    run_trinity(
        bam_files, output_dir, log_dir, project_name, num_cores,
        trinity_bin
    )


# Define functions
def import_file(input_file):
    with open(input_file) as f_in:
        txt = (line.rstrip() for line in f_in)
        txt = list(line for line in txt if line)
    return txt


def create_dir(output_dir, log_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    output_base = os.path.basename(output_dir)
    log_output_dir = os.path.join(log_dir, output_base)
    if not os.path.exists(log_output_dir):
        os.mkdir(log_output_dir)

    log_pipeline_dir = os.path.join(log_dir, 'pipeline')
    if not os.path.exists(log_pipeline_dir):
        os.mkdir(log_pipeline_dir)


def parse_config(config_file):
    config_txt = import_file(config_file)
    for line in config_txt:
        if line.startswith('TRINITY_PATH='):
            trinity_bin = line.replace('TRINITY_PATH=', '')
            break
    return trinity_bin


def run_trinity(
    bam_files, output_dir, log_dir, project_name, num_cores, trinity_bin
):
    output_base = os.path.basename(output_dir)
    # Trinity --genome_guided_bam rnaseq_alignments.csorted.bam
    # --max_memory 50G --genome_guided_max_intron 2000 --CPU 6
    for bam_file in bam_files:
        prefix = (
            os.path.splitext(os.path.basename(bam_file))[0]
            .split('_')[0]
        )
        outdir = os.path.join(output_dir, 'trinity_%s' % (prefix))

        new_output = os.path.join(outdir, 'Trinity_%s.fasta' % (prefix))
        logger_time.debug('START: Trinity for %s' % (prefix))
        if not os.path.exists(new_output):
            log_file = os.path.join(
                log_dir, output_base, 'trinity_%s.log' % (prefix)
            )
            command = (
                '%s --genome_guided_bam %s --genome_guided_max_intron %s '
                '--max_memory %s --CPU %s --output %s --jaccard_clip > '
                '%s 2>&1' % (
                    trinity_bin, bam_file, max_intron, max_memory, num_cores,
                    outdir, log_file
                )
            )
            logger_txt.debug('[Run] %s' % (command))
            os.system(command)

            # Rename the file
            trinity_output = os.path.join(outdir, 'Trinity-GG.fasta')
            os.rename(trinity_output, new_output)

        else:
            logger_txt.debug('Running Trinity has already been finished %s' % (
                prefix)
            )

        logger_time.debug('DONE : Trinity for %s' % (prefix))


if __name__ == "__main__":
    main(sys.argv[1:])