import os
import re
import shutil
import subprocess
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

from .latex import *

REGEX_BRACKETS = r'\[(.*)\]'

NORMAL_FONT_SIZE = "footnotesize"
SMALL_FONT_SIZE = "scriptsize"

CODE_PAGE_BREAK = "pagebreak"
CODE_TWO_COLUMNS = "twocolumns"
CODE_COL_BREAK = "colbreak"

print_msg = False


def msg(s):
    if print_msg: print(s)


def download_cover_image(url, path):
    import urllib.request
    urllib.request.urlretrieve(url, path)


def sanitise_input(content):
    result = content
    t = {"”": '"', "’": "'", "–": "-", "…": "...", "—": "-", "‘": "'"}

    for c in t:
        result = re.sub(c, t[c], result)
    result = result.strip()
    result = result.replace("&", "\&")
    result = result.replace("#", "\#")
    result = result.replace("_", "\_")
    return result


def remove_special_chars(content):
    return re.sub(r"[^a-zA-Z0-9]+", ' ', content)


def call_build_process(path, file):
    f = file.split("/")[-1]
    p = subprocess.run(["latexmk", "-lualatex", "-interaction=nonstopmode", f], cwd=path)
    return p


def save_pdf_images(path, file_name, pdf_name):
    images = convert_from_path(pdf_name)
    paths = []
    i = 1
    for img in images:
        name = f"{path}/{file_name}_page{i}.png"
        img.save(name, 'PNG')
        paths.append(name)
        i += 1
    return paths


def prepare_font_files(path):
    shutil.copy("app/static/fonts/CutiveMono-Regular.ttf", path)
    shutil.copy("app/static/fonts/TwCen-Regular.ttf", path)
    shutil.copy("app/static/fonts/TwCen-Bold.ttf", path)



def create_document(path, file_name, page_numbering=False):
    doc = Document(path, file_name)

    doc.set_document_class("article", ["a4paper"])
    doc.use_package("geometry", ["left=2cm", "right=2cm", "top=1cm", "bottom=2cm"])
    doc.use_package("fontspec", [])
    doc.use_package("parskip", [])
    doc.use_package("multicol", [])
    doc.use_package("hyperref", ["hidelinks"])

    if not page_numbering:
        doc.use_package("nopageno", [])

    doc.append(Command("setmainfont", 
                       options=["BoldFont={TwCen-Bold.ttf}", "ItalicFont={TwCen-Regular.ttf}", "BoldItalicFont={TwCen-Regular.ttf}"], 
                       arguments=["TwCen-Regular.ttf"]))
    doc.append(Command("newfontfamily", 
                       arguments=["\\cutive", "CutiveMono-Regular.ttf"]))
    
    doc.append(Text("\\newcommand{\\invisiblesection}[1]{\\refstepcounter{section}\\addcontentsline{toc}{section}{#1}\\markboth{#1}{#1}}"))

    return doc



def build_song_header(song, doc):
    env_center = Environment("center", [])

    title = sanitise_input(song.title)
    artist = sanitise_input(song.artist)
    release = sanitise_input(song.release)
    year = song.year
    
    env_center.append(Command("textbf", arguments=[title]))
    env_center.append(NewLine())
    env_center.append(Text(f"{artist} -- {release} ({year})"))

    if song.capo:
        capo = sanitise_input(song.capo)
        env_center.append(Text(f" -- Capo {capo}"))

    doc.append(env_center)


def get_lyrics_blocks(song):
    blocks = []
    lyrics = sanitise_input(song.lyrics)
    
    two_columns = False

    current_block_heading = ""
    current_block = ""

    for line in lyrics.split("\n"):
        # if the line is a heading with [...]
        m = re.search(REGEX_BRACKETS, line)
        if m:
            heading = m.group(1).strip()

            # finish previous block
            if current_block_heading != "":
                blocks.append((current_block_heading, current_block))

            # if the heading is a code, handle the code
            if heading == CODE_TWO_COLUMNS:
                two_columns = True
                continue

            # start new block
            current_block_heading = heading
            current_block = ""

        else:
            if line.strip() == "":
                continue

            current_block += line + "\\\\\n"

    # add the last block
    if current_block_heading != "":
        blocks.append((current_block_heading, current_block))
    
    return blocks, two_columns


