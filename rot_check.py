
from enum import IntEnum
import io
import os
import time

import click
import requests
import rotten_bites


@click.command()
@click.argument('directory')
@click.option('-t', '--to', required=True)
@click.option('-f', '--from', 'from_', required=True)
@click.option('-d', '--domain', required=True)
@click.option('-k', '--api_key', required=True)
def main(directory, to, from_, domain, api_key):
    added_files = []
    update_files = []
    nothing_files = []
    missing_files = []
    hash_error_files = []
    file_error_files = []

    def added_cb(file):
        """Print when file is added."""
        nonlocal added_files
        added_files.append(file)

    def updated_cb(file):
        """Print when file is updated."""
        nonlocal update_files
        update_files.append(file)

    def nothing_cb(file):
        """Print when nothing happens to a file."""
        nonlocal nothing_files
        nothing_files.append(file)

    def file_error_cb(path, file, error):
        """Print when file has an error."""
        file_error_files.append((path, file, error))

    def hash_error_cb(old_file, new_file):
        """Print when file has an hash error."""
        hash_error_files.append((old_file, new_file))

    def missing_cb(file):
        """Print when file is missing."""
        nonlocal missing_files
        missing_files += 1

    rotten_bites.run(directory, added_cb=added_cb, updated_cb=updated_cb,
                     nothing_cb=nothing_cb, file_error_cb=file_error_cb,
                     hash_error_cb=hash_error_cb, missing_cb=missing_cb)

    # Send email
    text = io.StringIO()
    text.write('{} files scanned, {} new, {} updated, {} missing, {} errors.'.format(
               len(added_files) + len(update_files) + len(nothing_files) + len(hash_error_files),
               len(added_files), len(update_files), len(missing_files), len(hash_error_files)))

    text.write('\n\n')

    def print_files(files):
        def get_path(file):
            return os.path.abspath(os.path.join(file.path, file.name))

        return '\n'.join(['\t{}'.format(get_path(file))
                          for file in files])

    if hash_error_files:
        text.write('Files with bit rot:\n')
        text.write(print_files(hash_error_files))

    if file_error_files:
        text.write('Files unable to open:\n')
        text.write(print_files(file_error_files))

    if added_files:
        text.write('Added files:\n')
        text.write(print_files(added_files))

    if update_files:
        text.write('Updated files:\n')
        text.write(print_files(update_files))

    if missing_files:
        text.write('Missing files:\n')
        text.write(print_files(missing_files))

    request = requests.post(
        'https://api.mailgun.net/v3/{0}/messages'.format(domain),
        auth=('api', api_key),
        data={'from': from_,
              'to': to,
              'subject': 'Rot Check ({})'.format(time.ctime()),
              'text': text.getvalue()})

    if request.status_code != 200 and request.text == 'Forbidden':
        print("Error: Incorrect API key")

    result = request.json()

    if 'Domain not found' in result['message']:
        print("Error: {}".format(result['message']))


if __name__ == '__main__':
    main()
