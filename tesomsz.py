from eme.entities import load_settings

file = 'routes.ini'

f = load_settings(file, delimiters=('=>','->')).conf

print(f)