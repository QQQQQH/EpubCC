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
    if ext not in [".epub", ".mobi"]:
        sys.stderr.write('%s is not a valid input file.' % input_file_path)
        sys.exit(1)

    output_file_path = convert(os.path.dirname(input_file_path), input_file_path, config)

    extracted_path = find_extracted_path(input_file_path)

    print('Trying extracting %s to %s' % (input_file_path, extracted_path))
    if ext == '.epub':
        zip_file = zipfile.ZipFile(input_file_path)
        zip_file.extractall(extracted_path)
    '''
    else:
        # Otherwise it's a mobi, use mobiunpack
        mobiunpack.unpackBook(input_file_path, extracted_path)
    '''

    return input_file_path, extracted_path, output_file_path


def find_extracted_path(input_path):
    candidate = os.path.splitext(input_path)[0]
    if os.path.exists(candidate):
        match = re.match('(.*)-(\d+)', candidate)
        if match:
            print(match.group(1))
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
        # Otherwise it's not in Open Container Format, look for opf in
        # the hard way
        opfs = glob.glob(os.path.join(input_path, '*.opf'))
        if len(opfs):
            return opfs[0]
    return None


def find_files_to_convert(opf_path):
    opf = parse(opf_path)
    files_need_convert = [opf_path]
    files_other = []
    types = ['application/x-dtbncx+xml', 'application/xhtml+xml', 'text/x-oeb1-document']
    for item in opf.iter('item'):
        media_type = item.attrib['media-type']
        href = item.attrib['href']
        path = os.path.join(os.path.dirname(opf_path), href)
        print(path)
        if os.path.isfile(path):
            if media_type in types:
                files_need_convert.append(path)
            else:
                files_other.append(path)

    return [files_need_convert, files_other]


def convert(path, string, config):
    string_old = os.path.join(path, 'string.old.txt')
    string_new = os.path.join(path, 'string.new.txt')
    ofile = open(string_old, 'w', encoding='utf-8')
    ofile.write(string)
    ofile.close()

    cmd = 'opencc -i "%s" -o "%s" -c "%s"' % (string_old, string_new, config)
    # print('\n\n\n!!!!!!!!!!!!!!!\n' + string +'\n\n' + cmd + '\n\n\n')
    # print(config)
    os.system(cmd)

    ifile = open(string_new, 'r', encoding='utf-8')
    new_string = ifile.read()
    ifile.close()

    os.remove(string_old)
    os.remove(string_new)
    return new_string


def convert_file_name(files, config):
    for file in files:
        dir_name = os.path.dirname(file)
        file_name = os.path.basename(file)
        print('Converting file name: %s' % file)
        os.rename(file, os.path.join(dir_name, convert(dir_name, file_name, config)))


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
        filename = os.path.join(current, f)
        fullname = os.path.join(base, filename)
        if os.path.isdir(fullname):
            add_dir_to_zip(archive, base, filename)
        else:
            archive.write(fullname, filename)


def repack_files(extracted_path, output_file_path, opf_path):
    (trunk, ext) = os.path.splitext(output_file_path)
    if os.path.isfile(output_file_path):
        print('Removing existing file')
        os.remove(output_file_path)
    print('Repacking converted files into %s' % output_file_path)
    if ext == '.epub':
        # epub is just normal zip file with a special extension
        epub = zipfile.ZipFile(output_file_path, "w", zipfile.ZIP_DEFLATED)
        add_dir_to_zip(epub, extracted_path, '.')
        epub.close()

    '''
    else:
        # Otherwise it's a mobi file, use kindlegen to repack
        cmd_args = []
        output_file = os.path.basename(output_file_path)
        cmd_args = ['kindlegen', opf_path, '-c2', '-verbose', '-o', output_file]
        p = subprocess.Popen(cmd_args, cwd=extracted_path)
        p.wait()

    if ext == '.mobi':
        # KindleGen puts output file under the same directory as the input file.
        original_output_path = os.path.join(extracted_path,
                                            os.path.basename(output_file_path))
        # KindleGen introduced redundant data, use kindlestrip to remove that.
        data_file = file(original_output_path, 'rb').read()
        strippedFile = kindlestrip.SectionStripper(data_file)
        outf = file(output_file_path, 'wb')
        outf.write(strippedFile.getResult())
        outf.close()
    '''
    print('Removing temporary directory %s' % extracted_path)
    shutil.rmtree(extracted_path)


def main():
    if len(sys.argv) != 3:
        sys.stderr.write('usage: epubcc.py <infile> config')
        sys.exit(1)

    config = sys.argv[-1]
    (input_file_path, extracted_path, output_file_path) = find_paths(config)
    opf_path = find_opf_path(extracted_path)

    if opf_path:
        files = find_files_to_convert(opf_path)
        files_need_convert = files[0]
        files_all = files[0] + files[1]
        if len(files_need_convert):
            convert_files(files_need_convert, config)
            convert_file_name(files_all, config)
        repack_files(extracted_path, output_file_path, opf_path)
    else:
        sys.stderr.write('%s is not in Open Packaging Format.' % extracted_path)
        sys.exit(1)


if __name__ == '__main__':
    main()
