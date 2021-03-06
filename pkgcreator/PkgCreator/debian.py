#!/usr/bin/env python
#@TODO: Validate file before

import os
import codecs
from stat import S_IRWXU,  S_IXGRP, S_IRGRP, S_IXOTH, S_IROTH
from PkgCreator import utils
from PkgCreator.console import console as c
from PkgCreator.abstract_generator import AbstractGenerator
from PkgCreator.abstract_generator import MSG_INSTALL, MSG_MENUS, MSG_ICONS, MSG_PACKAGING
from PkgCreator.menu_creator import POSTINST, POSTRM

RELATIONSHIPS = {}
for i in ('depends', 'recommends', 'suggests', 'enhances', 'pre_depends',
          'breaks', 'conflicts', 'provides', 'replaces'):
    RELATIONSHIPS[i] = i.replace('_', ' ').title().replace(' ', '-')
OTHER_FIELDS = {}
for i in ('section', 'priority', 'homepage', 'essential'):
    OTHER_FIELDS[i] = i.title()

class DebianGenerator(AbstractGenerator):
    def __init__(self, pkg_markup, outputdir, color):
        AbstractGenerator.__init__(self, pkg_markup, outputdir, color)
        self.distdir = self.outputdir
        self.outputdir = os.path.join(self.outputdir, 'deb')
        self.debiandir = os.path.join(self.outputdir, 'DEBIAN')
    def format_long_description(self, long_description):
        lines = long_description.splitlines()
        for n in range(len(lines)):
            lines[n] = ' ' + lines[n]
            if lines[n] == ' ':
                lines[n] += '.'
        return "\n".join(lines)
    def create_package(self):
        #Install files
        c.title(MSG_INSTALL)
        for f in self.info['files']:
            src = f['src']
            dst = os.path.join(self.outputdir, f['dst'][1:])
            utils.copy_file(src, dst)
        #Menus
        if 'menu' in self.info.keys():
            c.title(MSG_MENUS)
            menus = self.menu_creator.create()
            for m in menus:
                path = os.path.join(self.outputdir, m['path'])
                utils.create_file(path, m['content'])
            #Icons
            if 'icon' in self.info['menu'].keys():
                c.title(MSG_ICONS)
                icons = self.icon_creator.create()
                if icons:
                    for i in icons:
                        path = os.path.join(self.outputdir, i['path'])
                        c.eprint('- Creating icon %s ...' % path, indent=1)
                        utils.create_path(os.path.dirname(path))
                        i['img'].save(path)
        #Creating Debian-related files
        c.title('Generating Debian stuff')
        if 'menu' in self.info.keys():
            c.eprint('- Creating postinst and postrm scripts ...', indent=1)
            postinst = os.path.join(self.debiandir, 'postinst')
            postrm = os.path.join(self.debiandir, 'postrm')
            utils.create_file(postinst, POSTINST)
            utils.create_file(postrm, POSTRM)
            mode = S_IRWXU | S_IXGRP | S_IRGRP | S_IXOTH | S_IROTH
            os.chmod(postinst, mode)
            os.chmod(postrm, mode)
        #MD5Sum and installed size
        ignore_list = ['.svn', 'DEBIAN']
        c.eprint('- Calculating md5sums ...', indent=1, end='')
        md5sum_path = os.path.join(self.debiandir, 'md5sums')
        md5sum_values = utils.calculate_md5sums(self.outputdir, ignore_list)
        md5sum_values = md5sum_values.replace(self.outputdir + '/', '')
        c.print_success(md5sum_values)
        utils.create_file(md5sum_path, md5sum_values)
        c.eprint('- Calculating installed size ...', indent=1, end='')
        installed_size = utils.calculate_size(self.outputdir, ignore_list)
        installed_size = int ( round ( float (installed_size) / 1000 ) )
        c.print_success(installed_size)
        c.eprint('- Generating Control file ...', indent=1, end='')
        #Shortcut
        g = self.info['general']
        fpath = os.path.join(self.debiandir, 'control')
        with codecs.open(fpath, 'wt', 'utf-8') as f:
            f.write('Package: ' + g['package_name'] + '\n')
            f.write('Version: ' + str(g['version']) + '\n')
            f.write('Architecture: ' + g['architecture'] + '\n')
            f.write('Installed-Size: ' + str(installed_size) + '\n')
            e = lambda name, email: name + ' <' + email + '>'
            maintainer = e(g['maintainer']['name'], g['maintainer']['email'])
            f.write('Maintainer: ' + maintainer + '\n')
            #Related packages
            for r in RELATIONSHIPS.keys():
                if r in self.info:
                    items = ''
                    for d in self.info[r]:
                        items += d['name']
                        if 'version' in d.keys() and d['version']:
                            items += '(' + d['version'] + ')'
                        items += ', '
                    items = items[:-2] #remove last ,<space>
                    f.write(RELATIONSHIPS[r] + ': ' + items + '\n')
            #Other Debian control file fields:
            for o in OTHER_FIELDS.keys():
                if o in g.keys():
                    f.write(OTHER_FIELDS[o] + ': ' + g[o] + '\n')
            #Description:
            f.write('Description: ')
            if 'short_description' in g.keys():
                f.write(g['short_description'] + '\n')
            else:
                f.write('\n')
            if 'long_description' in g.keys():
                #@TODO: Format long description acording to Debian rules
                f.write(self.format_long_description(g['long_description']))
            f.write('\n')
        c.print_success(True)
        c.title(MSG_PACKAGING)
        c.eprint('- Running dpkg: ', indent=1, end='')
        cmd = 'dpkg-deb -b %s %s-%s.deb' % (
            self.outputdir, os.path.join(self.distdir, g['package_name']),
            g['version']
        )
        result = os.system(cmd)
        c.eprint('- Final package: ', indent=1, end='')
        c.print_success(not result)
        c.reset()
        self.quit_with_message(not result)

if __name__ == '__main__':
    g = DebianGenerator()
    g.create_package()