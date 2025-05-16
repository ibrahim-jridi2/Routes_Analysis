import glob
import codecs

for f in glob.glob('*.py'):
    try:
        with codecs.open(f, 'r', 'utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        try:
            with codecs.open(f, 'r', 'windows-1252') as file:
                content = file.read()
            with codecs.open(f, 'w', 'utf-8') as file:
                file.write(content)
            print(f'Converted {f} from windows-1252 to utf-8')
        except Exception as e:
            print(f'Could not convert {f}: {e}')