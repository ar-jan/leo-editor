# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20181103094900.1: * @file leoflexx.py
#@@first
#@@language python
#@@tabwidth -4
'''
A Stand-alone prototype for Leo using flexx.
'''
# pylint: disable=logging-not-lazy
#@+<< leoflexx imports >>
#@+node:ekr.20181113041314.1: ** << leoflexx imports >>
# import leo.core.leoGlobals as g
import leo.core.leoBridge as leoBridge
import leo.core.leoGui as leoGui
import leo.core.leoNodes as leoNodes
from flexx import flx
import re
import time
assert re and time
    # Suppress pyflakes complaints
#@-<< leoflexx imports >>
#@+<< ace assets >>
#@+node:ekr.20181111074958.1: ** << ace assets >>
# Assets for ace, embedded in the LeoFlexxBody and LeoFlexxLog classes.
base_url = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/'
flx.assets.associate_asset(__name__, base_url + 'ace.js')
flx.assets.associate_asset(__name__, base_url + 'mode-python.js')
flx.assets.associate_asset(__name__, base_url + 'theme-solarized_dark.js')
#@-<< ace assets >>
debug = False
debug_tree = True
#@+others
#@+node:ekr.20181103151350.1: **  init
def init():
    # At present, leoflexx is not a true plugin.
    # I am executing leoflexx.py from an external script.
    return False
#@+node:ekr.20181113041410.1: **  suppress_unwanted_log_messages
def suppress_unwanted_log_messages():
    '''
    Suppress the "Automatically scrolling cursor into view" messages by
    *allowing* only important messages.
    '''
    allowed = r'(Critical|Error|Leo|Session|Starting|Stopping|Warning)'
    pattern = re.compile(allowed, re.IGNORECASE)
    flx.set_log_level('INFO', pattern)
#@+node:ekr.20181107052522.1: ** class LeoApp(PyComponent)
# pscript never converts flx.PyComponents to JS.

class LeoApp(flx.PyComponent):
    '''
    The Leo Application.
    This is self.root for all flx.Widget objects!
    '''
    # This may be optional, but it doesn't hurt.
    main_window = flx.ComponentProp(settable=True)

    def init(self):
        c, g = self.open_bridge()
        print('app.init: c.frame', repr(c.frame))
        self.c, self.g = c, g
        self.gui = LeoBrowserGui(c, g)
        # Create all data-related ivars.
        self.create_all_data()
        # Create the main window and all its components.
        signon = '%s\n%s' % (g.app.signon, g.app.signon2)
        body = c.rootPosition().b
        redraw_dict = self.make_redraw_dict()
        main_window = LeoFlexxMainWindow(body, redraw_dict, signon)
        self._mutate('main_window', main_window)

    #@+others
    #@+node:ekr.20181111152542.1: *3* app.actions
    #@+node:ekr.20181111142921.1: *4* app.action: do_command
    @flx.action
    def do_command(self, command):

        w = self.main_window
        if command == 'redraw':
            d = self.make_redraw_dict()
            if 1:
                w.tree.redraw(d)
            else: # works.
                self.dump_redraw_dict(d)
        elif command == 'test':
            self.test_round_trip_positions()
            self.run_all_unit_tests()
        else:
            print('app.do_command: unknown command: %r' % command)
            ### To do: pass the command on to Leo's core.
    #@+node:ekr.20181113053154.1: *4* app.action: dump_redraw_dict & helpers
    @flx.action
    def dump_redraw_dict(self, d):
        '''Pretty print the redraw dict.'''
        print('app.dump_redraw dict...')
        padding, tag = None, 'c.p'
        self.dump_ap(d ['c.p'], padding, tag)
        level = 0
        for i, item in enumerate(d ['items']):
            self.dump_redraw_item(i, item, level)
            print('')
    #@+node:ekr.20181113085722.1: *5* app.action: dump_ap
    @flx.action
    def dump_ap (self, ap, padding=None, tag=None):
        '''Print an archived position fully.'''
        stack = ap ['stack']
        if not padding:
            padding = ''
        padding = padding + ' '*4 
        if stack:
            print('%s%s:...' % (padding, tag or 'ap'))
            padding = padding + ' '*4
            print('%schildIndex: %s v: %s %s stack...' % (
                padding,
                str(ap ['childIndex']),
                ap['gnx'],
                ap['headline'],
            ))
            padding = padding + ' '*4
            for d in ap ['stack']:
                print('%s%s %s %s' % (
                    padding,
                    str(d ['childIndex']).ljust(3),
                    d ['gnx'],
                    d ['headline'],
                ))
        else:
            print('%s%s: childIndex: %s v: %s stack: [] %s' % (
                padding, tag or 'ap',
                str(ap ['childIndex']).ljust(3),
                ap['gnx'],
                ap['headline'],
            ))
    #@+node:ekr.20181113091522.1: *4* app.action: redraw_item
    @flx.action
    def dump_redraw_item(self, i, item, level):
        '''Pretty print one item in the redraw dict.'''
        padding = ' '*4*level
        # Print most of the item.
        print('%s%s gnx: %s body: %s %s' % (
            padding,
            str(i).ljust(3),
            item ['gnx'].ljust(25),
            str(len(item ['body'])).ljust(4),
            item ['headline'],
        ))
        tag = None
        self.dump_ap(item ['ap'], padding, tag)
        # Print children...
        children = item ['children']
        if children:
            print('%sChildren...' % padding)
            print('%s[' % padding)
            padding = padding + ' '*4
            for j, child in enumerate(children):
                index = '%s.%s' % (i, j)
                self.dump_redraw_item(index, child, level+1)
            padding = padding[:-4]
            print('%s]' % padding)
    #@+node:ekr.20181112165240.1: *4* app.action: info (deprecated)
    @flx.action
    def info (self, s):
        '''Send the string s to the flex logger, at level info.'''
        if not isinstance(s, str):
            s = repr(s)
        flx.logger.info('Leo: ' + s)
            # A hack: automatically add the "Leo" prefix so
            # the top-level suppression logic will not delete this message.
    #@+node:ekr.20181113042549.1: *4* app.action: redraw
    def redraw (self):
        '''
        Send a **redraw list** to the tree.
        
        This is a recusive list lists of items (ap, gnx, headline) describing
        all and *only* the presently visible nodes in the tree.
        
        As a side effect, app.make_redraw_dict updates all internal dicts.
        '''
        print('app.redraw')
        w = self.main_window
        d = self.make_redraw_dict()
        w.tree.redraw(d)

        
    #@+node:ekr.20181111202747.1: *4* app.action: select_ap
    @flx.action
    def select_ap(self, ap):
        '''Select the position in Leo's core corresponding to the archived position.'''
        c = self.c
        p = self.ap_to_p(ap)
        c.frame.tree.select(p)
    #@+node:ekr.20181111095640.1: *4* app.action: send_children_to_tree
    @flx.action
    def send_children_to_tree(self, parent_ap):
        '''
        Call w.tree.receive_children(d), where d has the form:
            {
                'parent': parent_ap,
                'children': [ap1, ap2, ...],
            }
        '''
        w = self.main_window
        p = self.ap_to_p(parent_ap)
        if p.hasChildren():
            w.tree.receive_children({
                'parent': parent_ap,
                'children': [self.p_to_ap(z) for z in p.children()],
            })
        elif debug: ###
            # Not an error.
            print('app.send_children_to_tree: no children', p.h)
    #@+node:ekr.20181111095637.1: *4* app.action: set_body
    @flx.action
    def set_body(self, ap):
        '''Set the body text in LeoFlexxBody to the body text of indicated node.'''
        w = self.main_window
        gnx = ap ['gnx']
        v = self.gnx_to_vnode [gnx]
        assert v, repr(ap)
        w.body.set_body(v.b)
    #@+node:ekr.20181111095640.2: *4* app.action: set_status_to_unl
    @flx.action
    def set_status_to_unl(self, ap):
        '''Output the status line corresponding to ap.'''
        c, g, w = self.c, self.g, self.main_window
        gnxs = [z ['gnx'] for z in ap ['stack']]
        vnodes = [self.gnx_to_vnode[z] for z in gnxs]
        headlines = [v.h for v in vnodes]
        headlines.append(ap ['headline'])
        fn = g.shortFileName(c.fileName())
        w.status_line.set_text('%s#%s' % (fn, '->'.join(headlines)))
    #@+node:ekr.20181114015356.1: *3* app.create_all_data
    def create_all_data(self):
        '''Compute the initial values all data structures.'''
        t1 = time.clock()
        # This is likely the only data that ever will be needed.
        self.gnx_to_vnode = { v.gnx: v for v in self.c.all_unique_nodes() }
        t2 = time.clock()
        print('app.create_all_data: %5.2f sec. %s entries' % (
            (t2-t1), len(list(self.gnx_to_vnode.keys()))))
        if debug:
            self.test_round_trip_positions()
    #@+node:ekr.20181111155525.1: *3* app.archived positions
    #@+node:ekr.20181111204659.1: *4* app.p_to_ap (updates app.gnx_to_vnode)
    def p_to_ap(self, p):
        '''
        Convert a true Leo position to a serializable archived position.
        '''
        gnx = p.v.gnx
        if gnx not in self.gnx_to_vnode:
            print('=== update gnx_to_vnode', gnx.ljust(15), p.h,
                len(list(self.gnx_to_vnode.keys())))
            self.gnx_to_vnode [gnx] = p.v
        return {
            'childIndex': p._childIndex,
            'gnx': gnx,
            'headline': p.h, # For dumps.
            'stack': [{
                'gnx': v.gnx,
                'childIndex': childIndex,
                'headline': v.h, # For dumps & debugging.
            } for (v, childIndex) in p.stack ],
        }
    #@+node:ekr.20181111203114.1: *4* app.ap_to_p (uses gnx_to_vnode)
    def ap_to_p (self, ap):
        '''Convert an archived position to a true Leo position.'''
        childIndex = ap ['childIndex']
        v = self.gnx_to_vnode [ap ['gnx']]
        stack = [
            (self.gnx_to_vnode [d ['gnx']], d ['childIndex'])
                for d in ap ['stack']
        ]
        return leoNodes.position(v, childIndex, stack)
    #@+node:ekr.20181113043539.1: *4* app.make_redraw_dict & helpers
    def make_redraw_dict(self):
        '''
        Return a recursive, archivable, list of lists describing all and only
        the visible nodes of the tree.
        
        As a side effect, all LeoApp data are recomputed.
        '''
        c = self.c
        t1 = time.clock()
        aList = []
        p = c.rootPosition()
        ### Don't do this: it messes up tree redraw.
            # Testing: forcibly expand the first node.
            # p.expand()
        while p:
            if p.level() == 0 or p.isVisible():
                aList.append(self.make_dict_for_position(p))
                p.moveToNodeAfterTree()
            else:
                p.moveToThreadNext()
        d = {
            'c.p': self.p_to_ap(c.p),
            'items': aList,
        }
        if debug_tree:
            t2 = time.clock()
            print('app.make_redraw_dict: %5.4f sec' % (t2-t1))
        return d
    #@+node:ekr.20181113044701.1: *5* app.make_dict_for_position
    def make_dict_for_position(self, p):
        '''
        Recursively add a sublist for p and all its visible nodes.
        
        Update all data structures for p.
        '''
        c = self.c
        self.gnx_to_vnode[p.v.gnx] = p.v
        children = [
            self.make_dict_for_position(child)
                for child in p.children()
                    if child.isVisible(c)
        ]
        return {
            'ap': self.p_to_ap(p),
            'body': p.b,
            'children': children,
            'gnx': p.v.gnx,
            'headline': p.h,
        }
    #@+node:ekr.20181113180246.1: *4* app.test_round_trip_positions
    def test_round_trip_positions(self):
        '''Test the round tripping of p_to_ap and ap_to_p.'''
        c = self.c
        t1 = time.clock()
        for p in c.all_positions():
            ap = self.p_to_ap(p)
            p2 = self.ap_to_p(ap)
            assert p == p2, (repr(p), repr(p2), repr(ap))
        t2 = time.clock()
        if 1:
            print('app.test_new_tree: %5.3f sec' % (t2-t1))
    #@+node:ekr.20181105091545.1: *3* app.open_bridge
    def open_bridge(self):
        '''Can't be in JS.'''
        ### Monkey-Patch leoBridge.createGui???
        
        bridge = leoBridge.controller(gui = None,
            loadPlugins = False,
            readSettings = False,
            silent = False,
            tracePlugins = False,
            verbose = False, # True: prints log messages.
        )
        if not bridge.isOpen():
            flx.logger.error('Error opening leoBridge')
            return
        g = bridge.globals()
        path = g.os_path_finalize_join(g.app.loadDir, '..', 'core', 'LeoPyRef.leo')
        if not g.os_path_exists(path):
            flx.logger.error('open_bridge: does not exist: %r' % path)
            return
        c = bridge.openLeoFile(path)
        return c, g
    #@+node:ekr.20181115171220.1: *3* app.message
    def message(self, s):
        '''For testing.'''
        print('app.message: %s' % s)
    #@+node:ekr.20181112182636.1: *3* app.run_all_unit_tests
    def run_all_unit_tests (self):
        '''
        Run all unit tests from the bridge using the browser gui.
        '''
        print('===== app.run_all_unit_tests')
        self.c.debugCommands.runAllUnitTestsLocally()
        print('===== app.run_all_unit_tests DONE')
    #@-others