def build_text_blocks(song, doc):
    blocks, two_columns = get_lyrics_blocks(song)
    
    if two_columns:
        env_multicol = Environment("multicols", arguments=["2"])
        doc.append(env_multicol)
        current_col = env_multicol
    else:
        current_col = doc

    for block in blocks:
        heading = block[0]
        content = block[1]

        if heading == CODE_PAGE_BREAK and not two_columns:
            current_col.append(Command("pagebreak"))
            continue
        
        if heading == CODE_COL_BREAK:
            current_col.append(Command("columnbreak"))
            continue

        current_col.append(Command("textbf", arguments=[heading]))
        current_col.append(NewLine())

        env_content = Braces()
        env_content.append(Command("cutive"))
        env_content.append(Command("obeyspaces"))
        env_content.append(NoIndentText(content))

        current_col.append(env_content)


def build_song(song, doc, small_font):
    build_song_header(song, doc)

    size = SMALL_FONT_SIZE if small_font else NORMAL_FONT_SIZE
    env_content = Braces()
    env_content.append(Command(size, []))

    build_text_blocks(song, env_content)

    doc.append(env_content)




def build_song_standalone(song, path, file_name, small_font):
    doc = create_document(path, file_name)

    build_song(song, doc, small_font)

    return doc


def create_song(song, path):
    prepare_font_files(path)

    file_name = remove_special_chars(f"_{song.artist}_{song.title}").replace(" ", "_").lower()

    # first, build the song in normal font size
    doc = build_song_standalone(song, path, file_name, small_font=False)
    normal_doc_file = doc.build()
    call_build_process(path, normal_doc_file)
    pdf_name = normal_doc_file.replace(".tex", ".pdf")

    # check if the song is only one page
    with open(pdf_name, 'rb') as pdf:
        pages = len(PdfReader(pdf).pages)

    if pages == 1:
        img_paths = save_pdf_images(path, file_name, pdf_name)
        msg("Complete.")
        return pdf_name, img_paths, 1, False

    # then, if it has more than 2 pages, build the song in small font size
    doc = build_song_standalone(song, path, file_name, small_font=True)
    small_doc_file = doc.build()
    call_build_process(path, small_doc_file)
    pdf_name = small_doc_file.replace(".tex", ".pdf")

    with open(pdf_name, 'rb') as pdf:
        pages = len(PdfReader(pdf).pages)

    img_paths = save_pdf_images(path, file_name, pdf_name)
    msg("Complete.")

    return pdf_name, img_paths, pages, True



def build_songbook_cover(playlist, user, path, doc):
     doc.append(Command("pagestyle", arguments=["empty"]))


def build_songbook_toc(doc):   
    doc.append(Command("tableofcontents"))
    doc.append(Command("newpage"))
    doc.append(Command("pagestyle", arguments=["plain"]))
    doc.append(Command("pagenumbering", arguments=["arabic"]))
    doc.append(Command("setcounter", arguments=["page", "1"]))


def build_songbook_songs(playlist, doc):
    songs = playlist.songs
    songs.sort(key=lambda x: x.title)

    for song in playlist.songs:
        toc_entry = f"{song.title}"
        if song.artist:
            toc_entry += f"~~~{{\\footnotesize {song.artist}}}"
        doc.append(Command("invisiblesection", arguments=[toc_entry]))

        # build song itself
        small_font = True if song.small_font is None else song.small_font
        build_song(song, doc, small_font)

        doc.append(Command("pagebreak"))


def build_songbook(playlist, user, path):
    playlist_name = remove_special_chars(playlist.name).replace(" ", "_").lower()
    doc = create_document(path, f"songbook_{playlist_name}", page_numbering=True)

    build_songbook_cover(playlist, user, path, doc)
    build_songbook_toc(doc)
    build_songbook_songs(playlist, doc)   
    
    return doc


def create_songbook(playlist, user, path):
    try:
        os.mkdir(f"{path}/images")
    except:
        pass

    # i = 0
    # for song in playlist.songs:
    #     if song.cover_url:
    #         download_cover_image(song.cover_url, f"{path}/images/cover_{i:03d}.png")
    #         i += 1

    prepare_font_files(path)
    doc = build_songbook(playlist, user, path)
    doc_file = doc.build()
    call_build_process(path, doc_file)
    pdf_name = doc_file.replace(".tex", ".pdf")
    return pdf_name


    
    
