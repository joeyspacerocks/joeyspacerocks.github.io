from sys import argv
from os import path, mkdir
from datetime import datetime
import argparse
import re
from pathlib import Path
import chevron
import shutil
import markdown
import ffmpeg
import pprint

__version__ = '0.1.1'

def process_media(m):
    url = m.group(2)
    if url.endswith('.gif'):
        if path.isfile(url):
            dest = url.split('.')[0] + '.mp4'
            if not path.isfile(dest) or (path.getmtime(dest) < path.getmtime(url)):
                print(' - converting {} to mp4 ...'.format(url.split('/')[1]))
                ffmpeg.input(url).output(dest).run(quiet=True)
            return '<video autoplay="true" muted="true" loop="true"><source src="{}" type="video/mp4"></video>'.format(dest)
        else:
            print('ERROR: no such GIF - ' + url)
            return m.group(0)

    elif url.startswith('https://www.youtube.com'):
        # write embedded iframe
        pass
    else:
        return m.group(0)

def read_post(f):
    post = {
        'content': '',
        'icon': 'newspaper-o'
    }

    md_content = ''
    with open(f) as fh:
        header = True
        for line in fh:
            if header:
                if ':' in line:
                    parts = line.split(':', 2)
                    post[parts[0]] = parts[1].strip()
                else:
                    header = False
            else:
                md_content += line

    post['blurb'] = md_content.split('.')[0] + ' ...'

    md_content = re.sub(r'\!\[(.*?)\]\((.+?)\)', process_media, md_content)
    post['content'] = markdown.markdown(md_content)

    date = datetime.strptime(post['date'], '%Y%m%d')
    post['nice_date'] = date.strftime('%d %b %Y')

    return post

def write_html(data, tmpl_path, tmpl_file, dest_path, dest_file):
    src = path.join(tmpl_path, tmpl_file)
    dest = path.join(dest_path, dest_file)

    with open(src, 'r') as template:
        with open(dest, 'w') as out:
            out.write(chevron.render(template, data))

def main():
    src_path = 'posts'
    dest_path = 'out'
    tmpl_path = 'templates'

    if not path.exists(dest_path):
        mkdir(dest_path)
    
    index = []
    for f in Path(src_path).iterdir():
        if f.name.endswith(".txt"):
            post = read_post(f)
            # dest_file = path.splitext(f.name)[0] + '.html'
            dest_file = post['url'] + '.html'
            write_html(post, tmpl_path, 'post.html', dest_path, dest_file)
            index.append(post)

    index = sorted(index, key = lambda p: p['date'], reverse = True)
    write_html({'posts': index}, tmpl_path, 'index.html', dest_path, 'index.html')

    for f in Path(dest_path).iterdir():
        shutil.copy(f.absolute(), '.')

if __name__ == '__main__':
    main()