#@+node:ekr.20181115071559.1: ** Python wrappers
#@+node:ekr.20181115092337.3: *3* class LeoBrowserBody
class LeoBrowserBody(flx.PyComponent):
   
    def init(self, c, g):
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        self.colorizer = None
        self.use_chapters = False
        self.widget = None
        self.wrapper = StringTextWrapper(c, g, 'body')
        ### From LeoBody
            # frame.body = self
            # self.editorWidgets = {} # keys are pane names, values are text widgets
            # self.frame = frame
            # self.parentFrame = parentFrame # New in Leo 4.6.
            # self.totalNumberOfEditors = 0
            #
            # May be overridden in subclasses...
            # self.numberOfEditors = 1
            # self.pb = None # paned body widget.
    

        ###
            # self.insertPoint = 0
            # self.selection = 0, 0
            # self.s = "" # The body text
            # self.widget = None
            # self.editorWidgets['1'] = wrapper
            # self.colorizer = NullColorizer(self.c)

    #@+others
    #@+node:ekr.20181115092337.4: *4* LeoBrowserBody interface
    # At present theses do not issue messages.

    # Birth, death...
    def createControl(self, parentFrame, p):
        pass

    # Editors...
    def addEditor(self, event=None):
        pass
    def assignPositionToEditor(self, p):
        pass
    def createEditorFrame(self, w):
        return None
    def cycleEditorFocus(self, event=None):
        pass
    def deleteEditor(self, event=None):
        pass
    def selectEditor(self, w):
        pass
    def selectLabel(self, w):
        pass
    def setEditorColors(self, bg, fg):
        pass
    def unselectLabel(self, w):
        pass
    def updateEditors(self):
        pass
    # Events...
    def forceFullRecolor(self):
        pass
    def scheduleIdleTimeRoutine(self, function, *args, **keys):
        pass
        
    # Coloring...
    def recolor(self, p):
        pass
    recolor_now = recolor
    #@+node:ekr.20181115092337.5: *4* bb.setFocus
    def setFocus(self):
        pass
        ### self.message('set-focus-to-body')
    #@+node:ekr.20181115174333.3: *4* LeoBody.cmd (decorator)
    # def cmd(name):
        # '''Command decorator for the c.frame.body class.'''
        # # pylint: disable=no-self-argument
        # return g.new_cmd_decorator(name, ['c', 'frame', 'body'])
    #@+node:ekr.20181115174333.25: *4* LeoBody.Text
    #@+node:ekr.20181115174333.26: *5* LeoBody.getInsertLines
    def getInsertLines(self):
        '''
        Return before,after where:

        before is all the lines before the line containing the insert point.
        sel is the line containing the insert point.
        after is all the lines after the line containing the insert point.

        All lines end in a newline, except possibly the last line.
        '''
        g = self.g
        body = self
        w = body.wrapper
        s = w.getAllText()
        insert = w.getInsertPoint()
        i, j = g.getLine(s, insert)
        before = s[0: i]
        ins = s[i: j]
        after = s[j:]
        before = g.toUnicode(before)
        ins = g.toUnicode(ins)
        after = g.toUnicode(after)
        return before, ins, after
    #@+node:ekr.20181115174333.27: *5* LeoBody.getSelectionAreas
    def getSelectionAreas(self):
        '''
        Return before,sel,after where:

        before is the text before the selected text
        (or the text before the insert point if no selection)
        sel is the selected text (or "" if no selection)
        after is the text after the selected text
        (or the text after the insert point if no selection)
        '''
        g = self.g
        body = self
        w = body.wrapper
        s = w.getAllText()
        i, j = w.getSelectionRange()
        if i == j: j = i + 1
        before = s[0: i]
        sel = s[i: j]
        after = s[j:]
        before = g.toUnicode(before)
        sel = g.toUnicode(sel)
        after = g.toUnicode(after)
        return before, sel, after
    #@+node:ekr.20181115174333.28: *5* LeoBody.getSelectionLines
    def getSelectionLines(self):
        '''
        Return before,sel,after where:

        before is the all lines before the selected text
        (or the text before the insert point if no selection)
        sel is the selected text (or "" if no selection)
        after is all lines after the selected text
        (or the text after the insert point if no selection)
        '''
        g = self.g
        if g.app.batchMode:
            return '', '', ''
        # At present, called only by c.getBodyLines.
        body = self
        w = body.wrapper
        s = w.getAllText()
        i, j = w.getSelectionRange()
        if i == j:
            i, j = g.getLine(s, i)
        else:
            i, junk = g.getLine(s, i)
            junk, j = g.getLine(s, j)
        before = g.toUnicode(s[0: i])
        sel = g.toUnicode(s[i: j])
        after = g.toUnicode(s[j: len(s)])
        return before, sel, after # 3 strings.
    #@+node:ekr.20181115174333.29: *5* LeoBody.onBodyChanged
    # This is the only key handler for the body pane.

    def onBodyChanged(self, undoType, oldSel=None, oldText=None, oldYview=None):
        '''Update Leo after the body has been changed.'''
        c, g = self.c, self.g
        body, w = self, self.wrapper
        p = c.p
        insert = w.getInsertPoint()
        ch = '' if insert == 0 else w.get(insert - 1)
        ch = g.toUnicode(ch)
        newText = w.getAllText() # Note: getAllText converts to unicode.
        newSel = w.getSelectionRange()
        if not oldText:
            oldText = p.b; changed = True
        else:
            changed = oldText != newText
        if not changed: return
        c.undoer.setUndoTypingParams(p, undoType,
            oldText=oldText, newText=newText, oldSel=oldSel, newSel=newSel, oldYview=oldYview)
        p.v.setBodyString(newText)
        p.v.insertSpot = w.getInsertPoint()
        #@+<< recolor the body >>
        #@+node:ekr.20181115174333.30: *6* << recolor the body >>
        c.frame.scanForTabWidth(p)
        body.recolor(p)
        if g.app.unitTesting:
            g.app.unitTestDict['colorized'] = True
        #@-<< recolor the body >>
        if not c.changed: c.setChanged(True)
        self.updateEditors()
        p.v.contentModified()
        #@+<< update icons if necessary >>
        #@+node:ekr.20181115174333.31: *6* << update icons if necessary >>
        redraw_flag = False
        # Update dirty bits.
        # p.setDirty() sets all cloned and @file dirty bits.
        if not p.isDirty() and p.setDirty():
            redraw_flag = True
        # Update icons. p.v.iconVal may not exist during unit tests.
        val = p.computeIcon()
        if not hasattr(p.v, "iconVal") or val != p.v.iconVal:
            p.v.iconVal = val
            redraw_flag = True
        if redraw_flag:
            c.redraw_after_icons_changed()
        #@-<< update icons if necessary >>
    #@+node:ekr.20181115174333.32: *5* LeoBody.setSelectionAreas
    def setSelectionAreas(self, before, sel, after):
        '''
        Replace the body text by before + sel + after and
        set the selection so that the sel text is selected.
        '''
        body = self
        w = body.wrapper
        # 2012/02/05: save/restore Yscroll position.
        pos = w.getYScrollPosition()
        s = w.getAllText()
        before = before or ''
        sel = sel or ''
        after = after or ''
        w.delete(0, len(s))
        w.insert(0, before + sel + after)
        i = len(before)
        j = max(i, len(before) + len(sel) - 1)
        w.setSelectionRange(i, j, insert=j)
        w.setYScrollPosition(pos)
        return i, j
    #@-others
