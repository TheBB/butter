import imagehash
import os.path as path
from PIL import Image
from subprocess import run

from butter import gui, programs


def collision_check(db, filename, threshold=9):
    this_hash = imagehash.phash(Image.open(filename))
    collisions = [pic for pic in db.query() if pic - this_hash <= threshold]

    if collisions:
        input(f'{len(collisions)} collisions found...')
        gui.run_gui(program=programs.Images.factory(filename, *collisions))
        choice = input('(r) replace, (d) delete, (s) skip, (a) add anyway ').strip().lower()[0]
        if choice == 'd':
            run(['rm', filename])
            db.plugin_manager.add_failed(filename, reason='collision')
            return False
        if choice == 's':
            db.plugin_manager.add_failed(filename, reason='skip')
            return False
        if choice == 'r':
            for pic in collisions:
                db.delete(pic)
            db.session.commit()
            return True

    return True


def populate(db, filename):
    print('Staged: {}'.format(filename))

    gui.run_gui(program=programs.Images.factory(filename))

    extension = path.splitext(filename)[-1].lower()
    if extension == '.jpeg':
        extension = '.jpg'

    pic = db.Picture()
    pic.extension = extension[1:]
    modified = False
    while True:
        s = input('>>> ').strip()
        if s == '':
            if modified:
                return pic
            return None
        elif s == 'view':
            gui.run_gui(program=Images.factory(filename))
        elif s == 'skip':
            return None
        elif s == 'done':
            return pic
        elif s == '?':
            print(pic)
        else:
            try:
                if '=' in s:
                    key, value = s.split('=')
                    value = value.strip()
                    if value:
                        pic.assign_field(key, eval(value))
                else:
                    value = True
                    if s.startswith('not'):
                        value = False
                        s = s[3:]
                    pic.assign_field(s, value)
                    modified = True
            except Exception as e:
                print(e)
