import re
import shutil
from pylatex import Document, Command, Center, LineBreak, Package
from pylatex.base_classes import Environment
from pylatex.base_classes.command import CommandBase
from pylatex.basic import NewLine
from pylatex.utils import NoEscape, bold
from PyPDF2 import PdfFileReader
from pdf2image import convert_from_path

ENCODING = "gb18030"
REGEX_BRACKETS = r'\[.*?\]'
REGEX_PARS = r"\[.*?\]"

print_msg = False

def msg(s):
    if print_msg: print(s)

def remove_empty_lines(content):    
    return "".join([s for s in content.splitlines(True) if s.strip(" \t\r\n")])

def sanitize_input(content): 
    result = content       
    t = {"”" : '"', "’" : "'", "–" : "-", "…" : "...", "—" : "-", "‘" : "'"}

    for c in t:
        result = re.sub(c, t[c], result)
    return result

def replace_brackets(content):
    occurences = re.findall(REGEX_BRACKETS, content)
    captions = []
    for o in occurences:
        inside = o[1:-1]
        captions.append(inside)

    return captions

def set_listings(content):
    pars = re.split(REGEX_PARS, content)    
    new_pars = []
    for par in pars:
        new_par = remove_empty_lines(par)
        if new_par != None:
            new_pars.append(new_par) 
    if(new_pars[0] == ''):
        new_pars.remove('')
        
    return new_pars

def build_lyrics(captions, pars, doc):
    for i in range(0, len(pars)):
        if i > 0:
            doc.append(NewLine())
        doc.append(bold(captions[i]))
        if not re.match("^[\s]+$", pars[i]):
            doc.append(NewLine())
            doc.append(NoEscape("{ \cutive \obeyspaces"))           
            doc.append(pars[i])     
            doc.append(NoEscape("}"))
           

def create_doc(title, artist, release, year, size):
    geometry = {"left" : "2cm", "right" : "2cm", "top" : "1cm", "bottom" : "1cm"}

    doc = Document(indent=False, geometry_options = geometry, documentclass = "article")

    doc.packages.append(Package("fontspec"))
    doc.packages.append(Package('nopageno'))

    doc.append(NoEscape("\\newfontfamily{\cutive}{[CutiveMono-Regular.ttf]}"))
    
    with doc.create(Center()):
        doc.append(bold(sanitize_input(title)))
        doc.append(LineBreak())
        doc.append(f"{sanitize_input(artist)} - {sanitize_input(release)} ({year})")
    doc.append(Command("scriptsize") if size == "small" else Command("footnotesize"))
    return doc
    
def save_images(file_name, pdf_name):    
    images = convert_from_path(pdf_name)
    paths = []
    i = 1
    for img in images:
        name = f"{file_name}_page{i}.png"
        img.save(name, 'PNG')
        paths.append(name)
        i += 1
    return paths

def build_song_one_page(title, artist, release, year, pars, captions, path):
    file_name = f"{path}/{title}_{artist}_{year}"#os.path.join(path, f"{title}_{artist}_{year}")
    pdf_name = f"{path}/{title}_{artist}_{year}.pdf"#os.path.join(path, f"{title}_{artist}_{year}.pdf")

    # Copy font file to the tex path
    shutil.copy("CutiveMono-Regular.ttf", path)

    # Build first time with normal size.
    msg("Creating LaTeX document...")
    doc = create_doc(title, artist, release, year, "normal")
    build_lyrics(captions, pars, doc)
    msg("Building LaTeX document...")
    doc.generate_pdf(file_name, silent = True, clean=False,compiler='lualatex')

    with open(pdf_name,'rb') as pdf:
        pages = PdfFileReader(pdf).getNumPages()

    if pages == 1:
        img_paths = save_images(file_name, pdf_name)
        msg("Complete.")
        return pdf_name, img_paths

    # Build first time with normal size.
    msg("Document too long. Trying again with smaller font.")
    msg("Creating LaTeX document...")
    doc = create_doc(title, artist, release, year, "small")
    build_lyrics(captions, pars, doc)
    msg("Building LaTeX document...")
    doc.generate_pdf(file_name, silent = True, clean=False,compiler='lualatex')

    img_paths = save_images(file_name, pdf_name)

    msg("Complete.")

    return pdf_name, img_paths

def build_tex(content, title, artist, release, year, path):
    content = sanitize_input(content)   
    captions = replace_brackets(content)
    pars = set_listings(content) 

    if len(pars) != len(captions):
        msg("Error. Make sure every paragraph is labelled with [...]")
        print(len(captions))
        print(len(pars))
        return None, None

    return build_song_one_page(title, artist, release, year, pars, captions, path)  
     