#@+node:ekr.20181115092337.6: *3* class LeoBrowserFrame
class LeoBrowserFrame(flx.PyComponent):
    
    def init(self, c, g):
        '''Ctor for the LeoBrowserFrame class.'''
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        ### self.gui = gui
        self.title = '<LeoBrowserFrame.title>'
        #
        #
        c.frame = self
        assert self.c
        self.isNullFrame = False
        self.ratio = self.secondary_ratio = 0.5
        self.top = None # Always None.
        #
        # Create the component objects.
        self.body = LeoBrowserBody(c, g)
        self.iconBar = LeoBrowserIconBar(c, g)
        self.log = LeoBrowserLog(c, g)
        self.menu = LeoBrowserMenu(c, g)
        self.miniBufferWidget = LeoBrowserMinibuffer(c, g)
        self.statusLine = LeoBrowserStatusLine(c, g)
        self.tree = LeoBrowserTree(c, g)
        #
        # Official component ivars.
        self.colorPanel = None
        self.comparePanel = None
        self.findPanel = None
        self.fontPanel = None
        # self.keys = None
        self.outerFrame = None
        self.prefsPanel = None
        self.wrapper = None
        #
        # Other ivars
        self.cursorStay = True
        self.tab_width = 0
        self.w, self.h, self.x, self.y = 600, 500, 40, 40
            # Default window position.
        #
        ### From LeoFrame
            # # Objects attached to this frame.
            # self.useMiniBufferWidget = False
            # #
            # # Gui-independent data
            # #
            # 
            # self.componentsDict = {} # Keys are names, values are componentClass instances.
            # self.es_newlines = 0 # newline count for this log stream
            # self.openDirectory = ""
            # self.saved = False # True if ever saved
            # self.splitVerticalFlag = True
                # # Set by initialRatios later.
            # self.startupWindow = False # True if initially opened window
            # self.stylesheet = None # The contents of <?xml-stylesheet...?> line.
    
    #@+others
    #@+node:ekr.20181115092337.8: *4* bf.finishCreate
    def finishCreate(self):
        pass
        ### self.createFirstTreeNode()
            # Call the base LeoFrame method.
    #@+node:ekr.20181115092337.9: *4* bf.oops
    def oops(self):
        g = self.c
        g.trace("LeoBrowserFrame", g.callers(4))
    #@+node:ekr.20181115092337.10: *4* bf.redirectors (To do: add messages)
    def bringToFront(self):
        pass
    def cascade(self, event=None):
        pass
    def contractBodyPane(self, event=None):
        pass
    def contractLogPane(self, event=None):
        pass
    def contractOutlinePane(self, event=None):
        pass
    def contractPane(self, event=None):
        pass
    def deiconify(self):
        pass
    def destroySelf(self):
        pass
    def equalSizedPanes(self, event=None):
        pass
    def expandBodyPane(self, event=None):
        pass
    def expandLogPane(self, event=None):
        pass
    def expandOutlinePane(self, event=None):
        pass
    def expandPane(self, event=None):
        pass
    def fullyExpandBodyPane(self, event=None):
        pass
    def fullyExpandLogPane(self, event=None):
        pass
    def fullyExpandOutlinePane(self, event=None):
        pass
    def fullyExpandPane(self, event=None):
        pass
    def get_window_info(self):
        return 600, 500, 20, 20
    def hideBodyPane(self, event=None):
        pass
    def hideLogPane(self, event=None):
        pass
    def hideLogWindow(self, event=None):
        pass
    def hideOutlinePane(self, event=None):
        pass
    def hidePane(self, event=None):
        pass
    def leoHelp(self, event=None):
        pass
    def lift(self):
        pass
    def minimizeAll(self, event=None):
        pass
    def resizePanesToRatio(self, ratio, secondary_ratio):
        pass
    def resizeToScreen(self, event=None):
        pass
    def setInitialWindowGeometry(self):
        pass
    def setTopGeometry(self, w, h, x, y, adjustSize=True):
        return 0, 0, 0, 0
    def setWrap(self, flag, force=False):
        pass
    def toggleActivePane(self, event=None):
        pass
    def toggleSplitDirection(self, event=None):
        pass
    def update(self):
        pass
    #@+node:ekr.20181115115225.4: *4* LeoFrame.cmd (decorator)
    # def cmd(name):
        # '''Command decorator for the LeoFrame class.'''
        # # pylint: disable=no-self-argument
        # return g.new_cmd_decorator(name, ['c', 'frame',])
    #@+node:ekr.20181115172556.1: *4* LeoFrame.Must be defined in base class
    #@+node:ekr.20181115172556.2: *5* LeoFrame.initialRatios
    def initialRatios(self):
        c = self.c
        s = c.config.get("initial_split_orientation", "string")
        verticalFlag = s is None or (s != "h" and s != "horizontal")
        if verticalFlag:
            r = c.config.getRatio("initial-vertical-ratio")
            if r is None or r < 0.0 or r > 1.0: r = 0.5
            r2 = c.config.getRatio("initial-vertical-secondary-ratio")
            if r2 is None or r2 < 0.0 or r2 > 1.0: r2 = 0.8
        else:
            r = c.config.getRatio("initial-horizontal-ratio")
            if r is None or r < 0.0 or r > 1.0: r = 0.3
            r2 = c.config.getRatio("initial-horizontal-secondary-ratio")
            if r2 is None or r2 < 0.0 or r2 > 1.0: r2 = 0.8
        return verticalFlag, r, r2
    #@+node:ekr.20181115172556.3: *5* LeoFrame.longFileName & shortFileName
    def longFileName(self):
        return self.c.mFileName

    def shortFileName(self):
        g = self.c
        return g.shortFileName(self.c.mFileName)
    #@+node:ekr.20181115172556.5: *5* LeoFrame.promptForSave
    def promptForSave(self):
        '''
        Prompt the user to save changes.
        Return True if the user vetos the quit or save operation.
        '''
        c, g = self.c, self.g
        theType = "quitting?" if g.app.quitting else "closing?"
        # See if we are in quick edit/save mode.
        root = c.rootPosition()
        quick_save = not c.mFileName and not root.next() and root.isAtEditNode()
        if quick_save:
            name = g.shortFileName(root.atEditNodeName())
        else:
            name = c.mFileName if c.mFileName else self.title
        answer = g.app.gui.runAskYesNoCancelDialog(c,
            title="Confirm",
            message='Save changes to %s before %s' % (
                g.splitLongFileName(name), theType))
        if answer == "cancel":
            return True # Veto.
        if answer == "no":
            return False # Don't save and don't veto.
        if not c.mFileName:
            root = c.rootPosition()
            if not root.next() and root.isAtEditNode():
                # There is only a single @edit node in the outline.
                # A hack to allow "quick edit" of non-Leo files.
                # See https://bugs.launchpad.net/leo-editor/+bug/381527
                # Write the @edit node if needed.
                if root.isDirty():
                    c.atFileCommands.writeOneAtEditNode(root,
                        toString=False, force=True)
                return False # Don't save and don't veto.
            else:
                c.mFileName = g.app.gui.runSaveFileDialog(c,
                    initialfile='',
                    title="Save",
                    filetypes=[("Leo files", "*.leo")],
                    defaultextension=".leo")
                c.bringToFront()
        if c.mFileName:
            if g.app.gui.guiName() == 'curses':
                g.pr('Saving: %s' % c.mFileName)
            ok = c.fileCommands.save(c.mFileName)
            return not ok # New in 4.2: Veto if the save did not succeed.
        else:
            return True # Veto.
    #@+node:ekr.20181115172556.6: *5* LeoFrame.frame.scanForTabWidth
    def scanForTabWidth(self, p):
        '''Return the tab width in effect at p.'''
        c = self.c
        tab_width = c.getTabWidth(p)
        c.frame.setTabWidth(tab_width)
    #@+node:ekr.20181115172556.7: *5* LeoFrame.Icon area convenience methods
    def addIconButton(self, *args, **keys):
        if self.iconBar: return self.iconBar.add(*args, **keys)
        else: return None

    def addIconRow(self):
        if self.iconBar: return self.iconBar.addRow()

    def addIconWidget(self, w):
        pass
        ### if self.iconBar: return self.iconBar.addWidget(w)

    def clearIconBar(self):
        pass
        ### if self.iconBar: self.iconBar.clear()

    def createIconBar(self):
        return None
        ###
            # c = self.c
            # if not self.iconBar:
                # self.iconBar = self.iconBarClass(c, self.outerFrame)
            # return self.iconBar

    def getIconBar(self):
        return None
        ###
            # if not self.iconBar:
                # self.iconBar = self.iconBarClass(self.c, self.outerFrame)
            # return self.iconBar

    getIconBarObject = getIconBar

    def getNewIconFrame(self):
        return None
        ###
            # if not self.iconBar:
                # self.iconBar = self.iconBarClass(self.c, self.outerFrame)
            # return self.iconBar.getNewFrame()

    def hideIconBar(self):
        pass
        ### if self.iconBar: self.iconBar.hide()

    def showIconBar(self):
        pass
        ### if self.iconBar: self.iconBar.show()
    #@+node:ekr.20181115172556.8: *5* LeoFrame.Status line convenience methods
    def createStatusLine(self):
        pass
        ###
            # if not self.statusLine:
                # self.statusLine = self.statusLineClass(self.c, self.outerFrame)
            # return self.statusLine

    def clearStatusLine(self):
        self.statusLine.clear()
        ###if self.statusLine: self.statusLine.clear()

    def disableStatusLine(self, background=None):
        pass
        ### if self.statusLine: self.statusLine.disable(background)

    def enableStatusLine(self, background="white"):
        pass
        ### if self.statusLine: self.statusLine.enable(background)

    def getStatusLine(self):
        return self.statusLine

    getStatusObject = getStatusLine

    def putStatusLine(self, s, bg=None, fg=None):
        if self.statusLine: self.statusLine.put(s, bg, fg)

    def setFocusStatusLine(self):
        self.statusLine.setFocus()
        ### if self.statusLine: self.statusLine.setFocus()

    def statusLineIsEnabled(self):
        return True
        ###
            # if self.statusLine: return self.statusLine.isEnabled()
            # else: return False

    def updateStatusLine(self):
        self.statusLine.update()
        ### if self.statusLine: self.statusLine.update()
    #@+node:ekr.20181115172556.9: *5* LeoFrame.Cut/Copy/Paste
    #@+node:ekr.20181115172556.10: *6* LeoFrame.copyText
    ### @cmd('copy-text')
    def copyText(self, event=None):
        '''Copy the selected text from the widget to the clipboard.'''
        # f = self
        g = self.g
        w = event and event.widget
        # wname = c.widget_name(w)
        if not w or not g.isTextWrapper(w):
            return
        # Set the clipboard text.
        i, j = w.getSelectionRange()
        if i == j:
            ins = w.getInsertPoint()
            i, j = g.getLine(w.getAllText(), ins)
        # 2016/03/27: Fix a recent buglet.
        # Don't clear the clipboard if we hit ctrl-c by mistake.
        s = w.get(i,j)
        if s:
            g.app.gui.replaceClipboardWith(s)

    OnCopyFromMenu = copyText
    #@+node:ekr.20181115172556.11: *6* LeoFrame.cutText
    ### @cmd('cut-text')
    def cutText(self, event=None):
        '''Invoked from the mini-buffer and from shortcuts.'''
        c, g = self.c, self.g
        ### f = self
        w = event and event.widget
        if not w or not g.isTextWrapper(w):
            return
        name = c.widget_name(w)
        oldSel = w.getSelectionRange()
        oldText = w.getAllText()
        i, j = w.getSelectionRange()
        # Update the widget and set the clipboard text.
        s = w.get(i, j)
        if i != j:
            w.delete(i, j)
            w.see(i) # 2016/01/19: important
            g.app.gui.replaceClipboardWith(s)
        else:
            ins = w.getInsertPoint()
            i, j = g.getLine(oldText, ins)
            s = w.get(i,j)
            w.delete(i,j)
            w.see(i) # 2016/01/19: important
            g.app.gui.replaceClipboardWith(s)
        if name.startswith('body'):
            c.frame.body.onBodyChanged('Cut', oldSel=oldSel, oldText=oldText)
        elif name.startswith('head'):
            # The headline is not officially changed yet.
            # p.initHeadString(s)
            s = w.getAllText()
            # 2011/11/14: Not used at present.
            # width = f.tree.headWidth(p=None,s=s)
            # w.setWidth(width)
        else: pass

    OnCutFromMenu = cutText
    #@+node:ekr.20181115172556.12: *6* LeoFrame.pasteText
    ### @cmd('paste-text')
    def pasteText(self, event=None, middleButton=False):
        '''
        Paste the clipboard into a widget.
        If middleButton is True, support x-windows middle-mouse-button easter-egg.
        '''
        c, g = self.c, self.g
        w = event and event.widget
        wname = c.widget_name(w)
        if not w or not g.isTextWrapper(w):
            return
        if self.cursorStay and wname.startswith('body'):
            tCurPosition = w.getInsertPoint()
        i, j = oldSel = w.getSelectionRange()
            # Returns insert point if no selection.
        oldText = w.getAllText()
        if middleButton and c.k.previousSelection is not None:
            start, end = c.k.previousSelection
            s = w.getAllText()
            s = s[start: end]
            c.k.previousSelection = None
        else:
            s = g.app.gui.getTextFromClipboard()
        s = g.toUnicode(s)
        singleLine = wname.startswith('head') or wname.startswith('minibuffer')
        if singleLine:
            # Strip trailing newlines so the truncation doesn't cause confusion.
            while s and s[-1] in ('\n', '\r'):
                s = s[: -1]
        # Save the horizontal scroll position.
        if hasattr(w, 'getXScrollPosition'):
            x_pos = w.getXScrollPosition()
        # Update the widget.
        if i != j:
            w.delete(i, j)
        w.insert(i, s)
        w.see(i + len(s) + 2)
        if wname.startswith('body'):
            if self.cursorStay:
                if tCurPosition == j:
                    offset = len(s)-(j-i)
                else:
                    offset = 0
                newCurPosition = tCurPosition + offset
                w.setSelectionRange(i=newCurPosition, j=newCurPosition)
            c.frame.body.onBodyChanged('Paste', oldSel=oldSel, oldText=oldText)
        elif singleLine:
            s = w.getAllText()
            while s and s[-1] in ('\n', '\r'):
                s = s[: -1]
            # 2011/11/14: headline width methods do nothing at present.
            # if wname.startswith('head'):
                # The headline is not officially changed yet.
                # p.initHeadString(s)
                # width = f.tree.headWidth(p=None,s=s)
                # w.setWidth(width)
        else:
            pass
        # Never scroll horizontally.
        if hasattr(w, 'getXScrollPosition'):
            w.setXScrollPosition(x_pos)

    OnPasteFromMenu = pasteText
    #@+node:ekr.20181115172556.13: *6* LeoFrame.OnPaste (support middle-button paste)
    def OnPaste(self, event=None):
        return self.pasteText(event=event, middleButton=True)
    #@+node:ekr.20181115172556.14: *5* LeoFrame.Edit Menu
    #@+node:ekr.20181115172556.15: *6* LeoFrame.abortEditLabelCommand
    ### @cmd('abort-edit-headline')
    def abortEditLabelCommand(self, event=None):
        '''End editing of a headline and revert to its previous value.'''
        c, g = self.c, self.g
        tree = self.tree
        p = c.p
        if g.app.batchMode:
            c.notValidInBatchMode("Abort Edit Headline")
            return
        # Revert the headline text.
        # Calling c.setHeadString is required.
        # Otherwise c.redraw would undo the change!
        c.setHeadString(p, tree.revertHeadline)
        c.redraw(p)
    #@+node:ekr.20181115172556.16: *6* LeoFrame.endEditLabelCommand
    ### @cmd('end-edit-headline')
    def endEditLabelCommand(self, event=None, p=None):
        '''End editing of a headline and move focus to the body pane.'''
        c, g = self.c, self.g
        ### frame = self
        k = c.k
        if g.app.batchMode:
            c.notValidInBatchMode("End Edit Headline")
        else:
            w = c.get_focus()
            w_name = g.app.gui.widget_name(w)
            if w_name.startswith('head'):
                c.endEditing()
                c.treeWantsFocus()
            else:
                # c.endEditing()
                c.bodyWantsFocus()
                k.setDefaultInputState()
                # Recolor the *body* text, **not** the headline.
                k.showStateAndMode(w=c.frame.body.wrapper)
    #@+node:ekr.20181115173057.1: *4* LeoFrame.May be defined in subclasses
    #@+node:ekr.20181115173057.2: *5* LeoFrame.event handlers
    def OnBodyClick(self, event=None):
        pass

    def OnBodyRClick(self, event=None):
        pass
    #@+node:ekr.20181115173057.3: *5* LeoFrame.getTitle & setTitle
    def getTitle(self):
        return self.title

    def setTitle(self, title):
        self.title = title
    #@+node:ekr.20181115173057.4: *5* LeoFrame.initAfterLoad  & initCompleteHint
    def initAfterLoad(self):
        '''Provide offical hooks for late inits of components of Leo frames.'''
        ###
            # frame = self
            # frame.body.initAfterLoad()
            # frame.log.initAfterLoad()
            # frame.menu.initAfterLoad()
            # # if frame.miniBufferWidget: frame.miniBufferWidget.initAfterLoad()
            # frame.tree.initAfterLoad()

    def initCompleteHint(self):
        pass
    #@+node:ekr.20181115173057.5: *5* LeoFrame.setTabWidth
    def setTabWidth(self, w):
        '''Set the tab width in effect for this frame.'''
        # Subclasses may override this to affect drawing.
        self.tab_width = w
    #@-others
