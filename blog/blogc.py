from sys import argv
from os import path, mkdir
from datetime import datetime
import argparse
import re
from pathlib import Path
import chevron
import markdown
import pprint

__version__ = '0.1.1'

def process_media(m):
    url = m.group(2)
    if url.endswith('.mp4'):
        return '<video autoplay="true" muted="true" loop="true"><source src="{}" type="video/mp4"></video>'.format(url)
    elif url.startswith('https://www.youtube.com'):
        return '<iframe src="{}" frameborder="0" allowfullscreen></iframe>'.format(url)
    else:
        return m.group(0)

def read_post(f):
    post = {
        'content': '',
        'icon': 'newspaper-o'
    }

    md_content = ''
    blurb = None
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
                if not blurb:
                    blurb = line
                else:
                    md_content += line

    post['blurb'] = blurb
    post['tags'] = post.get('tags', '').split(',')

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
    print('Generating blog ... ')

    src_path = 'posts'
    dest_path = '.'
    tmpl_path = 'templates'

    if not path.exists(dest_path):
        mkdir(dest_path)

    index_pages = { 'index': [] }

    for f in Path(src_path).iterdir():
        if f.name.endswith(".txt"):
            post = read_post(f)
            dest_file = post.get('url', path.splitext(f.name)[0] + '.html') + '.html'
            write_html(post, tmpl_path, 'post.html', dest_path, dest_file)

            for t in post['tags']:
                if t in index_pages:
                    index_pages[t].append(post)
                else:
                    index_pages[t] = [post]

            index_pages['index'].append(post)

    for tag, posts in index_pages.items():
        posts = sorted(posts, key = lambda p: p['date'], reverse = True)

        tags = []
        for t in index_pages:
            tags.append({ 'tag': t, 'active': t == tag })

        data = {'tags': tags, 'tag': tag, 'posts': posts}
        write_html(data, tmpl_path, 'index.html', dest_path, tag + '.html')

if __name__ == '__main__':
    main()
