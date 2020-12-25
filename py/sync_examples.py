# Copyright 2020 H2O.ai, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os.path
from collections import defaultdict
from typing import List

example_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), 'examples'))
website_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'website'))


class Example:
    def __init__(self, filename: str, title: str, description: str, keywords: List[str], code: str):
        self.name = os.path.splitext(filename)[0]
        self.slug = self.name.replace('_', '-')
        self.filename = filename
        self.title = title
        self.subtitle = description.split('\n')[0].strip()
        self.description = description
        self.keywords = keywords
        self.code = code

    def to_md(self):
        if self.keywords:
            keywords = '\n'.join(['  - ' + x for x in self.keywords])
            keyword_tags = []
            for k in self.keywords:
                keyword_tags.append(f"<a href={{useBaseUrl('docs/examples/examples-tags#{k}')}}>{k}</a>")
            keywords_links = '  '.join(keyword_tags)
            header = f"""---
title: {self.title}
keywords:
{keywords}
---

import useBaseUrl from '@docusaurus/useBaseUrl';

        """
            footer = f"""

**Tags**:  {keywords_links}

            """
        else:
            header = f"""---
title: {self.title}
---
        """
            footer = ""

        body = f"""

{self.description}

<div className='cover' style={{{{ backgroundImage: 'url(' + require('./assets/{self.slug}.png').default + ')' }}}} />

```py
{self.code}
```
        """
        return header + body + footer


def read_lines(p: str) -> List[str]:
    with open(p) as f:
        return f.readlines()


def read_file(p: str) -> str:
    with open(p) as f:
        return f.read()


def write_file(p: str, txt: str) -> str:
    with open(p, 'w') as f:
        f.write(txt)
    return txt


def strip_comment(line: str) -> str:
    return line.strip(" #")


def get_keywords_if_available(line: str) -> List[str]:
    keywords = [x.strip() for x in line.split(',')]
    period_in_line = '.' in line
    spaces_in_keywords = any([' ' in x for x in keywords])
    if period_in_line or spaces_in_keywords:
        return []
    return keywords


def load_example(filename: str) -> Example:
    contents = read_file(os.path.join(example_dir, filename))
    parts = contents.split('---', maxsplit=1)
    header, code = parts[0].strip().splitlines(), parts[1].strip()
    title, description = strip_comment(header[0]), [strip_comment(x) for x in header[1:]]
    keywords = get_keywords_if_available(description[-2])
    return Example(filename, title, '\n'.join(description), keywords, code)


def make_toc(examples: List[Example]):
    return '''---
title: All Examples
slug: /examples/all
---

import useBaseUrl from '@docusaurus/useBaseUrl';

''' + '\n\n'.join([f"- <a href={{useBaseUrl('docs/examples/{e.slug}')}}>{e.title}</a>: {e.subtitle}" for e in examples])


def make_gallery_thumbnail(e: Example):
    return f"<a class='thumbnail' href={{useBaseUrl('docs/examples/{e.slug}')}}><div style={{{{backgroundImage:'url(' + require('./assets/{e.slug}.png').default + ')'}}}}></div>{e.title}</a>"  # noqa: E501


def make_gallery(examples: List[Example]):
    return '''---
title: Gallery
slug: /examples
---

import useBaseUrl from '@docusaurus/useBaseUrl';
''' + '\n' + '\n\n'.join([make_gallery_thumbnail(e) for e in examples])


def make_keyword_group(keyword: str, examples: List[Example]) -> str:
    sub_heading = f"### {keyword}\n"
    example_links = []
    for e in examples:
        example_links.append(f"<a href={{useBaseUrl('docs/examples/{e.slug}')}}>{e.title}</a>")
    return sub_heading + '  '.join(example_links) + '\n'


def index_examples(examples: List[Example]):
    keywords_dict = defaultdict(list)
    for e in examples:
        for k in e.keywords:
            keywords_dict[k].append(e)
    return sorted(keywords_dict.items())


def make_examples_by_keyword(examples: List[Example]):
    keywords = index_examples(examples)
    return '''---
title: Tags
---

import useBaseUrl from '@docusaurus/useBaseUrl';
''' + '\n' + '\n\n'.join([make_keyword_group(k, e) for k, e in keywords])


def main():
    filenames = [line.strip() for line in read_lines(os.path.join(example_dir, 'tour.conf')) if
                 not line.strip().startswith('#')]

    examples = [load_example(filename) for filename in filenames]

    example_md_dir = os.path.join(website_dir, 'docs', 'examples')
    thumbnail_dir = os.path.join(example_md_dir, 'assets')
    for e in examples:
        md = e.to_md()
        write_file(os.path.join(example_md_dir, f'{e.slug}.md'), md)
        if not os.path.exists(os.path.join(thumbnail_dir, f'{e.slug}.png')):
            print(f'*** ALERT: no thumbnail found for example "{e.slug}"')

    example_items = [dict(slug=e.slug) for e in examples]
    example_items.insert(0, dict(slug='index'))
    example_items.insert(1, dict(slug='all'))
    example_items.insert(2, dict(slug='examples-tags'))
    write_file(os.path.join(website_dir, 'examples.js'), f'module.exports={json.dumps(example_items)}')
    write_file(os.path.join(example_md_dir, 'index.md'), make_gallery(examples))
    write_file(os.path.join(example_md_dir, 'all.md'), make_toc(examples))
    write_file(os.path.join(example_md_dir, 'examples-tags.md'), make_examples_by_keyword(examples))


if __name__ == '__main__':
    main()