#@+node:ekr.20181113041113.1: *3* class LeoBrowserGui
class LeoBrowserGui(flx.PyComponent):
    '''Leo's Browser Gui.'''
    
    def init (self, c, g):
        '''The ctor for the LeoBroswerGui class.'''
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        self.mGuiName = 'BrowserGui'
        self.clipboardContents = ''
        self.isNullGui = True
        self.last_frame = LeoBrowserFrame(c, g)
        ###
            # From LeoGui.
            # self.FKeys = [] # The representation of F-keys.
            # self.ScriptingControllerClass = NullScriptingControllerClass
            # self.globalFindDialog = None
            # self.globalFindTab = None
            # self.globalFindTabManager = None
            # self.ignoreChars = [] # Keys that are always to be ignore.
            # self.leoIcon = None
            # self.mainLoop = None
            # self.root = None
            # self.specialChars = [] # A list of characters/keys to be handle specially.
            # self.splashScreen = None
            # self.utils = None
            #
            # From NullGui...
            # self.focusWidget = None
            # self.idleTimeClass = g.NullObject
            # self.script = None

    #@+others
    #@+node:ekr.20181115044516.1: *4* Overrides (to do)
    #@+node:ekr.20181115042835.4: *5* gui.create_key_event
    def create_key_event(self, c,
        binding=None,
        char=None,
        event=None,
        w=None,
        x=None, x_root=None,
        y=None, y_root=None,
    ):
        # Do not call strokeFromSetting here!
        # For example, this would wrongly convert Ctrl-C to Ctrl-c,
        # in effect, converting a user binding from Ctrl-Shift-C to Ctrl-C.
        g = self.g
        g.trace(g.callers())
        return leoGui.LeoKeyEvent(c, char, event, binding, w, x, y, x_root, y_root)
    #@+node:ekr.20181115042835.7: *5* gui.event_generate (Needed?)
    def event_generate(self, c, char, shortcut, w):
        print('gui.event_generated', self.g.callers())
        event = self.create_key_event(c, binding=shortcut, char=char, w=w)
        c.k.masterKeyHandler(event)
        c.outerUpdate()
    #@+node:ekr.20181115042835.5: *5* gui.guiName
    def guiName(self):
        
        return self.mGuiName
    #@+node:ekr.20181115042930.6: *5* gui.isTextWidget & isTextWrapper
    def isTextWidget(self, w):
        return True # Must be True for unit tests.

    def isTextWrapper(self, w):
        '''Return True if w is a Text widget suitable for text-oriented commands.'''
        return w and getattr(w, 'supportsHighLevelInterface', None)
    #@+node:ekr.20181115042753.1: *5* gui.oops
    def oops(self):
        print("LeoBrowserGui.oops", self.g.callers(4))
    #@+node:ekr.20181115042930.9: *5* gui.runMainLoop
    def runMainLoop(self):
        """Run the null gui's main loop."""
        print('gui.runMainLoop: not ready yet.')
        ###
            # g = self.g
            # if self.script:
                # frame = self.lastFrame
                # g.app.log = frame.log
                # self.lastFrame.c.executeScript(script=self.script)
            # else:
                # print('**** NullGui.runMainLoop: terminating Leo.')
            # # Getting here will terminate Leo.
    #@+node:ekr.20181115042835.28: *5* gui.widget_name (To do)
    def widget_name(self, w):
        # First try the widget's getName method.
        if not 'w':
            return '<no widget>'
        elif hasattr(w, 'getName'):
            return w.getName()
        elif hasattr(w, '_name'):
            return w._name
        else:
            return repr(w)
    #@+node:ekr.20181115042908.1: *4* From NullGui
    #@+node:ekr.20181115042930.3: *5* NullGui.dialogs
    def runAboutLeoDialog(self, c, version, theCopyright, url, email):
        return self.simulateDialog("aboutLeoDialog", None)

    def runAskLeoIDDialog(self):
        return self.simulateDialog("leoIDDialog", None)

    def runAskOkDialog(self, c, title, message=None, text="Ok"):
        return self.simulateDialog("okDialog", "Ok")

    def runAskOkCancelNumberDialog(self, c, title, message,
        cancelButtonText=None,
        okButtonText=None,
    ):
        return self.simulateDialog("numberDialog", -1)

    def runAskOkCancelStringDialog(self, c, title, message,
        cancelButtonText=None,
        okButtonText=None,
        default="",
        wide=False,
    ):
        return self.simulateDialog("stringDialog", '')

    def runCompareDialog(self, c):
        return self.simulateDialog("compareDialog", '')

    def runOpenFileDialog(self, c, title, filetypes, defaultextension,
        multiple=False,
        startpath=None,
    ):
        return self.simulateDialog("openFileDialog", None)

    def runSaveFileDialog(self, c, initialfile, title, filetypes, defaultextension):
        return self.simulateDialog("saveFileDialog", None)

    def runAskYesNoDialog(self, c, title,
        message=None,
        yes_all=False,
        no_all=False,
    ):
        return self.simulateDialog("yesNoDialog", "no")

    def runAskYesNoCancelDialog(self, c, title,
        message=None,
        yesMessage="Yes",
        noMessage="No",
        yesToAllMessage=None,
        defaultButton="Yes",
        cancelMessage=None,
    ):
        return self.simulateDialog("yesNoCancelDialog", "cancel")

    def simulateDialog(self, key, defaultVal):
        return defaultVal
    #@+node:ekr.20181115042930.4: *5* NullGui.clipboard & focus
    def get_focus(self, *args, **kwargs):
        return self.focusWidget

    def getTextFromClipboard(self):
        return self.clipboardContents

    def replaceClipboardWith(self, s):
        self.clipboardContents = s

    def set_focus(self, commander, widget):
        self.focusWidget = widget
    #@+node:ekr.20181115042930.5: *5* NullGui.do nothings
    def alert(self, message):
        pass
    def attachLeoIcon(self, window):
        pass
    def destroySelf(self):
        pass
    def finishCreate(self): 
        pass
    def getFontFromParams(self, family, size, slant, weight, defaultSize=12):
        return self.g.app.config.defaultFont
    def getIconImage(self, name):
        return None
    def getImageImage(self, name):
        return None
    def getTreeImage(self, c, path):
        return None
    def get_window_info(self, window):
        return 600, 500, 20, 20
    def onActivateEvent(self, *args, **keys): 
        pass
    def onDeactivateEvent(self, *args, **keys): 
        pass
    #@+node:ekr.20181115042930.8: *5* NullGui.panels
    def createComparePanel(self, c):
        """Create Compare panel."""
        self.oops()

    def createFindTab(self, c, parentFrame):
        """Create a find tab in the indicated frame."""
        pass # Now always done during startup.

    def createLeoFrame(self, c, title):
        """Create a null Leo Frame."""
        self.oops()
        ###
            # gui = self
            # self.lastFrame = leoFrame.NullFrame(c, title, gui)
            # return self.lastFrame
    #@+node:ekr.20181115042828.1: *4* From LeoGui
    def setScript(self, script=None, scriptFileName=None):
        pass
        ###
            # self.script = script
            # self.scriptFileName = scriptFileName

    def dismiss_splash_screen(self):
        pass

    def ensure_commander_visible(self, c):
        """E.g. if commanders are in tabs, make sure c's tab is visible"""
        pass

    def postPopupMenu(self, *args, **keys):
        pass
        
    def put_help(self, c, s, short_title):
        pass
    #@-others
#@+node:ekr.20181115092337.21: *3* class LeoBrowserIconBar
class LeoBrowserIconBar(flx.PyComponent):

    def init(self, c, g):
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        self.w = g.NullObject()
        ###
            # self.iconFrame = None
            # self.parentFrame = parentFrame
            
    #@+others
    #@+node:ekr.20181115114726.3: *4*  NullIconBarClass.Do nothing
    def addRow(self, height=None):
        pass

    def addRowIfNeeded(self):
        pass

    def addWidget(self, w):
        pass

    def createChaptersIcon(self):
        pass

    def deleteButton(self, w):
        pass

    def getNewFrame(self): return None

    def hide(self):
        pass

    def show(self): pass
    #@+node:ekr.20181115114726.4: *4* NullIconBarClass.add
    def add(self, *args, **keys):
        '''Add a (virtual) button to the (virtual) icon bar.'''
        pass ###
        ###
            # command = keys.get('command')
            # text = keys.get('text')
            # try:
                # g.app.iconWidgetCount += 1
            # except Exception:
                # g.app.iconWidgetCount = 1
            # n = g.app.iconWidgetCount
            # name = 'nullButtonWidget %d' % n
            # if not command:
        
                # def commandCallback(name=name):
                    # g.pr("command for %s" % (name))
        
                # command = commandCallback
        
            # class nullButtonWidget:
        
                # def __init__(self, c, command, name, text):
                    # self.c = c
                    # self.command = command
                    # self.name = name
                    # self.text = text
        
                # def __repr__(self):
                    # return self.name
        
            # b = nullButtonWidget(self.c, command, name, text)
            # return b
    #@+node:ekr.20181115114726.5: *4* NullIconBarClass.clear
    def clear(self):
        pass
        ### g.app.iconWidgetCount = 0
        ### g.app.iconImageRefs = []
    #@+node:ekr.20181115114726.6: *4* NullIconBarClass.setCommandForButton
    def setCommandForButton(self, button, command, command_p, controller, gnx, script):
        pass ###
        ### button.command = command
    #@-others
#@+node:ekr.20181115092337.22: *3* class LeoBrowserLog
class LeoBrowserLog(flx.PyComponent):
    
    def init(self, c, g):
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        self.isNull = False
        self.logNumber = 0
        self.widget = None ### self.createControl(parentFrame)
    ###
        # self.enabled = True

    #@+others
    #@+node:ekr.20181115092337.23: *4*  bl.not used
    #@+node:ekr.20181115092337.24: *5* bl.createControl
    def createControl(self, parentFrame):
        return self.createTextWidget() ### parentFrame)
    #@+node:ekr.20181115092337.25: *5* bl.finishCreate
    def finishCreate(self):
        pass
    #@+node:ekr.20181115092337.26: *5* bl.isLogWidget
    def isLogWidget(self, w):
        return False
    #@+node:ekr.20181115092337.27: *5* bl.tabs
    def clearTab(self, tabName, wrap='none'):
        pass

    def createCanvas(self, tabName):
        pass

    def createTab(self, tabName, createText=True, widget=None, wrap='none'):
        pass

    def deleteTab(self, tabName, force=False): pass

    def getSelectedTab(self): return None

    def lowerTab(self, tabName): pass

    def raiseTab(self, tabName): pass

    def renameTab(self, oldName, newName): pass

    def selectTab(self, tabName, createText=True, widget=None, wrap='none'): pass
    #@+node:ekr.20181115092337.28: *4* bl.createTextWidget
    def createTextWidget(self): ### , parentFrame):
        self.logNumber += 1
        c, g = self.c, self.g
        name="log-%d" % self.logNumber
        log = StringTextWrapper(c, g, name)
        return log
    #@+node:ekr.20181115092337.29: *4* bl.oops
    def oops(self):
        g = self.g
        g.trace("LeoBrowserLog:", g.callers(4))
    #@+node:ekr.20181115092337.30: *4* bl.put and putnl
    def put(self, s,
        color=None,
        tabName='Log',
        from_redirect=False,
        nodeLink=None,
    ):
        print(s) ###
        ##self.message('put', s=s, tabName=tabName)

    def putnl(self, tabName='Log'):
        print('') ###
        ### self.message('put-nl', tabName=tabName)
    #@-others
