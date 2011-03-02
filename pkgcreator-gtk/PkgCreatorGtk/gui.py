import os
import gtk
import yaml
import resources
from tabgeneral import TabGeneral
from tabfiles import TabFiles
from tabrelationships import TabRelationships

class GUI:
    def __init__(self):
        #Builder and main window
        self.builder = gtk.Builder()
        self.builder.add_from_file(resources.GUI_PATH)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window1")
        self.window.connect("destroy", gtk.main_quit)
        #Tabs GUI content responsible
        self.tabgeneral = TabGeneral(self.builder, self)
        self.tabrelationships = TabRelationships(self.builder, self)
        self.tabfiles = TabFiles(self.builder, self)
        
        #Dialogs
        self.about = self.builder.get_object("aboutdialog1")
        self.msgdiagSaveChanges = self.builder.get_object("msgdiagSaveChanges")
        self.msgdiagErrorFile = self.builder.get_object("msgdiagErrorFile")
        #File dialogs related
        self.fileDiagOpen = self.builder.get_object("filechooserOpen")
        self.fileDiagSave = self.builder.get_object("filechooserSave")
        self.buttonDiagSave = self.builder.get_object("buttonDiagSave")
        self.buttonDiagOpen = self.builder.get_object("buttonDiagOpen")
        #Other properties
        self.filename = None
        self.dict = {}
        #Config procedure
        self.__config_file_choosing()
        self.tabgeneral.config()
        self.__config_actions()

    def show(self):
        self.window.show_all()
        gtk.main()

    def quit(self, widget, *event):
        if(self.__warn_user()):
            gtk.main_quit()

    def show_about(self, widget, *event):
        self.about.run()
        self.about.hide()
    
    #File related

    def new(self, widget, *event):
        if(self.__warn_user()):
            self.filename = None
            self.__update_title()
            self.dict = {}
            self.tabgeneral.clear_all()
            self.tabfiles.clear_all()
            self.tabrelationships.clear_all()
            self.actionsSave.set_sensitive(False)
            self.actionsPrjOpened.set_sensitive(False)
            #clear output

    def open(self, widget, *event):
        if(self.__warn_user()):
            response = self.fileDiagOpen.run()
            self.fileDiagOpen.hide()
            if response == gtk.RESPONSE_OK:
                filename = self.fileDiagOpen.get_filename()
                if filename and filename.endswith(".yaml"):
                    with open(filename) as f:
                        try:
                            self.dict = yaml.load(f)
                            self.tabgeneral.from_dict(self.dict)
                            self.tabfiles.from_dict(self.dict)
                            self.tabrelationships.from_dict(self.dict)
                            self.actionsSave.set_sensitive(False)
                            self.actionsPrjOpened.set_sensitive(True)
                            self.filename = filename
                        except Exception as e:
                            #@todo: Put a msg box here
                            print "INVALID FILE!"
                            print e
                        finally:
                            self.__update_title()
                else:
                    self.msgdiagErrorFile.run()
                    self.msgdiagErrorFile.hide()

    def save(self, widget=None, *event):
        if self.filename:
            self.dict = {}
            self.tabgeneral.populate_dict(self.dict)
            self.tabfiles.populate_dict(self.dict)
            self.tabrelationships.populate_dict(self.dict)
            with open(self.filename, 'w') as f:
                yaml.dump(self.dict, f)
            self.actionsSave.set_sensitive(False)
        else:
            self.save_as()

    def save_as(self, widget=None, *event):
        response = self.fileDiagSave.run()
        self.fileDiagSave.hide()
        if response == gtk.RESPONSE_OK:
            filename = self.fileDiagSave.get_filename()
            if filename and filename.endswith(".yaml"):
                self.filename = filename
                self.save()
                self.__update_title()
            else:
                self.msgdiagErrorFile.run()
                self.msgdiagErrorFile.hide()

    def data_changed(self, widget, *event):
        self.actionsSave.set_sensitive(True)

    #History related

    def undo(self, widget, *event):
        print "Undo"

    def redo(self, widget, *event):
        print "Redo"

    #PkgCreator, kwalify and lintian related
    
    def run_pkgcreator(self, widget, *event):
        print "Run pkgcreator"
        """if file exists, save it and run
        else, warn user that he must save the file before creating the pkg"""

    #Private methods

    def __update_title(self):
        title = 'pkgcreator-gtk :: '
        if self.filename:
            self.window.set_title(title + os.path.basename(self.filename))
        else:
            self.window.set_title(title + '<untitled project>')
    
    def __warn_user(self):
        if self.actionsSave.get_sensitive():    #or if document.has_changes()
            response = self.msgdiagSaveChanges.run()
            self.msgdiagSaveChanges.hide()
            if response == gtk.RESPONSE_NO: return True         #proceed without saving
            elif response == gtk.RESPONSE_CANCEL: return False  #cancel operation
            elif response == gtk.RESPONSE_YES:                  #save and proceed
                self.save()
                return True
        else:                                   #proceed
            return True

    def __config_file_choosing(self):
        filefilter = self.builder.get_object("filefilterYAML")
        filefilter.add_mime_type('application/x-yaml')

    def __config_actions(self):
        self.actionsSave = gtk.ActionGroup("SaveCommands")
        self.actionsSave.add_action(self.builder.get_object("actionSave"))
        self.actionsSave.add_action(self.builder.get_object("actionSaveAs"))
        self.actionsSave.set_sensitive(False)
        #With a project opened: Run pkgcreator, validate document, run lintian, etc...
        self.actionsPrjOpened = gtk.ActionGroup("ProjectOpened")
        self.actionsPrjOpened.add_action(self.builder.get_object("actionRunPkgCreator"))
        self.actionsPrjOpened.set_sensitive(False)