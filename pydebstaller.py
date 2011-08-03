#!/usr/bin/python
# -*-encoding: iso-8859-1-*-
# For The Licence, See gpl.txt
# Written by dabear
# making good use of the pygtk-demo package
'''Dadebstaller

This program is a graphical frontend for dpkg. Run in from the command line with
Â«debinstall "debfile.deb"Â» or by double clicking a deb (must be configured first)
(Revision 0.1.0.0)
'''

import os,pygtk,commands,sys #,re
pygtk.require('2.0')
import gtk

GLOBAL_NAME= 'DaDebstaller (by dabear)'
GLOBAL_RUN_AS_ROOT = 'To run %s, you need to enter your admin password' % GLOBAL_NAME
GLOBAL_DEBUG = False

#todo: fix some bugs in up/-degrade, get regex working.
#what if dpkg-query is localized?

    
def validDEB( deb):
    #placing this in the InstallDEB class gave me an error :S
    if os.path.isfile(deb) and os.path.splitext(deb)[1] == '.deb':
        return True  
    return False    
    
class InstallDEB:
    'This class is responsible for maintaining and checking statuses on deb packages'
    def __init__(self, debpath=None, onerror=None):
        self.onerror=onerror
        if debpath is None:
            try:
                debpath=sys.argv[1]   
            except:
                pass
                    
        if not validDEB(debpath):
           if callable(onerror):
               onerror('invalid deb file')
               self.onerror=onerror
           else:
               print 'invalid deb file'
           sys.exit()
        else:
            pass
            self.debpath = debpath
    def info(self, reload=False):
        'This function returns info (and sets the same info in self.info) about the deb file located in the second param to this program'
        #TODO: get the darn regex working, so that we get the full description field, not
        #only the first line
        lines = commands.getoutput('dpkg-deb -I ' + sys.argv[1]).split('\n')
        interests = ['Package', 'Version', 'Section', 'Description']
        info={}
        
        #if reload == False and not self.info:
         
         #   return self.info
        for get in interests:
            #print '--'.join([x for x in lines if get in lines])
            for data in lines:
                trimmed = data.strip()
                #print get == data[0:len(get)+1].strip(' ')
                #if data[0:len(get)+1] == get:
                #   print data
                stripped =data[0:len(get)+1].strip(' ')
                if get == stripped:
                    info[get] = data[len(get)+3:]
        
        #com = re.compile('/Package: (?P<package>[^\n]*)\s*Version: (?P<version>[^\n]*)\s*Section: (?P<section>[^\n]*).*?Description: (?P<description>.*)$/s')
       # info = re.compile(r'/Package: (<package>[^\n]*)\s*Version: (?P<version>[^\n]*)\s*Section: (?P<section>[^\n]*).*?Description: (?P<description>.*)/', re.I or re.S ).match(lines).group(0)
        self.info = info     
        return info
        
    def isInstalled(self,package=None):
        'Tells if package is installed or not. Return True if installed, otherwise False'
        if package is None and self.info:
            package = self.info['Package']
        dpkg_query  = commands.getoutput('dpkg-query --show ' + package)

       
        if (dpkg_query == 'No packages found matching ' + package) \
        or (dpkg_query.split('\t')[1]) == '':
            #print 'Package `%s` is not installed' % package
            return False
        else:
            #print 'length:', dpkg_query.split('\t')
            #print 'last is empty:', (dpkg_query.split('\t')[1]) == ''
            #print 'Package %s is installed' % package
            
            self.installedQuery = dpkg_query
            return True
            
    def upgradable(self, debpath=None):
        'Tells if package (not specified=self.debpath) is an upgrade/degrade form the version installes on the system. If the package is not installed; return False. Returns True or False depending on success or failure'
        if debpath is None:
            debpath = self.debpath
            
        if  (not self.isInstalled()) or self.__equalVersion(): return False
        #impliement dpkg --compare-versions ver1 > ver2
        #if version installed is less than version in package, then
        # the the version in the package is newer, show upgrade 
        ltC ='if dpkg --compare-versions "'+ self.versionInstalled  + '" lt "' + \
        self.versionInPackage + '";then echo yes; fi '
        if commands.getoutput(ltC) == 'yes':
            return True
        return False
    def downgradable(self, debpath=None):
        if  (not self.isInstalled()) or self.__equalVersion():  return False 
        #impliement dpkg --compare-versions ver1 > ver2
        #if version installed is higher than in package, show downgrade
        # the the version in the package is newer, show upgrade 
        gtC ='if dpkg --compare-versions "'+ self.versionInstalled  + '" gt "' + \
        self.versionInPackage + '";then echo yes; fi '
        if commands.getoutput(gtC) == 'yes':
            return True
        return False
    def __equalVersion(self):
        installed = self.isInstalled()
        if not installed: return False
        string = self.installedQuery    
        self.versionInstalled = string.split('\t')[1]
        self.versionInPackage = self.info['Version']
        if self.versionInPackage == self.versionInstalled:
            return True
        return False
    def install(self, debpath=None, onerror=None, onsuccess=None, *args):
        if debpath is None:
            debpath = self.debpath
        if onerror is None:
            onerror = self.onerror 
        if onsuccess is None:
            onsuccess = onerror
        #onerror('testing installation', *args)       
        dpkg_install = commands.getoutput('dpkg -i %s' %(self.debpath))
        isSuccess = self.isInstalled()
        if isSuccess:
            onsuccess('package `%s` is now installed!' % self.debpath, *args)
        else:
        	onerror('package `%s` didn\'t get installed\n\n%s' %\
        	(self.debpath, dpkg_install), *args)
        	
    def remove(self,debName=None, onerror=None, onsuccess=None, *args):
        if debName is None:
            deb_name = self.info['Package']
        if onerror is None:
            onerror = self.onerror 
        if onsuccess is None:
            onsuccess = onerror
        dpkg_remove = commands.getoutput('dpkg --remove %s' % deb_name )
        #if it still is installed, something wrong happend
        isFailure = self.isInstalled()
        if isFailure:
            onerror('Package `%s` was not removed\n\n%s' % (deb_name, dpkg_remove),*args)
        else:
            onsuccess('Package `%s` successfully removed from your system' %deb_name, *args)