#@+node:ekr.20181115092337.31: *3* class LeoBrowserMenu
class LeoBrowserMenu(flx.PyComponent):
    
    def init(self, c, g):
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        self.isNull = True ### ???
        self.menus = {} # Menu dictionary.
        #
        ### From LeoMenu
            # self.enable_dict = {} # Created by finishCreate.
            # self.frame = frame
            # self.menuShortcuts = {}
            
    def finishCreate(self):
        pass 
        ### self.define_enable_dict()

    #@+others
    #@+node:ekr.20181115113707.4: *4* LeoMenu.error & oops
    def error(self, s):
        self.g.error('', s)
        
    def oops(self):
        g = self.g
        print('LeoMenu.oops', g.callers())
    #@+node:ekr.20181115113707.5: *4* LeoMenu.Gui-independent menu routines
    #@+node:ekr.20181115113707.6: *5* LeoMenu.capitalizeMinibufferMenuName
    #@@nobeautify

    def capitalizeMinibufferMenuName(self, s, removeHyphens):
        result = []
        for i, ch in enumerate(s):
            prev =     s[i - 1] if i > 0 else ''
            prevprev = s[i - 2] if i > 1 else ''
            if (
                i == 0 or
                i == 1 and prev == '&' or
                prev == '-' or
                prev == '&' and prevprev == '-'
            ):
                result.append(ch.capitalize())
            elif removeHyphens and ch == '-':
                result.append(' ')
            else:
                result.append(ch)
        return ''.join(result)
    #@+node:ekr.20181115113707.7: *5* LeoMenu.createMenusFromTables & helpers
    def createMenusFromTables(self):
        '''(leoMenu) Usually over-ridden.'''
        c, g = self.c, self.g
        aList = c.config.getMenusList()
        if aList:
            self.createMenusFromConfigList(aList)
        else:
            g.es_print('No @menu setting found')
    #@+node:ekr.20181115113707.8: *6* LeoMenu.createMenusFromConfigList & helpers
    def createMenusFromConfigList(self, aList):
        '''
        Create menus from aList.
        The 'top' menu has already been created.
        '''
        # Called from createMenuBar.
        c, g = self.c, self.g
        for z in aList:
            kind, val, val2 = z
            if kind.startswith('@menu'):
                name = kind[len('@menu'):].strip()
                if not self.handleSpecialMenus(name, parentName=None):
                    # Fix #528: Don't create duplicate menu items.
                    menu = self.createNewMenu(name)
                        # Create top-level menu.
                    if menu:
                        self.createMenuFromConfigList(name, val, level=0)
                    else:
                        g.trace('no menu', name)
            else:
                self.error('%s %s not valid outside @menu tree' % (kind, val))
        aList = c.config.getOpenWith()
        if aList:
            # a list of dicts.
            self.createOpenWithMenuFromTable(aList)
    #@+node:ekr.20181115113707.9: *7* LeoMenu.createMenuFromConfigList
    def createMenuFromConfigList(self, parentName, aList, level=0):
        """Build menu based on nested list

        List entries are either:

            ['@item', 'command-name', 'optional-view-name']

        or:

            ['@menu Submenu name', <nested list>, None]

        :param str parentName: name of menu under which to place this one
        :param list aList: list of entries as described above
        """
        g = self.g
        parentMenu = self.getMenu(parentName)
        table = []
        for z in aList:
            kind, val, val2 = z
            if kind.startswith('@menu'):
                # Menu names can be unicode without any problem.
                name = kind[5:].strip()
                if table:
                    self.createMenuEntries(parentMenu, table)
                if not self.handleSpecialMenus(name, parentName,
                    alt_name=val2, #848.
                    table=table,
                ):
                    menu = self.createNewMenu(name, parentName)
                        # Create submenu of parent menu.
                    if menu:
                        # Partial fix for #528.
                        self.createMenuFromConfigList(name, val, level + 1)
                table = []
            elif kind == '@item':
                name = str(val) # Item names must always be ascii.
                if val2:
                    # Translated names can be unicode.
                    table.append((val2, name),)
                else:
                    table.append(name)
            else:
                g.trace('can not happen: bad kind:', kind)
        if table:
            self.createMenuEntries(parentMenu, table)
    #@+node:ekr.20181115113707.10: *7* LeoMenu.handleSpecialMenus
    def handleSpecialMenus(self, name, parentName, alt_name=None, table=None):
        '''
        Handle a special menu if name is the name of a special menu.
        return True if this method handles the menu.
        '''
        c, g = self.c, self.g
        if table is None: table = []
        name2 = name.replace('&', '').replace(' ', '').lower()
        if name2 == 'plugins':
            # Create the plugins menu using a hook.
            g.doHook("create-optional-menus", c=c)
            return True
        elif name2.startswith('recentfiles'):
            # Just create the menu.
            # createRecentFilesMenuItems will create the contents later.
            g.app.recentFilesManager.recentFilesMenuName = alt_name or name
                #848
            self.createNewMenu(alt_name or name, parentName)
            return True
        elif name2 == 'help' and g.isMac:
            helpMenu = self.getMacHelpMenu(table)
            return helpMenu is not None
        else:
            return False
    #@+node:ekr.20181115113707.11: *5* LeoMenu.hasSelection
    # Returns True if text in the outline or body text is selected.

    def hasSelection(self):
        c = self.c; w = c.frame.body.wrapper
        if c.frame.body:
            first, last = w.getSelectionRange()
            return first != last
        else:
            return False
    #@+node:ekr.20181115113707.12: *4* LeoMenu.Helpers
    #@+node:ekr.20181115113707.13: *5* LeoMenu.canonicalizeMenuName & cononicalizeTranslatedMenuName
    def canonicalizeMenuName(self, name):
        return ''.join([ch for ch in name.lower() if ch.isalnum()])

    def canonicalizeTranslatedMenuName(self, name):
        return ''.join([ch for ch in name.lower() if ch not in '& \t\n\r'])
    #@+node:ekr.20181115113707.14: *5* LeoMenu.computeOldStyleShortcutKey
    def computeOldStyleShortcutKey(self, s):
        '''Compute the old-style shortcut key for @shortcuts entries.'''
        return ''.join([ch for ch in s.strip().lower() if ch.isalnum()])
    #@+node:ekr.20181115113707.15: *5* LeoMenu.createMenuEntries & helpers
    def createMenuEntries(self, menu, table, dynamicMenu=False):
        '''Create a menu entry from the table.
        New in 4.4: this method shows the shortcut in the menu,
        but this method **never** binds any shortcuts.'''
        c, g = self.c, self.g
        if g.app.unitTesting: return
        if not menu: return
        self.traceMenuTable(table)
        for data in table:
            label, command, done = self.getMenuEntryInfo(data, menu)
            if done: continue
            commandName = self.getMenuEntryBindings(command, dynamicMenu, label)
            if not commandName: continue
            masterMenuCallback = self.createMasterMenuCallback(
                dynamicMenu, command, commandName)
            realLabel = self.getRealMenuName(label)
            amp_index = realLabel.find("&")
            realLabel = realLabel.replace("&", "")
            # c.add_command ensures that c.outerUpdate is called.
            c.add_command(menu, label=realLabel,
                accelerator='', # The accelerator is now computed dynamically.
                command=masterMenuCallback,
                commandName=commandName,
                underline=amp_index)
    #@+node:ekr.20181115113707.16: *6* LeoMenu.createMasterMenuCallback
    def createMasterMenuCallback(self, dynamicMenu, command, commandName):

        c, g = self.c, self.g

        def setWidget():
            w = c.frame.getFocus()
            if w and g.isMac:
                 # 2012/01/11: redirect (MacOS only).
                wname = c.widget_name(w)
                if wname.startswith('head'):
                    w = c.frame.tree.edit_widget(c.p)
            # 2015/05/14: return a wrapper if possible.
            if not g.isTextWrapper(w):
                w = getattr(w, 'wrapper', w)
            return w

        if dynamicMenu:
            if command:

                def masterDynamicMenuCallback(c=c, command=command):
                    # 2012/01/07: set w here.
                    w = setWidget()
                    event = g.app.gui.create_key_event(c, w=w)
                    return c.k.masterCommand(func=command, event=event)

                return masterDynamicMenuCallback
            else:
                g.internalError('no callback for dynamic menu item.')

                def dummyMasterMenuCallback():
                    pass

                return dummyMasterMenuCallback
        else:

            def masterStaticMenuCallback(c=c, commandName=commandName):
                # 2011/10/28: Use only the command name to dispatch the command.
                # 2012/01/07: Bug fix: set w here.
                w = setWidget()
                event = g.app.gui.create_key_event(c, w=w)
                return c.k.masterCommand(commandName=commandName, event=event)

            return masterStaticMenuCallback
    #@+node:ekr.20181115113707.17: *6* LeoMenu.getMenuEntryBindings
    def getMenuEntryBindings(self, command, dynamicMenu, label):
        '''Compute commandName from command.'''
        c, g = self.c, self.g
        if g.isString(command):
            # Command is really a command name.
            commandName = command
        else:
            # First, get the old-style name.
            commandName = self.computeOldStyleShortcutKey(label)
        command = c.commandsDict.get(commandName)
        return commandName
    #@+node:ekr.20181115113707.18: *6* LeoMenu.getMenuEntryInfo
    def getMenuEntryInfo(self, data, menu):
        g = self.g
        done = False
        if g.isString(data):
            # A single string is both the label and the command.
            s = data
            removeHyphens = s and s[0] == '*'
            if removeHyphens: s = s[1:]
            label = self.capitalizeMinibufferMenuName(s, removeHyphens)
            command = s.replace('&', '').lower()
            if label == '-':
                self.add_separator(menu)
                done = True # That's all.
        else:
            ok = isinstance(data, (list, tuple)) and len(data) in (2, 3)
            if ok:
                if len(data) == 2:
                    # Command can be a minibuffer-command name.
                    label, command = data
                else:
                    # Ignore shortcuts bound in menu tables.
                    label, junk, command = data
                if label in (None, '-'):
                    self.add_separator(menu)
                    done = True # That's all.
            else:
                g.trace('bad data in menu table: %s' % repr(data))
                done = True # Ignore bad data
        return label, command, done
    #@+node:ekr.20181115113707.19: *6* LeoMenu.traceMenuTable
    def traceMenuTable(self, table):

        g = self.g
        trace = False and not g.unitTesting
        if not trace: return
        format = '%40s %s'
        g.trace('*' * 40)
        for data in table:
            if isinstance(data, (list, tuple)):
                n = len(data)
                if n == 2:
                    print(format % (data[0], data[1]))
                elif n == 3:
                    name, junk, func = data
                    print(format % (name, func and func.__name__ or '<NO FUNC>'))
            else:
                print(format % (data, ''))
    #@+node:ekr.20181115113707.20: *5* LeoMenu.createMenuItemsFromTable
    def createMenuItemsFromTable(self, menuName, table, dynamicMenu=False):
        g = self.g
        if g.app.gui.isNullGui:
            return
        try:
            menu = self.getMenu(menuName)
            if menu is None:
                return
            self.createMenuEntries(menu, table, dynamicMenu=dynamicMenu)
        except Exception:
            g.es_print("exception creating items for", menuName, "menu")
            g.es_exception()
        g.app.menuWarningsGiven = True
    #@+node:ekr.20181115113707.21: *5* LeoMenu.createNewMenu
    def createNewMenu(self, menuName, parentName="top", before=None):
        g = self.g
        try:
            parent = self.getMenu(parentName) # parent may be None.
            menu = self.getMenu(menuName)
            if menu:
                # Not an error.
                # g.error("menu already exists:", menuName)
                return None # Fix #528.
            else:
                menu = self.new_menu(parent, tearoff=0, label=menuName)
                self.setMenu(menuName, menu)
                label = self.getRealMenuName(menuName)
                amp_index = label.find("&")
                label = label.replace("&", "")
                if before: # Insert the menu before the "before" menu.
                    index_label = self.getRealMenuName(before)
                    amp_index = index_label.find("&")
                    index_label = index_label.replace("&", "")
                    index = parent.index(index_label)
                    self.insert_cascade(parent, index=index, label=label, menu=menu, underline=amp_index)
                else:
                    self.add_cascade(parent, label=label, menu=menu, underline=amp_index)
                return menu
        except Exception:
            g.es("exception creating", menuName, "menu")
            g.es_exception()
            return None
    #@+node:ekr.20181115113707.22: *5* LeoMenu.createOpenWithMenuFromTable & helpers
    def createOpenWithMenuFromTable(self, table):
        '''
        Table is a list of dictionaries, created from @openwith settings nodes.

        This menu code uses these keys:

            'name':     menu label.
            'shortcut': optional menu shortcut.

        efc.open_temp_file uses these keys:

            'args':     the command-line arguments to be used to open the file.
            'ext':      the file extension.
            'kind':     the method used to open the file, such as subprocess.Popen.
        '''
        g, k = self.g, self.c.k
        if not table: return
        g.app.openWithTable = table # Override any previous table.
        # Delete the previous entry.
        parent = self.getMenu("File")
        if not parent:
            if not g.app.batchMode:
                g.error('', 'createOpenWithMenuFromTable:', 'no File menu')
            return
        label = self.getRealMenuName("Open &With...")
        amp_index = label.find("&")
        label = label.replace("&", "")
        try:
            index = parent.index(label)
            parent.delete(index)
        except Exception:
            try:
                index = parent.index("Open With...")
                parent.delete(index)
            except Exception:
                g.trace('unexpected exception')
                g.es_exception()
                return
        # Create the Open With menu.
        openWithMenu = self.createOpenWithMenu(parent, label, index, amp_index)
        if not openWithMenu:
            g.trace('openWithMenu returns None')
            return
        self.setMenu("Open With...", openWithMenu)
        # Create the menu items in of the Open With menu.
        self.createOpenWithMenuItemsFromTable(openWithMenu, table)
        for d in table:
            k.bindOpenWith(d)
    #@+node:ekr.20181115113707.23: *6* LeoMenu.createOpenWithMenuItemsFromTable & callback
    def createOpenWithMenuItemsFromTable(self, menu, table):
        '''
        Create an entry in the Open with Menu from the table, a list of dictionaries.

        Each dictionary d has the following keys:

        'args':     the command-line arguments used to open the file.
        'ext':      not used here: used by efc.open_temp_file.
        'kind':     not used here: used by efc.open_temp_file.
        'name':     menu label.
        'shortcut': optional menu shortcut.
        '''
        c, g = self.c, self.g
        if g.app.unitTesting: return
        for d in table:
            label = d.get('name')
            args = d.get('args', [])
            accel = d.get('shortcut') or ''
            if label and args:
                realLabel = self.getRealMenuName(label)
                underline = realLabel.find("&")
                realLabel = realLabel.replace("&", "")
                callback = self.defineOpenWithMenuCallback(d)
                c.add_command(menu,
                    label=realLabel,
                    accelerator=accel,
                    command=callback,
                    underline=underline)
    #@+node:ekr.20181115113707.24: *7* LeoMenu.defineOpenWithMenuCallback
    def defineOpenWithMenuCallback(self, d):
        # The first parameter must be event, and it must default to None.

        def openWithMenuCallback(event=None, self=self, d=d):
            return self.c.openWith(d=d)

        return openWithMenuCallback
    #@+node:ekr.20181115113707.25: *5* LeoMenu.deleteRecentFilesMenuItems
    def deleteRecentFilesMenuItems(self, menu):
        """Delete recent file menu entries"""
        g = self.g
        rf = g.app.recentFilesManager
        # Why not just delete all the entries?
        recentFiles = rf.getRecentFiles()
        toDrop = len(recentFiles) + len(rf.getRecentFilesTable())
        self.delete_range(menu, 0, toDrop)
        for i in rf.groupedMenus:
            menu = self.getMenu(i)
            if menu:
                self.destroy(menu)
                self.destroyMenu(i)
    #@+node:ekr.20181115113707.26: *5* LeoMenu.defineMenuCallback
    def defineMenuCallback(self, command, name, minibufferCommand):
        c, g = self.c, self.g
        if minibufferCommand:
            # Create a dummy event as a signal to doCommand.
            event = g.app.gui.create_key_event(c)
            # The first parameter must be event, and it must default to None.

            def minibufferMenuCallback(event=event, self=self, command=command, label=name):
                c = self.c
                return c.doCommand(command, label, event)

            return minibufferMenuCallback
        else:
            # The first parameter must be event, and it must default to None.

            def legacyMenuCallback(event=None, self=self, command=command, label=name):
                c = self.c # 2012/03/04.
                c.check_event(event)
                return c.doCommand(command, label)

            return legacyMenuCallback
    #@+node:ekr.20181115113707.27: *5* LeoMenu.deleteMenu
    def deleteMenu(self, menuName):
        g = self.g
        try:
            menu = self.getMenu(menuName)
            if menu:
                self.destroy(menu)
                self.destroyMenu(menuName)
            else:
                g.es("can't delete menu:", menuName)
        except Exception:
            g.es("exception deleting", menuName, "menu")
            g.es_exception()
    #@+node:ekr.20181115113707.28: *5* LeoMenu.deleteMenuItem
    def deleteMenuItem(self, itemName, menuName="top"):
        """Delete itemName from the menu whose name is menuName."""
        g = self.g
        try:
            menu = self.getMenu(menuName)
            if menu:
                realItemName = self.getRealMenuName(itemName)
                self.delete(menu, realItemName)
            else:
                g.es("menu not found:", menuName)
        except Exception:
            g.es("exception deleting", itemName, "from", menuName, "menu")
            g.es_exception()
    #@+node:ekr.20181115113707.29: *5* LeoMenu.get/setRealMenuName & setRealMenuNamesFromTable
    # Returns the translation of a menu name or an item name.

    def getRealMenuName(self, menuName):
        g = self.g
        cmn = self.canonicalizeTranslatedMenuName(menuName)
        return g.app.realMenuNameDict.get(cmn, menuName)

    def setRealMenuName(self, untrans, trans):
        g = self.g
        cmn = self.canonicalizeTranslatedMenuName(untrans)
        g.app.realMenuNameDict[cmn] = trans

    def setRealMenuNamesFromTable(self, table):
        g = self.g
        try:
            for untrans, trans in table:
                self.setRealMenuName(untrans, trans)
        except Exception:
            g.es("exception in", "setRealMenuNamesFromTable")
            g.es_exception()
    #@+node:ekr.20181115113707.30: *5* LeoMenu.getMenu, setMenu, destroyMenu
    def getMenu(self, menuName):
        cmn = self.canonicalizeMenuName(menuName)
        return self.menus.get(cmn)

    def setMenu(self, menuName, menu):
        cmn = self.canonicalizeMenuName(menuName)
        self.menus[cmn] = menu

    def destroyMenu(self, menuName):
        cmn = self.canonicalizeMenuName(menuName)
        del self.menus[cmn]
    #@+node:ekr.20181115113707.31: *4* LeoMenu.Must be overridden in menu subclasses
    #@+node:ekr.20181115113707.32: *5* LeoMenu.9 Routines with Tk spellings
    def add_cascade(self, parent, label, menu, underline):
        self.oops()

    def add_command(self, menu, **keys):
        self.oops()

    def add_separator(self, menu):
        self.oops()
    # def bind (self,bind_shortcut,callback):
    #     self.oops()

    def delete(self, menu, realItemName):
        self.oops()

    def delete_range(self, menu, n1, n2):
        self.oops()

    def destroy(self, menu):
        self.oops()

    def insert(self, menuName, position, label, command, underline=None): # New in Leo 4.4.3 a1
        self.oops()

    def insert_cascade(self, parent, index, label, menu, underline):
        self.oops()

    def new_menu(self, parent, tearoff=0, label=''): # 2010: added label arg for pylint.
        self.oops(); return None
    #@+node:ekr.20181115113707.33: *5* LeoMenu.9 Routines with new spellings
    def activateMenu(self, menuName): # New in Leo 4.4b2.
        self.oops()

    def clearAccel(self, menu, name):
        self.oops()

    def createMenuBar(self, frame):
        self.oops()

    def createOpenWithMenu(self, parent, label, index, amp_index):
        self.oops(); return None

    def disableMenu(self, menu, name):
        self.oops()

    def enableMenu(self, menu, name, val):
        self.oops()

    def getMacHelpMenu(self, table):
        return None

    def getMenuLabel(self, menu, name):
        self.oops()

    def setMenuLabel(self, menu, name, label, underline=-1):
        self.oops()
    #@-others
