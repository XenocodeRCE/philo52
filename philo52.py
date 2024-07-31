import requests
import re
import os

def remove_leading_period(text):
    if text.startswith('.') or text.startswith(';'):
        return text[1:]
    return text

def remove_quotes_from_lines(text):
    lines = text.split('\n')
    for i in range(len(lines)):
        if 'text-align:right' in lines[i]:
            lines[i] = lines[i].replace('"', '')
    return '\n'.join(lines)

def remove_html_tags(text):
    return re.sub(r'<.*?>', '', text)

def split_at_last_quote(s):
    last_quote_index = s.rfind('"')
    if last_quote_index == -1:
        return [s]
    part1 = s[:last_quote_index].strip()
    part2 = s[last_quote_index + 1:].strip()
    return [part1, part2]

def split_if_four_quotes(s):
    indices = [i for i in range(len(s)) if s[i] == '"']
    if len(indices) == 4:
        third_quote_index = indices[2] + 1
        part1 = s[:third_quote_index].strip()
        part2 = s[third_quote_index:].strip()
        return [part1, part2]
    return [s]

def sanitize_filename(name):
    return re.sub(r'\W+', '_', name)

def get_next_filename(base_path, base_filename):
    counter = 1
    filename = os.path.join(base_path, f"{base_filename}_{counter:03d}.txt")
    while os.path.isfile(filename):
        counter += 1
        filename = os.path.join(base_path, f"{base_filename}_{counter:03d}.txt")
    return filename

def process_text_chunk(chunk):
    if "Retour au menu" in chunk:
        chunk = chunk.split("Retour au menu")[0]
    if "FAQ" in chunk:
        chunk = chunk.split("FAQ")[1]
    chunk = chunk.replace('\r', '').replace('\n', '').replace('text-autospace:none', '')
    chunk = remove_html_tags(chunk).replace('">', '').lstrip()
    if chunk.count('"') < 1:
        return []
    return split_if_four_quotes(chunk)

def process_page(url):
    response = requests.get(url)
    response.raise_for_status()
    html_content = response.text
    html_content = remove_quotes_from_lines(html_content)
    html_content = re.sub(r'<hr\s*/>\s*\n+', '<hr />', html_content)
    html_content = html_content.replace("<hr />\t", "<hr />").replace("text-align: ", "text-align:")
    html_content = html_content.replace("&nbsp;", "").replace("&#160;", "")
    chunks = html_content.split('<hr /><div style="text-align:justify')
    processed_strings = []
    for chunk in chunks:
        processed_strings.extend(process_text_chunk(chunk))
    return processed_strings

def save_processed_strings(processed_strings):
    for s in processed_strings:
        s = s[:-1] if s.endswith('"') else s
        texte, _, source = s.rpartition('"')
        source = source.strip()
        texte = remove_leading_period(texte).strip()
        if ", " in source:
            auteur = remove_leading_period(source.split(',', 1)[0]).strip()
            livre = remove_leading_period(source.split(',', 1)[1]).strip()
            auteur_folder = sanitize_filename(auteur)
            if not os.path.exists(auteur_folder):
                os.makedirs(auteur_folder)
            auteur_filename = get_next_filename(auteur_folder, sanitize_filename(auteur))
            with open(auteur_filename, 'w', encoding='utf-8') as file:
                file.write(f"Texte : {texte}\nAuteur : {auteur}\nLivre : {livre}\n")
        else:
            source_filename = get_next_filename('.', sanitize_filename(source))
            with open(source_filename, 'w', encoding='utf-8') as file:
                file.write(f"Texte : {texte}\nSource : {source}\n")

def main():
    base_url = 'https://www.philo52.com/mobile/articles.php?lng=fr&pg='
    for i in range(0, 99999):
        url = f"{base_url}{i}"
        try:
            processed_strings = process_page(url)
            save_processed_strings(processed_strings)
            print(f"Processed page {i} successfully.")
        except requests.HTTPError as e:
            print(f"Failed to process page {i}: {e}")
        except Exception as e:
            print(f"An error occurred while processing page {i}: {e}")

if __name__ == "__main__":
    main()