class DebstallerGUI(gtk.Window):
    def __init__(self, parent=None):
        'initializes GUI or gives a pop-up warning if deb isn\'t valid'
        try:
            deb = sys.argv[1]
            if not validDEB(deb): raise Exception
        except IndexError:
            self.incorrectDEB('I am sorry, installation can not continue as \
                there was no deb specified for installation')
        except:
            self.incorrectDEB()        
        else:
            # Create the toplevel window
            gtk.Window.__init__(self)
                
            try:
                self.set_screen(parent.get_screen())
            except AttributeError:
                self.connect('destroy', lambda *w: gtk.main_quit())
                self.set_default_size(569, 300)
                self.set_title(GLOBAL_NAME)
                self.set_border_width(1)
                self.extraInfo = ''
                main_vbox = gtk.VBox()
                self.add(main_vbox)
    
                self.debObj = InstallDEB(onerror=self.dialog)
                deb_name = os.path.basename(deb)
    
        #-----------------------------------------------------------------------
        #
        #Here is the main frame created. Package information also comes here
        #
        #-----------------------------------------------------------------------

                frame_horiz = gtk.Frame('Installing package `%s`:' % deb_name)
                info = self.debObj.info()
                #self.dialog(str([x + ':' +y for x,y in yo]))
                package = info['Package'] + ' v.'+ info['Version'] + '\n' + \
                info['Description']
    
                #self.debObj.isInstalled() is checked by upgradable/downgradable
                if self.debObj.upgradable():
                    self.extraInfo += '''\
Note: You are about to install a newer version than currently installed on your system
                    '''
                elif self.debObj.downgradable():
                    self.extraInfo += '''\
Note: You are about to install a lower version than currently installed on your system
                    '''    
                    
                #show reinstall button eventually??    
                elif self.debObj.isInstalled():
                    self.extraInfo += '''\
Note: This version of the package is already installed on your system!
 Please press the quit button to exit this program
                    '''   
                 

                #add information
                greeting = '''
Welcome to the %s! By pressing OK, you will be installing the
package named %s on to your Ubuntu Breezy system.

You are about to install, remove or reinstall
    %s
    %s
                ''' % (GLOBAL_NAME, deb_name, package ,self.extraInfo)
                label = gtk.Label(greeting)
                frame_horiz.add(label)
                
                main_vbox.pack_start(frame_horiz, padding=10)

                bbox = self.createBoxes()
                #self.debObj.isInstalled()
                #dpkg-query --show alacarte
                #alacarte        0.8-0ubuntu1
               
                main_vbox.pack_start(bbox, padding=10)
                
                self.show_all()
    def createBoxes(self):
        bbox = gtk.HButtonBox()
        bbox.set_spacing(2)
        
        button = gtk.Button(stock='gtk-quit')
        button.connect('clicked', lambda button, w=self: w.destroy())
        button.set_flags(gtk.CAN_DEFAULT)
        bbox.add(button)
        
        button = gtk.Button(stock='gtk-info')
        button.connect('clicked',  self.displayInfo)
        bbox.add(button)
        
        if self.debObj.isInstalled():
            #note: show reinstall and remove button??
            button = gtk.Button('Uninstall Package')
            #("signal_name", handler, arg1, arg2, arg3)
            button.connect('clicked', self.installation, 'remove')
            bbox.add(button)
            
            button = gtk.Button('Reinstall')
            button.connect('clicked', self.installation, 'reinstall')
            bbox.add(button)  
        #if is installed, but this is an older or newer version or
        #this package is not installed
        #elif self.debObj.isInstalled():  
        else:
            button = gtk.Button(stock='gtk-ok')
            #("signal_name", handler, arg1, arg2, arg3)
            button.connect('clicked', self.installation)
            bbox.add(button)
        
        
        #if installed and upgradable
        if  self.debObj.upgradable():        
            button = gtk.Button('Upgrade/')
            button.connect('clicked', self.installation)
            bbox.add(button)
        elif self.debObj.downgradable():
            button = gtk.Button('Force Downgrade')
            button.connect('clicked', self.installation, 'reinstall')
            bbox.add(button)          

        return bbox
        
    def installation(self, object, mode='install'):
        #self.dialog('mode:' +mode)
        if mode == 'install':   
            self.debObj.install(onsuccess=self.dialog)            
        elif mode == 'remove':
            self.debObj.remove(onsuccess=self.dialog)
        elif mode == 'reinstall':
            #debName=None, onerror=None, onsuccess=None, *args):
            self.debObj.remove(None,self.dialog, None, False)
            self.debObj.install(onsuccess=self.dialog)  
        else: return False 
       
    def buff(self, message):
        if i: i += i
        else: i = 0
        if i >= 2:
            self.dialog(message)
            message=''    
        
                
    def displayInfo(self, object, status=None,quit=False):        
        'installs and shows status about deb'
        #prints only info yet. should be used to install deb
        #print 'kom hit'
        deb = self.debObj.info
        info = str(deb)
        self.dialog(info, quit) 
        return False 
        
                
    def dialog(self, message, quit=True):
        dialog = gtk.MessageDialog(self,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
        message)
        dialog.run()
        dialog.destroy()
        if quit:
            gtk.main_quit()
            sys.exit()  
         
    def incorrectDEB(self, message=None):
        if not message: message = 'I am sorry, the specified file is not a deb'
        self.dialog(message)
        
def main():
    DebstallerGUI()
    gtk.main()
    
def requireRoot():
    userName = os.getenv('LOGNAME')
    #if not root, kill and prompt to open this file as root
    if userName == 'root':  return True
    return False

if __name__ == '__main__':
    #ensure user is root
    if GLOBAL_DEBUG:
        deb = InstallDEB()
        info = deb.info()
        #print  info['Package'], 'v.'+ info['Version'], '\n', info['Description']
        print 'this is an upgrade:',deb.upgradable()
        print 'this is a downgrade:',deb.downgradable()
        print 'is installed:',deb.isInstalled()
        #print deb.install()
        
        sys.exit(0)
    if requireRoot():
        main()               
    else:
    #Run this script again as root, if deb isn't specified, give a message
        try:
            s= 'gksudo --message="' + GLOBAL_RUN_AS_ROOT + '" "python %s %s"' % \
            (sys.argv[0], sys.argv[1])
            #print s
            test = commands.getoutput(s)
            #print test
        except IndexError: 
            print '''
            You must call this with ONE parameter,
            specifying the location of the deb'
            '''
        sys.exit(1)