#@+node:ekr.20181115120317.1: *3* class LeoBrowserMinibuffer
class LeoBrowserMinibuffer (flx.PyComponent):
    
    def init(self, c, g):
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        
    #@+others
    #@-others
#@+node:ekr.20181115092337.32: *3* class LeoBrowserStatusLine
class LeoBrowserStatusLine(flx.PyComponent):
    
    def init(self, c, g):
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        self.textWidget = StringTextWrapper(c, g, 'status-line')
        # Set the official ivars.
        c.frame.statusFrame = None
        c.frame.statusLabel = None
        c.frame.statusText = self.textWidget
        ###
            # self.enabled = True
        
    #@+others
    #@+node:ekr.20181115112320.2: *4* NullStatusLineClass.methods
    def disable(self, background=None):
        pass
        ### self.enabled = False
        ### self.c.bodyWantsFocus()

    def enable(self, background="white"):
        pass
        ### self.c.widgetWantsFocus(self.textWidget)
        ### self.enabled = True

    def clear(self):
        pass
        ### self.textWidget.delete(0, 'end')

    def get(self):
        return ''
        ### return self.textWidget.getAllText()

    def isEnabled(self):
        return True
        ### return self.enabled

    def put(self, s, bg=None, fg=None):
        pass ### To do.
        ### self.message('insert-at-end', s)
        ### self.textWidget.insert('end', s)

    def setFocus(self):
        pass

    def update(self):
        pass
    #@-others
#@+node:ekr.20181115092337.57: *3* class LeoBrowserTree
class LeoBrowserTree(flx.PyComponent):
    
    def init(self, c, g):
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        self.edit_text_dict = {}
        self.editWidgetsDict = {}
            # Keys are tnodes, values are StringTextWidgets.
        self.redrawCount = 0
        self.revertHeadline = None
    #
    ### From LeoTree
            # New in 4.2: keys are vnodes, values are pairs (p,edit widgets).
        # "public" ivars: correspond to setters & getters.
        # self.frame = frame
        # self.drag_p = None
        # self.generation = 0
            # Leo 5.6: low-level vnode methods increment
            # this count whenever the tree changes.
        # self.use_chapters = False
    #
    ### From NullTree
        # self.font = None
        # self.fontName = None
        # self.canvas = None
        # self.updateCount = 0
        
    #@+others
    #@+node:ekr.20181115111037.1: *4* bt.oops
    def oops(self):
        g = self.g
        print("LeoTree oops:", g.callers(4), "should be overridden in subclass")
    #@+node:ekr.20181115111104.1: *4* bt.onHeadChanged (Used by the leoBridge module)
    # Tricky code: do not change without careful thought and testing.
    # Important: This code *is* used by the leoBridge module.
    # See also, nativeTree.onHeadChanged.

    def onHeadChanged(self, p, undoType='Typing', s=None, e=None): # e used in qt_tree.py.
        '''
        Officially change a headline.
        Set the old undo text to the previous revert point.
        '''
        c, g = self.c, self.g
        u = c.undoer
        w = self.edit_widget(p)
        if c.suppressHeadChanged:
            return
        if not w:
            return
        ch = '\n' # New in 4.4: we only report the final keystroke.
        if s is None: s = w.getAllText()
        #@+<< truncate s if it has multiple lines >>
        #@+node:ekr.20181115111104.2: *5* << truncate s if it has multiple lines >>
        # Remove trailing newlines before warning of truncation.
        while s and s[-1] == '\n':
            s = s[: -1]
        # Warn if there are multiple lines.
        i = s.find('\n')
        if i > -1:
            g.warning("truncating headline to one line")
            s = s[: i]
        limit = 1000
        if len(s) > limit:
            g.warning("truncating headline to", limit, "characters")
            s = s[: limit]
        s = g.toUnicode(s or '')

        #@-<< truncate s if it has multiple lines >>
        # Make the change official, but undo to the *old* revert point.
        oldRevert = self.revertHeadline
        changed = s != oldRevert
        self.revertHeadline = s
        p.initHeadString(s)
        if g.doHook("headkey1", c=c, p=p, ch=ch, changed=changed):
            return # The hook claims to have handled the event.
        if changed:
            undoData = u.beforeChangeNodeContents(p, oldHead=oldRevert)
            if not c.changed: c.setChanged(True)
            # New in Leo 4.4.5: we must recolor the body because
            # the headline may contain directives.
            c.frame.scanForTabWidth(p)
            c.frame.body.recolor(p)
            dirtyVnodeList = p.setDirty()
            u.afterChangeNodeContents(p, undoType, undoData,
                dirtyVnodeList=dirtyVnodeList, inHead=True)
        if changed:
            c.redraw_after_head_changed()
            # Fix bug 1280689: don't call the non-existent c.treeEditFocusHelper
        g.doHook("headkey2", c=c, p=p, ch=ch, changed=changed)
    #@+node:ekr.20181115092337.59: *4* bt.printWidgets (not used)
    if 0:
        def printWidgets(self):
            d = self.editWidgetsDict
            for key in d:
                # keys are vnodes, values are StringTextWidgets.
                w = d.get(key)
                print('w', w, 'v.h:', key.headString, 's:', repr(w.s))
    #@+node:ekr.20181115092337.66: *4* bt.setHeadline
    def setHeadline(self, p, s):
        '''
        Set the actual text of the headline widget.

        This is called from the undo/redo logic to change the text before redrawing.
        '''
        ### self.message('set-headline', gnx=p.gnx, s=s)
        w = self.edit_widget(p)
        if w:
            w.delete(0, 'end')
            if s.endswith('\n') or s.endswith('\r'):
                s = s[: -1]
            w.insert(0, s)
            self.revertHeadline = s
        else:
            print('-' * 20, 'oops')
    #@+node:ekr.20181115175557.1: *4* From LeoTree
    #@+node:ekr.20181115111153.1: *5* LeoTree.Must be defined in base class
    #@+node:ekr.20181115111153.2: *6* LeoTree.endEditLabel
    def endEditLabel(self):
        '''End editing of a headline and update p.h.'''
        c = self.c; k = c.k; p = c.p
        # Important: this will redraw if necessary.
        self.onHeadChanged(p)
        if 0:
            # Can't call setDefaultUnboundKeyAction here: it might put us in ignore mode!
            k.setDefaultInputState()
            k.showStateAndMode()
        if 0:
            # This interferes with the find command and interferes with focus generally!
            c.bodyWantsFocus()
    #@+node:ekr.20181115111153.3: *6* LeoTree.getEditTextDict
    def getEditTextDict(self, v):
        # New in 4.2: the default is an empty list.
        return self.edit_text_dict.get(v, [])
    #@+node:ekr.20181115111153.4: *6* LeoTree.injectCallbacks
    def injectCallbacks(self):
        c, g = self.c, self.g
        #@+<< define callbacks to be injected in the position class >>
        #@+node:ekr.20181115111153.5: *7* << define callbacks to be injected in the position class >>
        # **Important:: These VNode methods are entitled to know about gui-level code.
        #@+others
        #@+node:ekr.20181115111153.6: *8* OnHyperLinkControlClick
        def OnHyperLinkControlClick(self, event=None, c=c):
            '''Callback injected into position class.'''
            p = self
            if c and c.exists:
                try:
                    if not g.doHook("hypercclick1", c=c, p=p, event=event):
                        c.selectPosition(p)
                        c.redraw()
                        c.frame.body.wrapper.setInsertPoint(0)
                    g.doHook("hypercclick2", c=c, p=p, event=event)
                except Exception:
                    g.es_event_exception("hypercclick")
        #@+node:ekr.20181115111153.7: *8* OnHyperLinkEnter
        def OnHyperLinkEnter(self, event=None, c=c):
            '''Callback injected into position class.'''
            try:
                p = self
                g.doHook("hyperenter1", c=c, p=p, event=event)
                g.doHook("hyperenter2", c=c, p=p, event=event)
            except Exception:
                g.es_event_exception("hyperenter")
        #@+node:ekr.20181115111153.8: *8* OnHyperLinkLeave
        def OnHyperLinkLeave(self, event=None, c=c):
            '''Callback injected into position class.'''
            try:
                p = self
                g.doHook("hyperleave1", c=c, p=p, event=event)
                g.doHook("hyperleave2", c=c, p=p, event=event)
            except Exception:
                g.es_event_exception("hyperleave")
        #@-others
        #@-<< define callbacks to be injected in the position class >>
        for f in (OnHyperLinkControlClick, OnHyperLinkEnter, OnHyperLinkLeave):
            g.funcToMethod(f, leoNodes.position)
    #@+node:ekr.20181115111153.9: *6* LeoTree.onHeadlineKey
    def onHeadlineKey(self, event):
        '''Handle a key event in a headline.'''
        w = event.widget if event else None
        ch = event.char if event else ''
        # This test prevents flashing in the headline when the control key is held down.
        if ch:
            self.updateHead(event, w)
    #@+node:ekr.20181115111153.10: *6* LeoTree.OnIconCtrlClick (@url)
    def OnIconCtrlClick(self, p):
        self.g.openUrl(p)
    #@+node:ekr.20181115111153.11: *6* LeoTree.OnIconDoubleClick (do nothing)
    def OnIconDoubleClick(self, p):
        pass
    #@+node:ekr.20181115111153.12: *6* LeoTree.updateHead
    def updateHead(self, event, w):
        '''Update a headline from an event.

        The headline officially changes only when editing ends.
        '''
        k = self.c.k
        ch = event.char if event else ''
        i, j = w.getSelectionRange()
        ins = w.getInsertPoint()
        if i != j:
            ins = i
        if ch in ('\b', 'BackSpace'):
            if i != j:
                w.delete(i, j)
                # Bug fix: 2018/04/19.
                w.setSelectionRange(i, i, insert=i)
            elif i > 0:
                i -= 1
                w.delete(i)
                w.setSelectionRange(i, i, insert=i)
            else:
                w.setSelectionRange(0, 0, insert=0)
        elif ch and ch not in ('\n', '\r'):
            if i != j:
                w.delete(i, j)
            elif k.unboundKeyAction == 'overwrite':
                w.delete(i, i + 1)
            w.insert(ins, ch)
            w.setSelectionRange(ins + 1, ins + 1, insert=ins + 1)
        s = w.getAllText()
        if s.endswith('\n'):
            s = s[: -1]
        # 2011/11/14: Not used at present.
            # w.setWidth(self.headWidth(s=s))
        if ch in ('\n', '\r'):
            self.endEditLabel() # Now calls self.onHeadChanged.
    #@+node:ekr.20181115175557.3: *5* LeoTree.May be defined in subclasses
    # These are new in Leo 4.6.

    def initAfterLoad(self):
        '''Do late initialization. Called in g.openWithFileName after a successful load.'''

    # Hints for optimization. The proper default is c.redraw()

    def redraw_after_contract(self, p):
        self.c.redraw()

    def redraw_after_expand(self, p):
        self.c.redraw()

    def redraw_after_head_changed(self):
        self.c.redraw()

    def redraw_after_icons_changed(self):
        self.c.redraw()

    def redraw_after_select(self, p=None):
        self.c.redraw()
    #@+node:ekr.20181115175557.18: *5* LeoTree.Must be defined in subclasses
    # Drawing & scrolling.
    def drawIcon(self, p):
        self.oops()

    def redraw(self, p=None):
        self.oops()
    redraw_now = redraw

    def scrollTo(self, p): self.oops()

    # Headlines.
    def editLabel(self, p, selectAll=False, selection=None):
        self.oops()

    def edit_widget(self, p):
        self.oops()
    #@+node:ekr.20181115175557.19: *5* LeoTree.select & helpers
    tree_select_lockout = False

    def select(self, p):
        '''
        Select a node.
        Never redraws outline, but may change coloring of individual headlines.
        The scroll argument is used by the gui to suppress scrolling while dragging.
        '''
        g = self.c
        if g.app.killed or self.tree_select_lockout: # Essential.
            return None
        try:
            c = self.c
            self.tree_select_lockout = True
            self.prev_v = c.p.v
            self.selectHelper(p)
        finally:
            self.tree_select_lockout = False
            if c.enableRedrawFlag:
                p = c.p
                # Don't redraw during unit testing: an important speedup.
                if c.expandAllAncestors(p) and not g.unitTesting:
                    # This can happen when doing goto-next-clone.
                    c.redraw_later()
                        # This *does* happen sometimes.
                else:
                    c.outerUpdate() # Bring the tree up to date.
                    if hasattr(self, 'setItemForCurrentPosition'):
                        # pylint: disable=no-member
                        self.setItemForCurrentPosition()
            else:
                c.requestLaterRedraw = True
    #@+node:ekr.20181115175557.20: *6* selectHelper (LeoTree) & helpers
    def selectHelper(self, p):
        '''
        A helper function for leoTree.select.
        Do **not** "optimize" this by returning if p==c.p!
        '''
        g = self.c
        if not p:
            # This is not an error! We may be changing roots.
            # Do *not* test c.positionExists(p) here!
            return
        c = self.c
        if not c.frame.body.wrapper:
            return # Defensive.
        assert p.v.context == c
            # Selecting a foreign position will not be pretty.
        old_p = c.p
        call_event_handlers = p != old_p
        # Order is important...
        self.unselect_helper(old_p, p)
        self.select_new_node(old_p, p)
        self.change_current_position(old_p, p)
        self.scroll_cursor(p)
        self.set_status_line(p)
        if call_event_handlers:
            g.doHook("select2", c=c, new_p=p, old_p=old_p, new_v=p, old_v=old_p)
            g.doHook("select3", c=c, new_p=p, old_p=old_p, new_v=p, old_v=old_p)
    #@+node:ekr.20181115175557.21: *7* LeoTree.is_qt_body (not used)
    if 0:

        def is_qt_body(self):
            '''Return True if the body widget is a QTextEdit.'''
            c = self.c
            import leo.plugins.qt_text as qt_text
            w = c.frame.body.wrapper.widget
            val = isinstance(w, qt_text.LeoQTextBrowser)
                # c.frame.body.wrapper.widget is a LeoQTextBrowser.
                # c.frame.body.wrapper is a QTextEditWrapper or QScintillaWrapper.
            return val
    #@+node:ekr.20181115175557.22: *7* 1. LeoTree.unselect_helper & helper
    def unselect_helper(self, old_p, p):
        '''Unselect the old node, calling the unselect hooks.'''
        c, g = self.c, self.g
        call_event_handlers = p != old_p
        if call_event_handlers:
            unselect = not g.doHook("unselect1", c=c, new_p=p, old_p=old_p, new_v=p, old_v=old_p)
        else:
            unselect = True
        if unselect and old_p != p:
            # Actually unselect the old node.
            self.endEditLabel()
        if call_event_handlers:
            g.doHook("unselect2", c=c, new_p=p, old_p=old_p, new_v=p, old_v=old_p)
    #@+node:ekr.20181115175557.23: *7* 2. LeoTree.select_new_node & helper
    def select_new_node(self, old_p, p):
        '''Select the new node, part 1.'''
        c, g = self.c, self.g
        call_event_handlers = p != old_p
        if call_event_handlers:
            select = not g.doHook("select1",
                c=c, new_p=p, old_p=old_p,
                new_v=p, old_v=old_p)
        else:
            select = True
        if select:
            self.revertHeadline = p.h
            # Not that expensive
            c.frame.setWrap(p)
            self.set_body_text_after_select(p, old_p)
            c.nodeHistory.update(p)
    #@+node:ekr.20181115175557.24: *8* LeoTree.set_body_text_after_select
    def set_body_text_after_select(self, p, old_p, force=False):
        '''Set the text after selecting a node.'''
        c = self.c
        w = c.frame.body.wrapper
        s = p.v.b # Guaranteed to be unicode.
        # Part 1: get the old text.
        old_s = w.getAllText()
        if not force and p and p == old_p and s == old_s:
            return
        # Part 2: set the new text. This forces a recolor.
        c.setCurrentPosition(p)
            # Important: do this *before* setting text,
            # so that the colorizer will have the proper c.p.
        w.setAllText(s)
        # This is now done after c.p has been changed.
            # p.restoreCursorAndScroll()
    #@+node:ekr.20181115175557.25: *7* 3. LeoTree.change_current_position
    def change_current_position(self, old_p, p):
        '''Select the new node, part 2.'''
        c = self.c
        # c.setCurrentPosition(p)
            # This is now done in set_body_text_after_select.
        c.frame.scanForTabWidth(p)
            #GS I believe this should also get into the select1 hook
        use_chapters = c.config.getBool('use-chapters')
        if use_chapters:
            cc = c.chapterController
            theChapter = cc and cc.getSelectedChapter()
            if theChapter:
                theChapter.p = p.copy()
        # Do not call treeFocusHelper here!
            # c.treeFocusHelper()
        c.undoer.onSelect(old_p, p)
    #@+node:ekr.20181115175557.26: *7* 4. LeoTree.scroll_cursor
    def scroll_cursor(self, p):
        '''Scroll the cursor.'''
        p.restoreCursorAndScroll()
            # Was in setBodyTextAfterSelect
    #@+node:ekr.20181115175557.27: *7* 5. LeoTree.set_status_line
    def set_status_line(self, p):
        '''Update the status line.'''
        c = self.c
        c.frame.body.assignPositionToEditor(p)
            # New in Leo 4.4.1.
        c.frame.updateStatusLine()
            # New in Leo 4.4.1.
        c.frame.clearStatusLine()
        verbose = getattr(c, 'status_line_unl_mode', '') == 'canonical'
        if p and p.v:
            c.frame.putStatusLine(p.get_UNL(with_proto=verbose, with_index=verbose))
    #@-others
