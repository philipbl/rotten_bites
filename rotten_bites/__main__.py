"""CLI portion of Rotten Bites."""
# pylint: disable=no-value-for-parameter
from enum import IntEnum
import os

import click
import rotten_bites


class Logging(IntEnum):
    """Use to determine what gets printed."""

    quiet = 1
    normal = 2
    verbose = 3


def read_ignore_list(file):
    """
    Convert file to a list of ignored files/folders.

    Takes care of removing white spaces and comments.
    """
    for line in file or []:
        line = line.strip()

        # Ignore empty lines and comments
        if line == '' or line[0] == '#':
            continue

        yield line


@click.command()
@click.argument('directory')
@click.option('--delete', is_flag=True,
              help='Delete all .bit_check files.')
@click.option('-n', '--dry-run', is_flag=True,
              help='Run without making any changes. No .bit_check files are '
                   'created or updated')
@click.option('--ignore-list', type=click.File('r'),
              help='List of files and folders to ignore. Similar syntax to '
                   '.gitignore files. "-" can be used to read from stdin.')
@click.option('-q', '--quiet', 'logging', flag_value=Logging.quiet,
              help='Turn off all output except for hash errors.')
@click.option('-v', '--verbose', 'logging', flag_value=Logging.verbose,
              help='Display all files that are scanned, even if they haven\'t'
                   ' changed')
@click.option('--verify', default=False, is_flag=True,
              help='Verify hashes without updating.')
# pylint: disable=too-many-arguments,too-many-locals
def main(directory, delete, dry_run, ignore_list, verify, logging):
    """
    Run CLI.

    Given a directory, rotten bites calculates the sha1 hash of every file
    and stores it in .bit_check files. Once stored, subsequent checks will see
    if the hash has changed, detecting bit rot.

    Status codes:

        'E'     error, sha1 mismatch

        'a'     add to index

        'u'     update sha1

        ' '     not modified (shown only with verbose)

        '?'     could not read file (permission denied or file no longer
                exists)
    """
    ignore_list = read_ignore_list(ignore_list)
    logging = logging or Logging.normal
    added_files = 0
    update_files = 0
    nothing_files = 0
    hash_error_files = 0
    missing_files = 0

    def vprint(msg, log_level):
        """Print depending on the log level."""
        if logging >= log_level:
            click.echo(msg)

    def added_cb(file):
        """Print when file is added."""
        nonlocal added_files

        added_files += 1
        vprint("a  {}".format(os.path.join(file.path, file.name)),
               Logging.normal)

    def updated_cb(file):
        """Print when file is updated."""
        nonlocal update_files

        update_files += 1
        vprint("u  {}".format(os.path.join(file.path, file.name)),
               Logging.normal)

    def nothing_cb(file):
        """Print when nothing happens to a file."""
        nonlocal nothing_files

        nothing_files += 1
        vprint("   {}".format(os.path.join(file.path, file.name)),
               Logging.verbose)

    def file_error_cb(path, file, error):
        """Print when file has an error."""
        vprint("?  {}".format(os.path.join(path, file)), Logging.normal)

    def hash_error_cb(old_file, new_file):
        """Print when file has an hash error."""
        nonlocal hash_error_files

        hash_error_files += 1
        vprint("E  {}".format(os.path.join(old_file.path, old_file.name)),
               Logging.quiet)

    def missing_cb(file):
        """Print when file is missing."""
        nonlocal missing_files

        missing_files += 1
        vprint("d  {}".format(os.path.join(file.path, file.name)),
               Logging.normal)

    if delete:
        rotten_bites.delete_check_files(directory)
        return

    rotten_bites.run(directory, added_cb=added_cb, updated_cb=updated_cb,
                     nothing_cb=nothing_cb, file_error_cb=file_error_cb,
                     hash_error_cb=hash_error_cb, missing_cb=missing_cb,
                     just_verify=verify, ignore=ignore_list, dry_run=dry_run)

    vprint("", Logging.normal)
    if dry_run:
        click.echo('** DRY-RUN **')
    vprint(
        '{} files scanned, {} new, {} updated, {} missing, {} errors.'.format(
            added_files + update_files + nothing_files + hash_error_files,
            added_files, update_files, missing_files, hash_error_files),
        Logging.normal)

if __name__ == '__main__':
    main()
