import glob
import os
import re
import shutil
import sys
import zipfile

from lxml.html import parse


def find_paths(config):
    input_file_path = sys.argv[1]

    if not os.path.exists(input_file_path):
        sys.stderr.write('%s does not exist.' % input_file_path)
        sys.exit(1)

    ext = os.path.splitext(input_file_path)[1]
    if ext != '.epub':
        sys.stderr.write('%s is not a valid input file.' % input_file_path)
        sys.exit(1)

    output_file_path = convert(os.path.dirname(input_file_path), input_file_path, config)
    (trunk, ext) = os.path.splitext(output_file_path)
    output_file_path = '%s.converted%s' % (trunk, ext)


    extracted_path = find_extracted_path(input_file_path)

    print('Trying extracting %s to %s' % (input_file_path, extracted_path))
    zip_file = zipfile.ZipFile(input_file_path)
    zip_file.extractall(extracted_path)

    return input_file_path, extracted_path, output_file_path


def find_extracted_path(input_path):
    candidate = os.path.splitext(input_path)[0]
    if os.path.exists(candidate):
        match = re.match('(.*)-(\d+)', candidate)
        if match:
            candidate = match.group(1)
            digit = int(match.group(2)) + 1
        else:
            digit = 1
        candidate = "%s-%d" % (candidate, digit)
        return find_extracted_path(candidate)
    else:
        return candidate


def find_opf_path(input_path):
    metadata_file = os.path.join(input_path, "META-INF", "container.xml")
    if os.path.isfile(metadata_file):
        metadata = parse(metadata_file)
        for root_file in metadata.iter('rootfile'):
            opf_file = root_file.attrib['full-path']
            opf_path = os.path.join(input_path, opf_file)
            if os.path.isfile(opf_path):
                return opf_path
    else:
        opfs = glob.glob(os.path.join(input_path, '*.opf'))
        if len(opfs):
            return opfs[0]
    return None


def find_files_to_convert(opf_path):
    opf = parse(opf_path)
    files_need_convert = [opf_path]
    types = ['application/x-dtbncx+xml', 'application/xhtml+xml', 'text/x-oeb1-document']
    for item in opf.iter('item'):
        media_type = item.attrib['media-type']
        href = item.attrib['href']
        path = os.path.join(os.path.dirname(opf_path), href)
        if os.path.isfile(path):
            if media_type in types:
                files_need_convert.append(path)

    return files_need_convert


def convert(path, string, config):
    string_old = os.path.join(path, 'string.old.txt')
    string_new = os.path.join(path, 'string.new.txt')
    ofile = open(string_old, 'w', encoding='utf-8')
    ofile.write(string)
    ofile.close()

    cmd = 'opencc -i "%s" -o "%s" -c "%s"' % (string_old, string_new, config)
    os.system(cmd)

    ifile = open(string_new, 'r', encoding='utf-8')
    new_string = ifile.read()
    ifile.close()

    os.remove(string_old)
    os.remove(string_new)
    return new_string


def convert_files(files, config):
    for file in files:
        print('Converting file: %s' % file)
        output_file = '%s.tmp' % file
        cmd = 'opencc -i "%s" -o "%s" -c "%s"' % (file, output_file, config)
        os.system(cmd)
        os.remove(file)
        os.rename(output_file, file)


def add_dir_to_zip(archive, base, current):
    for f in os.listdir(os.path.join(base, current)):
        file_name = os.path.join(current, f)
        full_name = os.path.join(base, file_name)
        if os.path.isdir(full_name):
            add_dir_to_zip(archive, base, file_name)
        else:
            archive.write(full_name, file_name)


def repack_files(extracted_path, output_file_path):
    (trunk, ext) = os.path.splitext(output_file_path)
    if os.path.isfile(output_file_path):
        output_file_path = '%s.new%s' % (trunk, ext)
        if os.path.isfile(output_file_path):
            print('Removing existing file %s', output_file_path)
            os.remove(output_file_path)
    print('Repacking converted files into %s' % output_file_path)
    epub = zipfile.ZipFile(output_file_path, "w", zipfile.ZIP_DEFLATED)
    add_dir_to_zip(epub, extracted_path, '.')
    epub.close()

    print('Removing temporary directory %s' % extracted_path)
    shutil.rmtree(extracted_path)


def main():
    if len(sys.argv) != 3:
        sys.stderr.write('usage: epubcc.py <infile> config \n <infile> must be ".epub" file.')
        sys.exit(1)

    config = sys.argv[-1]
    (input_file_path, extracted_path, output_file_path) = find_paths(config)
    opf_path = find_opf_path(extracted_path)

    if opf_path:
        files_need_convert = find_files_to_convert(opf_path)
        if len(files_need_convert):
            convert_files(files_need_convert, config)
        repack_files(extracted_path, output_file_path)
    else:
        sys.stderr.write('%s is not in Open Packaging Format.' % extracted_path)
        sys.exit(1)


if __name__ == '__main__':
    main()