#@+node:ekr.20181115092337.33: *3* class StringTextWrapper (object)
class StringTextWrapper(object):
    '''
    A class that represents text as a Python string.
    This class forwards messages to the browser.
    '''
    def __init__(self, c, g, name):
        '''Ctor for the StringTextWrapper class.'''
        # pylint: disable=arguments-differ
        self.c = c
        self.g = g
        self.name = name
        self.ins = 0
        self.sel = 0, 0
        self.s = ''
        self.supportsHighLevelInterface = True
        self.widget = None # This ivar must exist, and must be None.
    
    def __repr__(self):
        return '<StringTextWrapper: %s>' % (self.name)
    
    def getName(self):
        return self.name # Essential.

    #@+others
    #@+node:ekr.20181115092337.34: *4* stw.Clipboard
    def clipboard_clear(self):
        g = self.g
        g.app.gui.replaceClipboardWith('')

    def clipboard_append(self, s):
        g = self.g
        s1 = g.app.gui.getTextFromClipboard()
        self.g.app.gui.replaceClipboardWith(s1 + s)
    #@+node:ekr.20181115092337.35: *4* stw.Config
    def setStyleClass(self, name):
        pass 
        ### self.message('set-style', name=name)

    def tag_configure(self, colorName, **kwargs):
        pass
        ### kwargs['color-name'] = colorName
        ### self.message('configure-tag', keys=kwargs)
    #@+node:ekr.20181115092337.36: *4* stw.flashCharacter
    def flashCharacter(self, i, bg='white', fg='red', flashes=3, delay=75):
        pass
        ### self.message('flash-character', i=i, bg=bg, fg=fg, flashes=flashes, delay=delay)
    #@+node:ekr.20181115092337.37: *4* stw.Focus
    def getFocus(self):
        # This isn't in StringTextWrapper.
        pass
        ### self.message('get-focus')

    def setFocus(self):
        pass
        ### self.message('set-focus')
    #@+node:ekr.20181115092337.38: *4* stw.Insert Point
    def see(self, i):
        pass
        ### self.message('see-position', i=i)

    def seeInsertPoint(self):
        pass
        ### self.message('see-insert-point')
        
    #@+node:ekr.20181115092337.39: *4* stw.Scrolling
    def getXScrollPosition(self):
        ### self.message('get-x-scroll')
        return 0

    def getYScrollPosition(self):
        ### self.message('get-y-scroll')
        return 0
        
    def setXScrollPosition(self, i):
        pass
        ### self.message('set-x-scroll', i=i)
        
    def setYScrollPosition(self, i):
        pass
        ### self.message('set-y-scroll', i=i)
        
    #@+node:ekr.20181115092337.40: *4* stw.Text
    #@+node:ekr.20181115092337.41: *5* stw.appendText
    def appendText(self, s):
        '''StringTextWrapper.'''
        self.s = self.s + s
        self.ins = len(self.s)
        self.sel = self.ins, self.ins
        ### self.message('body-append-text', s=s)
    #@+node:ekr.20181115092337.42: *5* stw.delete
    def delete(self, i, j=None):
        '''StringTextWrapper.'''
        i = self.toPythonIndex(i)
        if j is None: j = i + 1
        j = self.toPythonIndex(j)
        # This allows subclasses to use this base class method.
        if i > j: i, j = j, i
        s = self.getAllText()
        self.setAllText(s[: i] + s[j:])
        # Bug fix: 2011/11/13: Significant in external tests.
        self.setSelectionRange(i, i, insert=i)
        ### self.message('body-delete-text',
            # s=s[:i]+s[j:],
            # sel=(i,i,i))
    #@+node:ekr.20181115092337.43: *5* stw.deleteTextSelection
    def deleteTextSelection(self):
        '''StringTextWrapper.'''
        i, j = self.getSelectionRange()
        self.delete(i, j)
    #@+node:ekr.20181115092337.44: *5* stw.get
    def get(self, i, j=None):
        '''StringTextWrapper.'''
        g = self.g
        i = self.toPythonIndex(i)
        if j is None:
            j = i + 1
        j = self.toPythonIndex(j)
        s = self.s[i: j]
        ### self.message('body-get-text', s=s)
        return g.toUnicode(s)
    #@+node:ekr.20181115092337.45: *5* stw.getAllText
    def getAllText(self):
        '''StringTextWrapper.'''
        g = self.g
        s = self.s
        ### self.message('body-get-all-text')
        return g.toUnicode(s)
    #@+node:ekr.20181115092337.46: *5* stw.getInsertPoint
    def getInsertPoint(self):
        '''StringTextWrapper.'''
        # self.message('body-get-insert-point')
        i = self.ins
        if i is None:
            if self.virtualInsertPoint is None:
                i = 0
            else:
                i = self.virtualInsertPoint
        self.virtualInsertPoint = i
        return i
    #@+node:ekr.20181115092337.47: *5* stw.getSelectedText
    def getSelectedText(self):
        '''StringTextWrapper.'''
        g = self.g
        # self.message('body-get-selected-text')
        i, j = self.sel
        s = self.s[i: j]
        return g.toUnicode(s)
    #@+node:ekr.20181115092337.48: *5* stw.getSelectionRange
    def getSelectionRange(self, sort=True):
        '''StringTextWrapper'''
        # self.message('body-get-selection-range')
        sel = self.sel
        if len(sel) == 2 and sel[0] >= 0 and sel[1] >= 0:
            i, j = sel
            if sort and i > j:
                sel = j, i
            return sel
        else:
            i = self.ins
            return i, i
    #@+node:ekr.20181115092337.49: *5* stw.hasSelection
    def hasSelection(self):
        '''StringTextWrapper.'''
        # self.message('body-has-selection')
        i, j = self.getSelectionRange()
        return i != j
    #@+node:ekr.20181115092337.50: *5* stw.insert
    def insert(self, i, s):
        '''StringTextWrapper.'''
        i = self.toPythonIndex(i)
        s1 = s
        self.s = self.s[: i] + s1 + self.s[i:]
        i += len(s1)
        self.ins = i
        self.sel = i, i
    #@+node:ekr.20181115092337.51: *5* stw.selectAllText
    def selectAllText(self, insert=None):
        '''StringTextWrapper.'''
        self.setSelectionRange(0, 'end', insert=insert)
    #@+node:ekr.20181115092337.52: *5* stw.setAllText
    def setAllText(self, s):
        '''StringTextWrapper.'''
        self.s = s
        i = len(self.s)
        self.ins = i
        self.sel = i, i
    #@+node:ekr.20181115092337.53: *5* stw.setInsertPoint
    def setInsertPoint(self, pos, s=None):
        '''StringTextWrapper.'''
        self.virtualInsertPoint = i = self.toPythonIndex(pos)
        self.ins = i
        self.sel = i, i
    #@+node:ekr.20181115092337.54: *5* stw.setSelectionRange
    def setSelectionRange(self, i, j, insert=None):
        '''StringTextWrapper.'''
        i, j = self.toPythonIndex(i), self.toPythonIndex(j)
        self.sel = i, j
        self.ins = j if insert is None else self.toPythonIndex(insert)
    #@+node:ekr.20181115092337.55: *5* stw.toPythonIndex
    def toPythonIndex(self, index):
        '''StringTextWrapper.'''
        g = self.g
        return g.toPythonIndex(self.s, index)
    #@+node:ekr.20181115092337.56: *5* stw.toPythonIndexRowCol
    def toPythonIndexRowCol(self, index):
        '''StringTextWrapper.'''
        g = self.g
        s = self.getAllText()
        i = self.toPythonIndex(index)
        row, col = g.convertPythonIndexToRowCol(s, i)
        return i, row, col
    #@-others
