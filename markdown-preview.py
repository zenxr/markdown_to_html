import argparse
import os
import webbrowser
import html
try:
    import config
except:
    import example_config

class FilterBase(object):
    def __call__(self, content):
        return self.filter(content)

    def filter(self, content):
        # to be implemented by derived classes
        raise TypeError("This method to be implemented by derived")

class CodeBlockFilter(FilterBase):
    def __init__(self):
        super(CodeBlockFilter, self).__init__()
        self.in_codeblock = False

    def filter(self, content):
        return [self.filter_line(line) for line in content]

    def filter_line(self, line):
        if line.lstrip().startswith('```'):
            self.in_codeblock = not self.in_codeblock
            if self.in_codeblock:
                return '<pre><code>\n'
            else:
                return '</code></pre>\n'
        return line

class IgnoreCodeBlockFilterBase(FilterBase):
    def filter(self, content):
        self.in_codeblock = False
        return [self.check_codeblock(line) for line in content]

    def check_codeblock(self, line):
        if line.lstrip().startswith('```'):
            self.in_codeblock = not self.in_codeblock
        if not self.in_codeblock:
            line = self.filter_line(line)
        return line

    def filter_line(self, line):
        raise TypeError("This method to be implemented by derived")

class EmptyLineFilter(FilterBase):
    def __init__(self):
        super(EmptyLineFilter, self).__init__()
        self.in_paragraph = False
        self.whitespace_lines = []
    
    def filter(self, content):
        in_codeblock = False
        response = []
        for idx, line in enumerate(content):
            if not in_codeblock and line.isspace():
                self.whitespace_lines.append(idx)
            if line.startswith('```'):
                in_codeblock = not in_codeblock
        for idx, line in enumerate(content):
            response.append(self.filter_line(idx, line))
        return response

    def filter_line(self, idx, line):
        if idx in self.whitespace_lines:
            line = EmptyLineFilter.filter_whitespace(idx, len(self.whitespace_lines) - 1)
        return line

    @staticmethod
    def filter_whitespace(idx, last_whitespace_idx):
        if idx == 0:
            return '<p>\n'
        elif idx == last_whitespace_idx:
            return '<\p>\n'
        else:
            return '</p>\n<p>\n'

class EmphasisFilter(IgnoreCodeBlockFilterBase):
    def __init__(self):
        super(EmphasisFilter, self).__init__()
        self.in_emphasis = False
        self.emphasis_toggle = lambda: '<i>' if not self.in_emphasis else '</i>'
        self.tokens = ['*', '_']

    def filter_line(self, line):
        match = self.get_match(line)
        while(match):
            line = line.replace(match, self.emphasis_toggle(), 1)
            self.in_emphasis = not self.in_emphasis
            match = self.get_match(line)
        return line

    def get_match(self, line):
        return next((token for token in self.tokens if token in line), None)

class BoldFilter(IgnoreCodeBlockFilterBase):
    def __init__(self):
        super(BoldFilter, self).__init__()
        self.in_bold = False
        self.bold_toggle = lambda: '<b>' if not self.in_bold else '</b>'
        self.tokens = ['**', '__']

    def filter_line(self, line):
        match = self.get_match(line)
        while(match):
            line = line.replace(match, self.bold_toggle(), 1)
            self.in_bold = not self.in_bold
            match = self.get_match(line)
        return line

    def get_match(self, line):
        return next((token for token in self.tokens if token in line), None)

class InlineCodeFilter(IgnoreCodeBlockFilterBase):
    def __init__(self):
        super(InlineCodeFilter, self).__init__()
        self.inline_code = False
        self.inline_code_toggle = lambda: '<code>' if not self.inline_code else '</code>'

    def filter_line(self, line):
        while('`' in line):
            line = line.replace('`', self.inline_code_toggle(), 1)
            # replace intermediate text with escaped unicode
            if not self.inline_code:
                try:
                    inline_code, after_code = codeline.split('`', 1)
                    line = '%s`%s' % (html.escape(inline_code), after_code)
                except:
                    pass
            self.inline_code = not self.inline_code
        return line
    
class HeaderFilter(IgnoreCodeBlockFilterBase):
    def __init__(self):
        super(HeaderFilter, self).__init__()
        self.tokens = [
            ['######', '<h6>', '</h6>\n'],
            ['#####', '<h5>', '</h5>\n'],
            ['####', '<h4>', '</h4>\n'],
            ['###', '<h3>', '</h3>\n'],
            ['##', '<h2>', '</h2>\n'],
            ['#', '<h1>', '</h1>\n']
        ]

    def filter_line(self, line):
        for sub_filter in self.tokens:
            if line.startswith(sub_filter[0]):
                line = line.replace(sub_filter[0], sub_filter[1], 1).rstrip() + sub_filter[2]
                break
        return line

class ListFilter(IgnoreCodeBlockFilterBase):
    def __init__(self):
        super(ListFilter, self).__init__()
        self.indent_level = 0
        self.tokens = ['* ', '- ', '+ ']
    
    def filter_line(self, line):
        match = next((t for t in self.tokens if line.lstrip().startswith(t)), None)
        if match:
            curr_indent_level = len(line.split(match, 1)[0])
            if curr_indent_level > self.indent_level:
                line = line.replace(match, '<ul><li>', 1).rstrip() + '</li>\n'
            elif curr_indent_level < self.indent_level:
                line = line.replace(match, '</ul><li>').rstrip() + '</li>\n'
            else:
                line = line.replace(match, '<li>').rstrip() + '</li>\n'
            self.indent_level = curr_indent_level
        return line

#TODO
# class OrderedListFilter(IgnoreCodeBlockFilterBase):

class MdToHtml:
    filters = [EmptyLineFilter(), CodeBlockFilter(), InlineCodeFilter(), ListFilter(), HeaderFilter(), BoldFilter(), EmphasisFilter()]

    @staticmethod
    def convert(infile):
        contents = MdToHtml.read_file(args.file)
        filtered_contents = MdToHtml.parse_html(contents)
        packed_html_path = os.path.join(os.path.dirname(infile), 'html', os.path.basename(infile).replace('.md', '.html'))
        MdToHtml.write_file(packed_html_path, MdToHtml.pack_document(filtered_contents))
        return packed_html_path
    
    @staticmethod
    def read_file(filepath):
        with open(filepath, 'r') as f:
            return f.readlines()

    @staticmethod
    def write_file(filepath, contents):
        if os.path.exists(filepath):
            os.remove(filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.writelines(contents)

    @staticmethod
    def parse_html(contents):
        for filter in MdToHtml.filters:
            contents = filter(contents)
        return contents

    @staticmethod
    def pack_document(contents):
        print("Packing")
        return [config.header] + contents + [config.footer]

    @staticmethod
    def preview(infile):
        document = MdToHtml.convert(infile)
        webbrowser.open(os.path.abspath(document))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', action='store', required=True)
    args = parser.parse_args()

    MdToHtml.preview(args.file)

