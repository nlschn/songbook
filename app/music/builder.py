import os
import re
import shutil
import subprocess
from pylatex import Document, Command, Center, LineBreak, Package
from pylatex.position import VerticalSpace
from pylatex.base_classes import Environment
from pylatex.base_classes.command import CommandBase, Arguments
from pylatex.basic import NewLine
from pylatex.utils import NoEscape, bold, italic
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
    file_name = f"{path}/{title}_{artist}_{year}"
    pdf_name = f"{path}/{title}_{artist}_{year}.pdf"

    # Copy font file to the tex path
    shutil.copy("app/static/fonts/CutiveMono-Regular.ttf", path)

    # Build first time with normal size.
    msg("Creating LaTeX document...")
    doc = create_doc(title, artist, release, year, "normal")
    build_lyrics(captions, pars, doc)
    msg("Building LaTeX document...")
    doc.generate_pdf(file_name, silent = True, clean = True, compiler='lualatex')

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
    doc.generate_pdf(file_name, silent = True, clean = True, compiler='lualatex')

    img_paths = save_images(file_name, pdf_name)

    msg("Complete.")

    return pdf_name, img_paths

def build_tex(song, path):
    content = sanitize_input(song.lyrics)   
    captions = replace_brackets(content)
    pars = set_listings(content) 

    if len(pars) != len(captions):
        msg("Error. Make sure every paragraph is labelled with [...]")
        print(len(captions))
        print(len(pars))
        return None, None

    return build_song_one_page(song.title, song.artist, song.release, song.year, pars, captions, path)  
     

class IncludePDFCommand(CommandBase):
    _latex_name = "includegraphics"
    packages = [Package('graphicx')]

class TextWidthCommand(CommandBase):
    _latex_name = "textwidth"
    packages = []

class PageBreakCommand(CommandBase):
    _latex_name = "pagebreak"    

class PageStyleCommand(CommandBase):
    _latex_name = "pagestyle"  
    packages = [Package('fancyhdr')]

class FooterCommand(CommandBase):
    _latex_name = "fancyfoot"  
    packages = [Package('fancyhdr')]

class HeaderCommand(CommandBase):
    _latex_name = "fancyhead"  
    packages = [Package('fancyhdr')]

class HyperlinkCommand(CommandBase):
    packages = [Package('hyperref')]
    _latex_name = ","


def build_songbook(playlist, user, path):
    # shutil.copy("app/static/fonts/TwCen-Regular.TTF", "./")

    msg("Create tex document...")

    geometry = {"left" : "2cm", "right" : "2cm", "top" : "2cm", "bottom" : "2cm"}
    doc = Document(indent=False, geometry_options=geometry, documentclass = "article")
    doc.packages.append(Package(NoEscape("fix-cm")))

    # doc.append(NoEscape("\\newfontfamily{\\twcen}{[TwCen-Regular.TTF]}"))

    doc.append(HyperlinkCommand())
    doc.append(NoEscape("""\hypersetup{
colorlinks,
citecolor=black,
filecolor=black,
linkcolor=black,
urlcolor=black
}"""))
    doc.append(NoEscape("\\newcommand\\invisiblesection[1]{\\refstepcounter{section}\\addcontentsline{toc}{section}{#1}\\markboth{#1}{#1}}"))
    
    # Title page
    doc.append(NoEscape("\\thispagestyle{empty}")) 
    doc.append(VerticalSpace("15em"))
    with(doc.create(Center())):
        doc.append(IncludePDFCommand(options=f"width=15cm", arguments=Arguments("../../logo/logoheaderdark")))
        doc.append(NewLine())
        # doc.append(NoEscape("{\\twcen"))
        doc.append(NoEscape("{\\fontsize{30}{36}\selectfont"))
        doc.append(f"by {user.prename} {user.surname}")
        doc.append(NoEscape("}"))
        # doc.append(NoEscape("}"))
    doc.append(PageBreakCommand())
   
    doc.append(NoEscape("\\tableofcontents"))     
    doc.append(NoEscape("\\newgeometry{margin=0.1cm}"))
    doc.append(NoEscape("\\setcounter{page}{1}"))
    
    p = 1
    count = 1
    for i in range(len(playlist.songs)):
        song = playlist.songs[i]

        # First, build the pdf
        pdf_path, _ = build_tex(song, path)

        doc.append(NoEscape("\\invisiblesection{"))
        doc.append(song.title)
        doc.append(NoEscape("\\textnormal{~"))
        if song.artist != "" and song.artist != None:
            doc.append(" - " + song.artist)
        doc.append(NoEscape("}}"))

        with open(pdf_path,'rb') as pdf:
            pages = PdfFileReader(pdf).getNumPages()
        
        for page in range(1, pages + 1):
            with(doc.create(Center())):
                doc.append(VerticalSpace(NoEscape("-1em")))            
                doc.append(NoEscape(f"\includegraphics[scale=0.9, page={page}] " + "{" + f"{song.title}_{song.artist}_{song.year}" + "}"))
                doc.append(NewLine())
                doc.append(NoEscape(f"{p} - " + italic(f"{page}/{pages}")))
                p += 1

        doc.append(PageBreakCommand())
        count += 1

    msg("Build pdf document...")
    result_path = f"{path}/{playlist.name}_songbook"
    doc.generate_tex(result_path)
    doc.generate_pdf(result_path, silent = True, clean = True)

    # does not work
    # with open(f"{result_path}.tex", 'r+') as f:
    #     content = f.read()
    #     f.seek(0, 0)
    #     f.write('\\nonstopmode\n' + content)

    # subprocess.run(["latexmk", "-pdf", f"{result_path}.tex", f"-jobname={result_path}"])
    # subprocess.run(["latexmk", "-c"])

    # os.remove("./TwCen-Regular.TTF")


    # doc.generate_pdf(result_path, silent = True, clean = False)
    return f"{result_path}.pdf"