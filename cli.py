from enum import IntEnum
import os

import click
import pathspec
import rotten_bits


class Logging(IntEnum):
    quiet = 1
    normal = 2
    verbose = 3


@click.command()
@click.argument('directory', default='.')
@click.option('--delete', default=False, is_flag=True)
@click.option('--ignore-list', type=click.File('r'))
@click.option('-q', '--quiet', 'logging', flag_value=Logging.quiet,
              help="")
@click.option('-v', '--verbose', 'logging', flag_value=Logging.verbose,
              help="")
@click.option('--verify', default=False, is_flag=True,
              help="Verify hashes without updating.")
def main(directory, delete, ignore_list, verify, logging):
    """
    Runs rotten_bits. It checks to something.

    directory argument.

    Status codes:
    'E'     error, md5 mismatch
    'a'     add to index
    'u'     update md5
    ' '     not modified (with verbose)
    '?'     could not read file
    """

    spec = pathspec.PathSpec.from_lines(pathspec.GitIgnorePattern, ignore_list or [])

    print(spec)
    exit()

    logging = logging or Logging.normal
    added_files = 0
    update_files = 0
    nothing_files = 0
    hash_error_files = 0
    deleted_files = 0

    print(ignore_list)
    exit()

    def vprint(msg, log_level):
        # print(log_level, logging)
        if logging >= log_level:
            click.echo(msg)

    def added_cb(file):
        nonlocal added_files

        added_files += 1
        vprint("a  {}".format(os.path.join(file.path, file.name)), Logging.normal)

    def updated_cb(file):
        nonlocal update_files

        update_files += 1
        vprint("u  {}".format(os.path.join(file.path, file.name)), Logging.normal)

    def nothing_cb(file):
        nonlocal nothing_files

        nothing_files += 1
        vprint("   {}".format(os.path.join(file.path, file.name)), Logging.verbose)

    def file_error_cb(path, file, error):
        vprint("?  {}".format(os.path.join(file.path, file.name)), Logging.normal)

    def hash_error_cb(old_file, new_file):
        nonlocal hash_error_files

        hash_error_files += 1
        vprint("E  {}".format(os.path.join(old_file.path, old_file.name)), Logging.normal)

    def deleted_cb(file):
        nonlocal deleted_files

        deleted_files += 1
        vprint("d  {}".format(os.path.join(file.path, file.name)), Logging.normal)

    if delete:
        rotten_bits.delete_check_files(directory)
        return

    rotten_bits.run(directory, added_cb=added_cb, updated_cb=updated_cb,
                    nothing_cb=nothing_cb, file_error_cb=file_error_cb,
                    hash_error_cb=hash_error_cb, deleted_cb=deleted_cb,
                    just_verify=verify, ignore=ignore_list)

    vprint("", Logging.normal)
    vprint(
        '{} files scanned, {} new, {} updated, {} missing, {} errors.'.format(
        added_files + update_files + nothing_files + hash_error_files,
        added_files, update_files, deleted_files, hash_error_files),
        Logging.normal)

if __name__ == '__main__':
    main()