#@+node:ekr.20181107052700.1: ** Js side: flx.Widgets
#@+node:ekr.20181104082144.1: *3* class LeoFlexxBody

class LeoFlexxBody(flx.Widget):
    
    """ A CodeEditor widget based on Ace.
    """

    CSS = """
    .flx-CodeEditor > .ace {
        width: 100%;
        height: 100%;
    }
    """

    def init(self, body):
        # pylint: disable=arguments-differ
        # pylint: disable=undefined-variable
            # window
        global window
        self.ace = window.ace.edit(self.node, "editor")
        self.ace.navigateFileEnd()  # otherwise all lines highlighted
        self.ace.setTheme("ace/theme/solarized_dark")
        self.ace.getSession().setMode("ace/mode/python")
        self.set_body(body)

    @flx.reaction('size')
    def __on_size(self, *events):
        self.ace.resize()
        
    @flx.action
    def set_body(self, body):
        self.ace.setValue(body)
#@+node:ekr.20181104082149.1: *3* class LeoFlexxLog
class LeoFlexxLog(flx.Widget):

    CSS = """
    .flx-CodeEditor > .ace {
        width: 100%;
        height: 100%;
    }
    """

    def init(self, signon):
        # pylint: disable=arguments-differ
        # pylint: disable=undefined-variable
            # window
        global window
        self.ace = window.ace.edit(self.node, "editor")
        self.ace.navigateFileEnd()  # otherwise all lines highlighted
        self.ace.setTheme("ace/theme/solarized_dark")
        self.ace.setValue(signon)
        
    @flx.action
    def put(self, s):
        self.ace.setValue(self.ace.getValue() + '\n' + s)

    @flx.reaction('size')
    def __on_size(self, *events):
        self.ace.resize()
#@+node:ekr.20181104082130.1: *3* class LeoFlexxMainWindow
class LeoFlexxMainWindow(flx.Widget):
    
    '''
    Leo's main window, that is, root.main_window.
    
    Each property x below is accessible as root.main_window.x.
    '''
    # All these properties *are* needed.
    body = flx.ComponentProp(settable=True)
    log = flx.ComponentProp(settable=True)
    minibuffer = flx.ComponentProp(settable=True)
    status_line = flx.ComponentProp(settable=True)
    tree = flx.ComponentProp(settable=True)

    def init(self, body_s, data, signon):
        # pylint: disable=arguments-differ
        with flx.VSplit():
            with flx.HSplit(flex=1):
                tree = LeoFlexxTree(data, flex=1)
                log = LeoFlexxLog(signon, flex=1)
            body = LeoFlexxBody(body_s, flex=1)
            minibuffer = LeoFlexxMiniBuffer()
            status_line = LeoFlexxStatusLine()
        for name, prop in (
            ('body', body),
            ('log', log),
            ('minibuffer', minibuffer),
            ('status_line', status_line),
            ('tree', tree),
        ):
            self._mutate(name, prop)

    #@+others
    #@-others
#@+node:ekr.20181104082154.1: *3* class LeoFlexxMiniBuffer
class LeoFlexxMiniBuffer(flx.Widget):

    def init(self): 
        with flx.HBox():
            flx.Label(text='Minibuffer')
            self.widget = flx.LineEdit(flex=1, placeholder_text='Enter command')
        self.widget.apply_style('background: yellow')
    
    @flx.action
    def set_text(self, s):
        self.widget.set_text(s)
        
    @flx.reaction('widget.user_done')
    def on_event(self, *events):
        for ev in events:
            command = self.widget.text
            if command.strip():
                self.widget.set_text('')
                self.root.do_command(command)
#@+node:ekr.20181104082201.1: *3* class LeoFlexxStatusLine
class LeoFlexxStatusLine(flx.Widget):
    
    def init(self):
        with flx.HBox():
            flx.Label(text='Status Line')
            self.widget = flx.LineEdit(flex=1, placeholder_text='Status')
        self.widget.apply_style('background: green')

    @flx.action
    def set_text(self, s):
        self.widget.set_text(s)
#@+node:ekr.20181104082138.1: *3* class LeoFlexxTree
class LeoFlexxTree(flx.Widget):

    CSS = '''
    .flx-TreeWidget {
        background: #000;
        color: white;
        /* background: #ffffec; */
        /* Leo Yellow */
        /* color: #afa; */
    }
    '''
    
    def init(self, redraw_dict):
        # pylint: disable=arguments-differ
        self.leo_items = {}
            # Keys are ap keys, created by tree.ap_to_key.
            # values are LeoTreeItems.
        self.leo_populated_dict = {}
            # Keys are ap keys, created by tree.ap_to_key.
            # values are ap's.
        self.clear_tree()
        self.tree = flx.TreeWidget(flex=1, max_selected=1)
            # The gnx of the selected tree item.
        self.redraw_from_dict(redraw_dict)
        
    #@+others
    #@+node:ekr.20181112163222.1: *4* tree.actions
    #@+node:ekr.20181112163252.1: *5* tree.action: clear_tree
    @flx.action
    def clear_tree(self):
        '''
        Completely clear the tree, preparing to recreate it.
        
        Important: we do *not* clear self.tree itself!
        '''
        # pylint: disable=access-member-before-definition
        #
        # print('===== tree.clear_tree')
        #
        # Clear all tree items.
        for item in self.leo_items.values():
            if debug or debug_tree:
                print('tree.clear_tree: dispose: %r' % item)
            item.dispose()
        #
        # Clear the internal data structures.
        self.leo_items = {}
        self.leo_populated_dict = {}
    #@+node:ekr.20181110175222.1: *5* tree.action: receive_children
    @flx.action
    def receive_children(self, d):
        '''
        Using d, populate the children of ap. d has the form:
            {
                'parent': ap,
                'children': [ap1, ap2, ...],
            }
        '''
        parent_ap = d ['parent']
        children = d ['children']
        self.populate_children(children, parent_ap)
    #@+node:ekr.20181113043004.1: *5* tree.action: redraw
    @flx.action
    def redraw(self, redraw_dict):
        '''
        Clear the present tree and redraw using the redraw_list.
        '''
        self.clear_tree()
        self.redraw_from_dict(redraw_dict)
    #@+node:ekr.20181114072307.1: *4* tree.ap_to_key
    def ap_to_key(self, ap):
        '''Produce a key for the given ap.'''
        childIndex = ap ['childIndex']
        gnx = ap ['gnx']
        headline = ap ['headline'] # Important for debugging.
        stack = ap ['stack']
        stack_s = '::'.join([
            'childIndex: %s, gnx: %s' % (z ['childIndex'], z ['gnx'])
                for z in stack
        ])
        key = 'Tree key<childIndex: %s, gnx: %s, %s <stack: %s>>' % (
            childIndex, gnx, headline, stack_s or '[]')
        if False and key not in self.leo_populated_dict:
            print('')
            print('tree.ap_to_key: new key', ap ['headline'])
            print('key', key)
        return key
    #@+node:ekr.20181112172518.1: *4* tree.reactions
    #@+node:ekr.20181109083659.1: *5* tree.reaction: on_selected_event
    @flx.reaction('tree.children**.selected')
    def on_selected_event(self, *events):
        '''
        Update the tree and body text when the user selects a new tree node.
        '''
        for ev in events:
            if ev.new_value:
                # We are selecting a node, not de-selecting it.
                ap = ev.source.leo_ap
                self.leo_selected_ap = ap
                    # Track the change.
                self.root.set_body(ap)
                    # Set the body text directly.
                self.root.set_status_to_unl(ap)
                    # Set the status line directly.
                self.root.send_children_to_tree(ap)
                    # Send the children back to us.
    #@+node:ekr.20181104080854.3: *5* tree.reaction: on_tree_event
    # actions: set_checked, set_collapsed, set_parent, set_selected, set_text, set_visible
    @flx.reaction(
        'tree.children**.checked',
        'tree.children**.collapsed',
        'tree.children**.visible', # Never seems to fire.
    )
    def on_tree_event(self, *events):
        for ev in events:
            if 0:
                self.show_event(ev)
    #@+node:ekr.20181111011928.1: *4* tree.populate_children
    def populate_children(self, children, parent_ap):
        '''Populate parent with the children if necessary.'''
        trace = False
        if trace: print('tree.populate_children...')
        parent_key = self.ap_to_key(parent_ap)
        if parent_key in self.leo_populated_dict:
            # print('tree.populate_children: already populated', parent_ap ['headline'])
            return
        #
        # Set the key once, here.
        self.leo_populated_dict [parent_key] = parent_ap
        #
        # Populate the items.
        if parent_key not in self.leo_items:
            print('tree.populate_children: can not happen')
            self.root.dump_ap(parent_ap, None, 'parent_ap')
            for item in self.leo_items:
                print(item)
            return
        if trace:
            print('tree.populate_children:', len(children))
            print('parent_ap', repr(parent_ap))
            print('parent item:', repr(self.leo_items[parent_ap]))
        with self.leo_items[parent_key]:
            for child_ap in children:
                headline = child_ap ['headline']
                child_key = self.ap_to_key(child_ap)
                child_item = LeoFlexxTreeItem(child_ap, text=headline, checked=None, collapsed=True)
                self.leo_items [child_key] = child_item
    #@+node:ekr.20181113043131.1: *4* tree.redraw_from_dict & helper
    def redraw_from_dict(self, d):
        '''
        Create LeoTreeItems from all items in the redraw_dict.
        The tree has already been cleared.
        '''
        # print('==== tree.redraw_from_dict')
        self.leo_selected_ap = d ['c.p']
            # Usually set in on_selected_event.
        for item in d ['items']:
            self.create_item_with_parent(item, self.tree)
           
    def create_item_with_parent(self, item, parent):
        '''Create a tree item for item and all its visible children.'''
        with parent:
            ap = item ['ap']
            headline = ap ['headline']
            # Create the tree item.
            tree_item = LeoFlexxTreeItem(ap, text=headline, checked=None, collapsed=True)
            key = self.ap_to_key(ap)
            self.leo_items [key] = tree_item
            # Create the item's children...
            for child in item ['children']:
                self.create_item_with_parent(child, tree_item)
    #@+node:ekr.20181108232118.1: *4* tree.show_event
    def show_event(self, ev):
        '''Put a description of the event to the log.'''
        w = self.root.main_window
        id_ = ev.source.title or ev.source.text
        kind = '' if ev.new_value else 'un-'
        s = kind + ev.type
        message = '%s: %s' % (s.rjust(15), id_)
        w.log.put(message)
        if debug and debug_tree:
            print('tree.show_event: ' + message)
    #@-others
#@+node:ekr.20181108233657.1: *3* class LeoFlexxTreeItem
class LeoFlexxTreeItem(flx.TreeItem):
    
    def init(self, leo_ap):
        # pylint: disable=arguments-differ
        self.leo_ap = leo_ap
#@-others
if __name__ == '__main__':
    flx.launch(LeoApp)
    flx.logger.info('LeoApp: after flx.launch')
    if not debug:
        suppress_unwanted_log_messages()
    flx.run()
#@-leo
