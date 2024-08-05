import json
import os
import re

from deep_translator import GoogleTranslator


def translate_markdown(text, dest_language="pt"):
    # Regex expressions
    MD_CODE_REGEX = r"```[a-z]*\n[\s\S]*?\n```"
    CODE_REPLACEMENT_KW = r"xx_markdown_code_xx"

    MD_LINK_REGEX = r"\[[^)]+\)"
    LINK_REPLACEMENT_KW = "xx_markdown_link_xx"

    # Markdown tags
    END_LINE = "\n"
    IMG_PREFIX = "!["
    HEADERS = ["### ", "###", "## ", "##", "# ", "#"]  # Should be from this order (bigger to smaller)

    # Inner function to replace tags from text from a source list
    def replace_from_list(tag, text, replacement_list):
        if not replacement_list:
            return text

        def list_to_gen():
            return [x for x in replacement_list]

        replacement_gen = list_to_gen()
        return re.sub(tag, lambda x: next(iter(replacement_gen)), text)

    # Create an instance of Translator
    translator = GoogleTranslator(source="auto", target=dest_language)

    # Inner function for translation
    def translate(text):
        if not text:
            return ""
        # Get all markdown links
        md_links = re.findall(MD_LINK_REGEX, text)

        # Get all markdown code blocks
        md_codes = re.findall(MD_CODE_REGEX, text)

        # Replace markdown links in text to markdown_link
        text = re.sub(MD_LINK_REGEX, LINK_REPLACEMENT_KW, text)

        # Replace links in markdown to tag markdown_link
        text = re.sub(MD_CODE_REGEX, CODE_REPLACEMENT_KW, text)

        # Translate text
        try:
            text = translator.translate(text)
        except Exception as e:
            print(f"Translation error: {e}")
            return None

        if text is None:
            return ""

        # Replace tags to original link tags
        text = replace_from_list(LINK_REPLACEMENT_KW, text, md_links)

        # Replace code tags
        text = replace_from_list(CODE_REPLACEMENT_KW, text, md_codes)

        return text

    # Check if there are special Markdown tags
    if len(text) >= 2:
        if text[-1:] == END_LINE:
            return translate(text) + "\n"

        if text[:2] == IMG_PREFIX:
            return text

        for header in HEADERS:
            len_header = len(header)
            if text[:len_header] == header:
                return header + translate(text[len_header:])

    translated_text = translate(text)
    if translated_text is None:
        return ""
    return translated_text


def jupyter_translate(fname, language="fr", rename_source_file=False, print_translation=False):
    with open(fname, encoding="utf-8") as file:
        data_translated = json.load(file)

    skip_row = False
    for i, cell in enumerate(data_translated["cells"]):
        for j, source in enumerate(cell["source"]):
            if cell["cell_type"] == "markdown":
                if source[:3] == "```":
                    skip_row = not skip_row  # Invert flag until I find next code block

                if not skip_row:
                    if source not in ["```\n", "```", "\n"] and source[:4] != "<img":  # Don't translate cause
                        # of: 1. ``` -> ëëë 2. '\n' disappeared 3. image's links damaged
                        translated_text = translate_markdown(source, dest_language=language)
                        data_translated["cells"][i]["source"][j] = translated_text
                        if print_translation:
                            print(translated_text)

    if rename_source_file:
        fname_bk = f"{'.'.join(fname.split('.')[:-1])}_bk.ipynb"  # index.ipynb -> index_bk.ipynb

        os.rename(fname, fname_bk)
        print(f"{fname} has been renamed as {fname_bk}")

        with open(fname, "w") as f:
            f.write(json.dumps(data_translated))
        print(f"The {language} translation has been saved as {fname}")
    else:
        dest_fname = f"{'.'.join(fname.split('.')[:-1])}_{language}.ipynb"  # any.name.ipynb -> any.name_pt.ipynb
        with open(dest_fname, "w") as f:
            f.write(json.dumps(data_translated))
        print(f"The {language} translation has been saved as {dest_fname}")


def markdown_translator(input_fpath, output_fpath, input_name_suffix=""):
    with open(input_fpath, encoding="utf-8") as f:
        content = f.readlines()
    content = "".join(content)
    content_translated = translate_markdown(content)
    if input_name_suffix != "":
        new_input_name = f"{'.'.join(input_fpath.split('.')[:-1])}{input_name_suffix}.md"
        os.rename(input_fpath, new_input_name)
    with open(output_fpath, "w", encoding="utf-8") as f:
        f.write(content_translated)


if __name__ == "__main__":
    jupyter_translate(
        "/Users/regislon/Documents/Projects/hepia-engineering-informatics/hepia-engineering-informatics/notebooks/P03.0_Loops.ipynb"
    )
