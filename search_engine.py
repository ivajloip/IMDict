from urllib.request import FancyURLopener
import urllib.request
import urllib.parse 
import re

class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)'

def connect_to_dictionary(url):
    if not url:
        return None
    myopener = MyOpener()
    try:
        page = myopener.open(url)
    except:
        return None
    return page

def text_url(from_lang, to_lang, text):
    url = 'http://translate.google.bg/translate_t?prev=hp&hl=bg&js=y&text=' + urllib.parse.quote_plus(text) + '%0D%0A&file=&sl=' + from_lang + '&tl=' + to_lang + '&history_state0=#'        
    return url

def word_url(from_lang, to_lang, word):
    address = 'http://www.google.bg/dictionary?source=translation&hl=' + to_lang + '&q=' + urllib.parse.quote_plus(word) + '&langpair=' + from_lang + '|' + to_lang
    return address

def urban_dict_url(from_lang, to_lang, word):
    address = 'http://www.urbandictionary.com/define.php?term=' + urllib.parse.quote_plus(word)
    return address

def find_from_urban_dict(from_lang, to_lang, word):
    print("using urban dict")
    conn = connect_to_dictionary(urban_dict_url(from_lang, to_lang, word))
    s = ''.join((_.decode() for _ in conn.readlines()))
    match = re.search(r'(?m)(?s)<div class=\'definition\'>(?P<definition>.*?)</div>',s)
    if not match:
        return '<p><strong>' + word + '</strong></p>' + find_translation(from_lang, to_lang, word)
    return '<p><strong>' + word + '</strong></p>' + '<p>' + find_translation(from_lang, to_lang, re.sub(r'<br.>', '\n', match.group('definition')))


def find_word(from_lang, to_lang, word):
    conn = connect_to_dictionary(word_url(from_lang, to_lang, word))
    s = ''.join((_.decode() for _ in conn.readlines()))
    match = re.search(r'(?m)<span class="dct-tt">(?P<definition>.*?)</span>', s)
    if not match:
        match = re.search(r'<h2 class="wd">(?P<definition>.*?)</h2>', s)
        if not match: 
            return find_from_urban_dict(from_lang, to_lang, word)
        match = re.search(r'(?m)<div class="wbtr_cnt">\n(?P<definition>.*?)$', s)
        return '<p><strong>' + word + '</strong></p>' + match.group('definition')

    find_transcription = re.search(r'(?m)<span class="dct-tp">(?P<definition>(\[|/).*?)$', s)
    if find_transcription:
        word = '<p><strong>' + match.group('definition').upper() + ' ' + find_transcription.group('definition') + '</strong></p>'
    else: 
         word = '<p><strong>' + match.group('definition').upper() + '</strong></p>'

    l = [word]
    s = s[match.end():]
    index = 1

    while True:
        match = re.search(r'(?m)(?P<class><span class="dct-tt">|title="Part-of-speech">)(?P<definition>(.|\n)+?)(?P<end>$|</span>)', s)
        if not match: break
        if match.group('class') == 'title="Part-of-speech">':
            if s[(match.end())%len(s)] != ':':
                l.append('<p><strong>' + match.group('definition') + '</strong></p>')
            else:
                l.append('<p><strong>' + 'Synonymous ' + match.group('definition') + 's' + '</strong></p>')
            index = 1
        else:
            if match.group('end'):
                tmp = re.search(r'dict_lk">(?P<definition>.*)</a>',match.group('definition'))
                if tmp: 
                    l.append('<p>' + str(index) + '. <a href="' + tmp.group('definition') + '">' + tmp.group('definition') + '</p>')
                else :
                    l.append('<p>' + str(index) + '. ' + match.group('definition') + '</p>')
                index += 1
            else:
                print(match.group('definition'))
                l.append('<p>● ' + match.group('definition') + '</p>')
        s = s[match.end():]
#    l.append('<FONT color=#00ff00>proba :)</FONT>')
    return ''.join(l)
        

def find_translation(from_lang, to_lang, text):
    conn = connect_to_dictionary(text_url(from_lang, to_lang, text))
    s = ''.join((_.decode() for _ in conn.readlines()))
    
    res = '<p><strong>' + text + '<strong></p>'

    match = re.search(r'(?P<class><ol><li>|<td><b>)(?P<definition>.*?)</li>', s)
    
    if not match:
        match = re.search(r'overflow:auto">(?P<definition>.*?)&lt;br&gt;</textarea>', s)
        if not match:
            return  res + '<b>Could not find definition</b>'
        return '<p>' + re.sub('&lt;br&gt;', '</p> <p>', match.group('definition')) + '</p>'
    index = 1

    while match:
        if match.group('class') == r'<ol><li>':
            res += '<p> ' + str(index) + '. ' + match.group('definition') + '</p>'
            index += 1
        else:
            res += '<p><strong>' + match.group('definition') + '</p></strong>'
            index = 1
        
        s = s[match.end():]
        match = re.search(r'(?P<class><ol><li>|<td><b>)(?P<definition>.*?)</li>', s)

    return res        
        
