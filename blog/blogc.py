from sys import argv
from os import path, mkdir
from datetime import datetime
import pytz
import argparse
import re
from pathlib import Path
import chevron
import markdown
import pprint
from feedgen.feed import FeedGenerator
import ffmpeg
import urllib.request

__version__ = '0.1.1'

image_path = 'images'

def thumb_file(f):
    return path.join(image_path, 'th_' + f)

def process_media(m):
    image_path = 'images'

    url = m.group(2)
    if url.endswith('.mp4'):
        return '<video autoplay="true" muted="true" loop="true"><source src="{}" type="video/mp4"></video>'.format(url)
    elif url.startswith('https://www.youtube.com'):
        return '<iframe src="{}" frameborder="0" allowfullscreen></iframe>'.format(url)
    else:
        return m.group(0)

# find first image/video and generate image from it
def generate_thumb(md_content, post_url):
    image_file = thumb_file(post_url + '.png')
    
    if not path.isfile(image_file):
        m = re.search(r'\!\[(.*?)\]\((.+?)\)', md_content)
        if not m:
            return None

        url = m.group(2)

        if url.startswith('https://www.youtube.com'):
            video_id = url.split('/')[-1]
            image_url = 'https://img.youtube.com/vi/{}/0.jpg'.format(video_id)
            urllib.request.urlretrieve(image_url, image_file)

        else:
            ffmpeg.input(url).output(image_file, vframes=1).run(quiet=True)

    return image_file

def read_post(f):
    print('Processing post source file: ' + f.name)

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

    if not ('url' in post):
        post['url'] = path.splitext(path.basename(f))[0]

    post['thumb'] = generate_thumb(md_content, post['url'])
    post['thumb'] = post['thumb'] or path.join(image_path, post['banner'])
        

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
    page_size = 5

    if not path.exists(dest_path):
        mkdir(dest_path)

    index_pages = { 'index': [] }
    all_posts = []

    for f in Path(src_path).iterdir():
        if f.name.endswith(".txt"):
            post = read_post(f)
            all_posts.append(post)
            dest_file = post['url'] + '.html'
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

        page_posts = []
        page = 0
        page_count = int(len(posts) / page_size) + 1

        for p in posts:
            page_posts.append(p)
            if len(page_posts) == page_size:
                write_index_page(tags, tag, page, page_count, page_posts, tmpl_path, dest_path)
                page += 1
                page_posts.clear()

        if len(page_posts) > 0:
            write_index_page(tags, tag, page, page_count, page_posts, tmpl_path, dest_path)

    generate_rss(all_posts)
    print('Finished')

def index_filename(tag, page):
    return (tag if page == 0 else '{}_{}'.format(tag, page + 1)) + '.html'

def write_index_page(tags, tag, page, page_count, posts, tmpl_path, dest_path):
    nav = {}
    if page > 0:
        nav['prev'] = index_filename(tag, page - 1)
    if page < page_count - 1:
        nav['next'] = index_filename(tag, page + 1)
    if page_count > 1:
        nav['pages'] = []
        for p in range(0, page_count):
            nav['pages'].append({
                'page': p + 1, 
                'url': index_filename(tag, p),
                'active': page == p
            })

    data = {'tags': tags, 'tag': tag, 'posts': posts, 'nav': nav}
    write_html(data, tmpl_path, 'index.html', dest_path, index_filename(tag, page))

def generate_rss(posts):
    print('Generating RSS feed ...')

    fg = FeedGenerator()
    fg.id('https://fistfulofsquid.com/blog')
    fg.title('Fistful of Squid Blog')
    fg.description('A blog by Joe, a part-time games developer')
    fg.author( {'name':'Joe Trewin', 'uri': 'https://twitter.com/joeyspacerocks' } )
    fg.link( href='https://fistfulofsquid.com/blog')
    fg.link( href='https://fistfulofsquid.com/blog/rss', rel='self' )
    fg.language('en')

    for post in sorted(posts, key = lambda p: p['date']):
        fe = fg.add_entry()
        fe.id('https://fistfulofsquid.com/blog/' + post['url'])
        fe.title(post['title'])
        fe.link(href='https://fistfulofsquid.com/blog/' + post['url'])
        fe.description(post['blurb'])
        date = datetime.strptime(post['date'], '%Y%m%d').replace(tzinfo=pytz.UTC)
        fe.published(date)
        fe.updated(date)

    rssfeed  = fg.rss_str(pretty=True)
    fg.rss_file('rss.xml')

if __name__ == '__main__':
    main()
