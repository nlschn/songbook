INDENT = "    "

class Command:
    def __init__(self, name, options=None, arguments=None):
        if options is None:
            options = []
        if arguments is None:
            arguments = []

        self.name = name
        self.options = options
        self.arguments = arguments

    def build(self, indent):
        args = list(map(lambda x: f"{{{x}}}", self.arguments))
        s = f"{INDENT * indent}"
        s += f"\\{self.name}"
        if self.options:
            s += f"[{', '.join(self.options)}]"
        s += f"{''.join(args)}\n"

        return s

class CustomEnvironment:
    def __init__(self, name, options):
        self.name = name
        self.options = options
        self.children = []

    def append(self, element):
        self.children.append(element)

    def build(self, indent):
        s = f"\n{INDENT * indent}"
        s += "\\begin"        
        s += f"{{{self.name}}}"
        
        for option in self.options:
            s += option
        s += "\n"

        for child in self.children:
            s += child.build(indent + 1)

        s += f"{INDENT * indent}\\end{{{self.name}}}\n"
        return s

class Environment:
    def __init__(self, name, options=None, arguments=None, children=None):
        self.name = name
        self.options = options if options else []
        self.arguments = arguments if arguments else []
        self.children = children if children else []

    def append(self, element):
        self.children.append(element)

    def build(self, indent):
        s = f"\n{INDENT * indent}"
        s += "\\begin"
        if self.options:
            s += f"[{', '.join(self.options)}]"
        s += f"{{{self.name}}}\n"
        if self.arguments:
            s += "".join([f"{{{arg}}}" for arg in self.arguments])

        for child in self.children:
            s += child.build(indent + 1)

        s += f"{INDENT * indent}\\end{{{self.name}}}\n"
        return s

class Package:
    def __init__(self, name, options):
        self.name = name
        self.options = options

class Text:
    def __init__(self, content):
        self.content = content

    def build(self, indent):
        return f"{INDENT * indent}{self.content}\n"
    
class NoIndentText:
    def __init__(self, content):
        self.content = content

    def build(self, indent):
        return f"{self.content}\n"

class Braces:
    def __init__(self):
        self.children = []

    def append(self, element):
        self.children.append(element)

    def build(self, indent):
        s = f"{INDENT * indent}"
        s += f"{{\n"

        for child in self.children:
            s += child.build(indent + 1)

        s += f"{INDENT * indent}}}\n"
        return s
       
class NewLine:
    def build(self, indent):
        return f"{INDENT * indent}~\\\\\n"

class Document:
    def __init__(self, path, name):
        self.path = path
        self.name = name

        self.packages = []
        self.document_class_options = []
        self.document_class = "article"

        self.preamble = []
        self.children = []

    def set_document_class(self, document_class, options):
        self.document_class = document_class
        self.document_class_options = options
    
    def use_package(self, package, options):
        self.packages.append(Package(package, options))

    def append(self, element):
        self.children.append(element)
        return element
    
    def append_preamble(self, element):
        self.preamble.append(element)
    
    def build(self):
        document_class_str = f'[{", ".join(self.document_class_options)}]{{{self.document_class}}}'
        s = f"\\documentclass{document_class_str}\n\n"

        for package in self.packages:
            s += f"\\usepackage[{', '.join(package.options)}]{{{package.name}}}\n"

        s += "\n"

        for preamble in self.preamble:
            s += preamble.build(0)
            
        s+= "\n"

        env_doc = Environment("document", children=self.children)
        s += env_doc.build(0)

        file_name = f"{self.path}/{self.name}.tex"
        with open(file_name, "w") as f:
            f.write(s)

        return file_name