import wx
import re # 名余曰Regex兮，字余曰灵均
import os.path
import webbrowser

# 匹配项颜色
YELLOW = wx.Colour(255,253,84)
BLUE = wx.Colour(179,219,251)

class MainFrame(wx.Frame):

    def __init__(self,*args,**kw):
        super(MainFrame, self).__init__(*args, **kw)
        
        self.pnl = wx.Panel(self)
        self.InitUI()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.path = "无标题"
        self.zoomFactor = 1
        self.IsEdited = False
        self.defaultFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, "宋体")
        self.tc.SetFont(self.defaultFont)
        self.fontColor = None
        self.autowraplength = 400 # 过长文本自动开启自动换行
        self.selectedText = ""
        self.selectedTextLength = 0
        self.matches = []  # 存储所有匹配项的位置
        self.current_match_index = -1  # 当前选中的匹配项索引
        self.IsCaseSensitive = False # 区分大小写开关
        self.IsWholeWord = False # 全词匹配开关
        self.IsRegexSearch = False # 正则搜索开关

    def InitUI(self):

        self.tc = wx.TextCtrl(self.pnl, -1 , '',
            style=wx.TE_DONTWRAP | wx.TE_MULTILINE | wx.TE_RICH2)

        self.tc.Bind(wx.EVT_TEXT, self.OnEdited)
        self.tc.Bind(wx.EVT_KEY_UP, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_LEFT_UP,self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_MOTION, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_TEXT, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_KEY_DOWN, self.KeyMouseEvent)
        
        # 菜单栏
        self.makeMenuBar()
        # 右键菜单
        self.tc.Bind(wx.EVT_RIGHT_DOWN, self.OnShowContextMenu)
        
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetFieldsCount(3)
        self.statusBar.SetStatusWidths([-1, 100, 100])
        self.set_status_content()
        
        # 布局
        # vbox(hbox(line,tc),
        #      searchbox(sbox,rbox,bbox))
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        #linenumber
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox.Add(self.hbox, 1, wx.EXPAND)
        #self.hbox.Add(self.linenumber, 1, wx.EXPAND)
        self.hbox.Add(self.tc, 20, wx.EXPAND)
        
        self.searchbox = wx.BoxSizer(wx.VERTICAL) 
        if "searchbox": # 手动缩进
            self.vbox.Add(self.searchbox, 0, wx.EXPAND)
            
            sbox = wx.BoxSizer(wx.HORIZONTAL)
            self.rbox = wx.BoxSizer(wx.HORIZONTAL)
            self.bbox = wx.BoxSizer(wx.HORIZONTAL)
            
            self.searchbox.Add(sbox, 0, wx.EXPAND)
            self.searchbox.Add(self.rbox, 0, wx.EXPAND)
            self.searchbox.Add(self.bbox, 0, wx.EXPAND)
            
            st = wx.StaticText(self.pnl, -1, '查找')
            sbox.Add(st, 0, wx.ALIGN_LEFT | wx.ALL, 5)
            self.searchCtrl = wx.TextCtrl(self.pnl, -1, '', style=wx.TE_PROCESS_ENTER)
            sbox.Add(self.searchCtrl, 1, wx.ALL, 5)
            
            st = wx.StaticText(self.pnl, -1, '替换')
            self.rbox.Add(st, 0, wx.ALIGN_LEFT | wx.ALL, 5)
            self.replaceCtrl = wx.TextCtrl(self.pnl, -1, '', style=wx.TE_PROCESS_ENTER)
            self.rbox.Add(self.replaceCtrl, 1, wx.ALL, 5)
            
            self.prevBtn = wx.Button(self.pnl, -1, '上个')
            self.nextBtn = wx.Button(self.pnl, -1, '下个')
            self.replaceBtn = wx.Button(self.pnl, -1, '替换')
            self.replaceAllBtn = wx.Button(self.pnl, -1, '全部')
            self.caseBtn = wx.Button(self.pnl, -1, 'Cc', size=(25, 25))
            self.caseBtn.SetToolTip('区分大小写 (Alt+C)')
            self.wordBtn = wx.Button(self.pnl, -1, 'W', size=(25, 25))
            self.wordBtn.SetToolTip('全词匹配 (Alt+W)')
            self.regexBtn = wx.Button(self.pnl, -1, '.*', size=(25, 25))
            self.regexBtn.SetToolTip('正则表达式 (Alt+R)')
            self.closeBtn = wx.Button(self.pnl, -1, '✘', size=(25, 25))

            self.bbox.AddMany([
                (self.prevBtn, 1, wx.ALIGN_LEFT | wx.ALL, 5),
                (self.nextBtn, 1, wx.ALIGN_LEFT | wx.ALL, 5),
                (self.replaceBtn, 1, wx.ALIGN_LEFT | wx.ALL, 5),
                (self.replaceAllBtn, 1, wx.ALIGN_LEFT | wx.ALL, 5),
                (self.caseBtn, 0, wx.ALIGN_LEFT | wx.TOP, 5),
                (self.wordBtn, 0, wx.LEFT | wx.TOP, 5),
                (self.regexBtn, 0, wx.LEFT | wx.TOP, 5),
                (self.closeBtn, 0, wx.LEFT | wx.ALL, 5)])
            
            Btns = [self.prevBtn, self.nextBtn, self.replaceBtn,
                    self.replaceAllBtn, self.caseBtn, self.wordBtn,
                    self.regexBtn, self.closeBtn]
            for btn in Btns:
                btn.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
            
            self.searchCtrl.Bind(wx.EVT_TEXT,self.OnSearch)
            self.searchCtrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
            self.prevBtn.Bind(wx.EVT_BUTTON, self.OnPrevMatch)
            self.nextBtn.Bind(wx.EVT_BUTTON, self.OnNextMatch)
            self.replaceBtn.Bind(wx.EVT_BUTTON, self.OnReplace)
            self.replaceAllBtn.Bind(wx.EVT_BUTTON, self.OnReplaceAll)
            self.caseBtn.Bind(wx.EVT_BUTTON, self.OnToggleCase)
            self.wordBtn.Bind(wx.EVT_BUTTON, self.OnToggleWord)
            self.regexBtn.Bind(wx.EVT_BUTTON, self.OnToggleRegex)
            self.closeBtn.Bind(wx.EVT_BUTTON, self.OnToggleSearch)
        
        self.pnl.SetSizer(self.vbox)
        
        # 快捷键绑定
        self.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('R'), self.regexBtn.GetId()),
            (wx.ACCEL_ALT, ord('C'), self.caseBtn.GetId()),
            (wx.ACCEL_ALT, ord('W'), self.wordBtn.GetId()),
        ]))

    # 菜单栏
    def makeMenuBar(self):
        
        # 文件
        
        fileMenu = wx.Menu()
        newItem = fileMenu.Append(-1, '新建(&N)\tCtrl+N', '新建文件')
        openItem = fileMenu.Append(-1, '打开(&O)\tCtrl+O', '打开文件')
        saveItem = fileMenu.Append(-1, '保存(&S)\tCtrl+S', '保存文件')
        saveasItem = fileMenu.Append(-1, '另存为(&A)...', '保存文件为...')
        fileMenu.AppendSeparator()
        exitItem = fileMenu.Append(-1, '退出(&X)', '退出程序')
        self.Bind(wx.EVT_MENU, self.OnNew, newItem, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpen, openItem, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSave, saveItem, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, saveasItem, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnClose, exitItem, id=wx.ID_EXIT)
        
        # 编辑
        
        editMenu = wx.Menu()
        undoItem = editMenu.Append(wx.ID_UNDO, '撤销(&U)\tCtrl+Z')
        redoItem = editMenu.Append(wx.ID_REDO, '重做(&R)\tCtrl+Y')
        editMenu.AppendSeparator()
        cutItem = editMenu.Append(wx.ID_CUT, '剪切(&T)\tCtrl+X')
        copyItem = editMenu.Append(wx.ID_COPY, '复制(&C)\tCtrl+C')
        pasteItem = editMenu.Append(wx.ID_PASTE, '粘贴(&P)\tCtrl+V')
        deleteItem = editMenu.Append(wx.ID_DELETE, '删除(&L)\tDel')
        selectallItem = editMenu.Append(wx.ID_SELECTALL, '全选(&A)\tCtrl+A')
        editMenu.AppendSeparator()
        searchItem = editMenu.Append(-1, '查找(&F)\tCtrl+F')
        replaceItem = editMenu.Append(-1, '替换(&R)\tCtrl+H')
        gotoItem = editMenu.Append(-1, '转到(&G)\tCtrl+G')
        
        pasteItem.Enable(False)
        cutItem.Enable(False)
        copyItem.Enable(False)
        
        self.Bind(wx.EVT_MENU, self.OnUndo, undoItem)
        self.Bind(wx.EVT_MENU, self.OnRedo, redoItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAll, selectallItem)
        self.Bind(wx.EVT_MENU, self.OnDelete, deleteItem)
        self.Bind(wx.EVT_MENU, self.OnCopy, copyItem, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.OnPaste, pasteItem)
        self.Bind(wx.EVT_MENU, self.OnCut, cutItem, id)
        self.Bind(wx.EVT_MENU, self.OnToggleSearch, searchItem)
        self.Bind(wx.EVT_MENU, self.OnToggleReplace, replaceItem)
        self.Bind(wx.EVT_MENU, self.OnGoto, gotoItem)

        # 查看
        
        viewMenu = wx.Menu()
        self.statusItem = viewMenu.AppendCheckItem(
            wx.ID_STATIC, "&状态栏(&S)\tF9", "显示状态栏") # 查看菜单添加项
        self.statusItem.Check(True) # 状态栏默认勾选
        self.wrapItem = viewMenu.AppendCheckItem(-1, "自动换行\tF10")
        #viewMenu.Check(self.wrapItem.GetId(), False)
        fontItem = viewMenu.Append(-1, '字体(&F)', '设置字体样式')
        self.Bind(wx.EVT_MENU, self.OnFont, fontItem)
        self.Bind(wx.EVT_MENU, self.OnShowStatus, self.statusItem)
        self.Bind(wx.EVT_MENU, self.OnWrap, self.wrapItem)
        zoomMenu = wx.Menu()
        viewMenu.AppendSubMenu(zoomMenu, "缩放(&Z)") # 查看菜单添加子菜单
        zoomInItem = zoomMenu.Append(wx.ID_ZOOM_IN, "放大(&I)\tCtrl++ ") # 查看菜单添加项
        zoomOutItem = zoomMenu.Append(wx.ID_ZOOM_OUT, "缩小(&O)\tCtrl+-") # 查看菜单添加项
        zoomResetItem = zoomMenu.Append(wx.ID_ZOOM_100, "重置(&R)\tCtrl+0") # 查看菜单添加项
        self.Bind(wx.EVT_MENU, self.OnZoomIn, zoomInItem)
        self.Bind(wx.EVT_MENU, self.OnZoomOut, zoomOutItem)
        self.Bind(wx.EVT_MENU, self.OnZoomReset, zoomResetItem)

        # 帮助
        
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(-1,'关于')
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)
    
        # 创建菜单栏
        self.menuBar = wx.MenuBar()
        self.menuBar.Append(fileMenu, '文件(&F)')
        self.menuBar.Append(editMenu, '编辑(&E)')
        self.menuBar.Append(viewMenu, '查看(&V)')
        self.menuBar.Append(helpMenu, '帮助(&H)')
        self.SetMenuBar(self.menuBar)
    
    def OnShowContextMenu(self, event):
        contextMenu = wx.Menu()
        undoItem = contextMenu.Append(wx.ID_UNDO, "撤销(&U)")
        redoItem = contextMenu.Append(wx.ID_REDO, "重做(&R)")
        contextMenu.AppendSeparator()
        cutItem = contextMenu.Append(wx.ID_CUT, "剪切(&T)")
        copyItem = contextMenu.Append(wx.ID_COPY, "复制(&C)")
        pasteItem = contextMenu.Append(wx.ID_PASTE, "粘贴(&V)")
        deleteItem = contextMenu.Append(wx.ID_DELETE, "删除(&D)")
        selectallItem = contextMenu.Append(wx.ID_SELECTALL, "全选(&A)")
        contextMenu.AppendSeparator()
        fontItem = contextMenu.Append(-1, "字体(&F)")
        searchItem = contextMenu.Append(-1, "查找(&F)")
        
        # TE_RICH2内置撤销 重做 剪切 复制 粘贴 删除功能，故不用绑定
        self.Bind(wx.EVT_MENU, self.OnToggleSearch, searchItem)
        self.Bind(wx.EVT_MENU, self.OnFont, fontItem)
        
        self.PopupMenu(contextMenu)
        contextMenu.Destroy()
        

    # 基本文件功能
    def OnUndo(self,event):
        self.tc.Undo()
    def OnRedo(self,event):
        self.tc.Redo()
    def OnSelectAll(self,event):
        self.tc.SelectAll()
    def OnDelete(self,event):
        start, end = self.tc.GetSelection()
        self.tc.Remove(start, end)
    def OnCopy(self,event):
        self.tc.Copy()
        self.menuBar.FindItemById(wx.ID_PASTE).Enable(True)
    def OnPaste(self,event):
        self.tc.Paste()
    def OnCut(self,event):
        self.tc.Cut()
        self.menuBar.FindItemById(wx.ID_PASTE).Enable(True)
    def OnGoto(self,event):
        nowline = self.get_cursor_pos()[0]
        lines = len(self.tc.GetValue().split('\n'))
        dlg = GotoDialog(self, lines, nowline)
        if dlg.ShowModal() == wx.ID_OK:
            line_to_go = dlg.GetValue()
            pos = 0
            for i in range(line_to_go - 1):
                pos += len(lines[i]) + 1  # 加1是因为包括换行符

            self.tc.SetInsertionPoint(pos)
            self.tc.ShowPosition(pos)
            self.tc.SetFocus()
            dlg.Destroy()
    
    # 放大
    def OnZoomIn(self, event):
        font = self.tc.GetFont()
        font.SetPointSize(font.GetPointSize() + self.zoomFactor)
        self.tc.SetFont(font)

    # 缩小
    def OnZoomOut(self, event):
        font = self.tc.GetFont()
        font.SetPointSize(font.GetPointSize() - self.zoomFactor)
        self.tc.SetFont(font)

    # 重置
    def OnZoomReset(self, event):
        self.tc.SetFont(self.defaultFont)

    # 字体
    def OnFont(self, event):
        dialog = wx.FontDialog(self, wx.FontData())
        data = dialog.GetFontData()
        data.SetInitialFont(self.tc.GetFont())
        if dialog.ShowModal() == wx.ID_OK:
            font = data.GetChosenFont()
            color = data.GetColour()
            if self.selectedText == "":
                self.tc.SetFont(font)
                self.tc.SetForegroundColour(color)
                self.HaveEdited()
            else:
                start, end = self.tc.GetSelection()
                self.tc.SetStyle(start, end, wx.TextAttr(font=font, colText=color))
        dialog.Destroy()

    # 检测修改文件内容并改变标题
    def OnEdited(self, event):
        self.SetTitle("*" + self.path + " - 记事本")
        self.IsEdited = True
    
    def HaveEdited(self):
        self.IsEdited = False
        title = "无标题 - 记事本" if self.path == "无标题" else self.path + " - 记事本"
        self.SetTitle(title)

    def OnNew(self, event):
        if not self.SaveWarn(event):
                return
        self.tc.Clear()
        self.IsEdited = False
        self.path = "无标题"
        self.SetTitle("无标题 - 记事本")

    def SaveWarn(self, event):
        """
        Return False if the user cancels the save.
        """
        if not self.IsEdited:
            return True

        dlg = wx.MessageDialog(self, ' 是否将更改保存到'
            + self.path + '？\n\n ', '提示',
            wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
        )
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            self.OnSave(event)
            return True
        elif result == wx.ID_NO:
            return True
        else:  # result == wx.CANCEL
            return False

    def OnOpen(self, event):
        if not self.SaveWarn(event):
            return
        dlg = wx.FileDialog(self, "选择一个文件", wildcard="Text files (*.txt)|*.txt",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.path = dlg.GetPath()
            with open(self.path, 'r') as f:
                self.tc.SetValue(f.read())
            self.IsEdited = False
        dlg.Destroy()
        self.SetTitle(self.path + " - 记事本")
        
        # 过长文本自动开启自动换行
        if self.tc.GetWindowStyleFlag() & wx.TE_DONTWRAP:
            for line in range(1,self.tc.GetValue().count('\n') + 2):
                length = self.tc.GetLineLength(line - 1)
                if length >= self.autowraplength:
                    self.OnWrap(event)
                    dlg = wx.MessageDialog(self, f'第{line}行文本过长({length})，已自动开启自动换行！\n\n ', '提示')
                    dlg.ShowModal()
                    break
            

    def OnSave(self, event):
        if self.path == "无标题":
            self.OnSaveAs(event)
        else:
            with open(self.path, 'w') as f:
                f.write(self.tc.GetValue())
            self.HaveEdited()
            
    def OnSaveAs(self, event):
        dlg = wx.FileDialog(self, "选择一个文件", wildcard="Text files (*.txt)|*.txt",
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'w') as f:
                f.write(self.tc.GetValue())
            self.HaveEdited()
        dlg.Destroy()

    def OnAbout(self, event):
        dlg = AboutDialog()
        dlg.ShowModal()
        dlg.Destroy()
        
    # 关闭二次确认
    def OnClose(self, event):
        if self.SaveWarn(event):
            self.Destroy()

    def KeyMouseEvent(self, event):
        event.Skip()
        self.set_status_content()
        self.set_menu_item()
        
    def set_menu_item(self):
        if self.selectedText:
            self.MenuBar.FindItemById(wx.ID_CUT).Enable(True)
            self.MenuBar.FindItemById(wx.ID_COPY).Enable(True)
        else:
            self.MenuBar.FindItemById(wx.ID_CUT).Enable(False)
            self.MenuBar.FindItemById(wx.ID_COPY).Enable(False)
        
    # 获取光标位置
    # 根据换行符计算行数，显示真实行数列数
    def get_cursor_pos(self):
        '''
        Return (line, col) tuple of cursor position.
        '''
        pos = self.tc.GetInsertionPoint()  # 获得光标索引值
        text = self.tc.GetValue()[:pos]
        line = text.count('\n') + 1  # 计算行数
        
        last_newline_pos = text.rfind('\n')  # 上一个换行符的位置
        if last_newline_pos == -1:
            col = pos + 1  # 如果没有换行符，则为光标在当前行的位置加1
        else:
            col = pos - last_newline_pos # 否则为光标在当前行的位置

        return line, col

    def get_selected_text(self):
        if self.tc.GetSelection() == (0, 0):
            self.selectedText = ""
            self.selectedTextLength = 0
        else:
            self.selectedText = self.tc.GetStringSelection()
            self.selectedTextLength = len(self.selectedText)

    # 状态栏内容
    def set_status_content(self):
        line, col = self.get_cursor_pos()
        self.get_selected_text()
        cursor_info = (f"{line}:{col}") # 行数：列数
        if self.selectedTextLength != 0:
            selected_info = f"({self.selectedTextLength})"
            self.SetStatusText(f"{cursor_info} {selected_info}", 2)
        else:
            self.SetStatusText(f"{cursor_info}", 2)

    # 切换状态栏显示
    def OnShowStatus(self, event):
        if self.StatusBar.IsShown():
            self.StatusBar.Hide()
        else:
            self.set_status_content()
            self.StatusBar.Show()
        self.Layout()

    # 自动换行
    def OnWrap(self, event):
        tc_size = self.tc.GetSize()
        value = self.tc.GetValue()
        font = self.tc.GetFont()
        current_style = self.tc.GetWindowStyleFlag()
        current_index = 0 # 防止与自动换行的文本框位置冲突
        if current_style & wx.TE_DONTWRAP:
            new_style = current_style & ~wx.TE_DONTWRAP # 移除 TE_DONTWRAP 样式来启用自动换行
            self.wrapItem.Check(True)
        else:
            new_style = current_style | wx.TE_DONTWRAP # 添加 TE_DONTWRAP 样式来禁用自动换行
            self.wrapItem.Check(False)
        self.tc.Destroy()
        
        self.tc= wx.TextCtrl(self.pnl, -1, '', style=new_style)
        self.vbox.Insert(current_index, self.tc, 1, wx.EXPAND)
        self.pnl.SetSizer(self.vbox)
        self.tc.SetFont(font)
        self.tc.SetSize(tc_size)
        self.tc.SetFocus()

        if self.IsEdited: # 获取改变内容前的文件编辑状态
            self.tc.SetValue(value)
        else:
            self.tc.SetValue(value)
            self.HaveEdited()
        
        self.tc.Bind(wx.EVT_TEXT, self.OnEdited)
        self.tc.Bind(wx.EVT_KEY_UP, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_LEFT_UP,self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_MOTION, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_TEXT, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_KEY_DOWN, self.KeyMouseEvent)

    # 查找
    def OnSearch(self, event):
        text_to_find = self.searchCtrl.GetValue()
        self.clear_highlight()
        if text_to_find:
            flags = 0 if self.IsCaseSensitive else re.IGNORECASE # 区分大小写
            if self.IsRegexSearch:
                text_to_find = r'\b' + text_to_find + r'\b' if self.IsWholeWord else text_to_find # 全词匹配
                try:
                    self.matches = [match.span() for match in re.finditer(text_to_find, self.tc.GetValue(), flags)]
                except re.error:
                    self.matches = []
                    self.SetStatusText("正则表达式无效", 1)
                    return
            else:
                self.matches = [match.span() for match in re.finditer(re.escape(text_to_find), self.tc.GetValue(), flags)]

            num_matches = len(self.matches)
            
            if num_matches == 0:
                self.current_match_index = -1 # 如果当前没有匹配项，则重置索引
            elif num_matches > 0 and self.current_match_index == -1:
                self.current_match_index = 0 # 如果有匹配项但当前没有索引（初始时）设置索引为第一个匹配项
                # 这里保证了替换时位置不变
            
            if num_matches > 0:
                self.SetStatusText(f"1/{num_matches}个匹配", 1)
                self.highlight_all_matches()
                self.select_current_match()
            else:
                self.SetStatusText("0个匹配", 1)
                self.tc.SelectNone()
                self.tc.SetStyle(0, len(self.tc.GetValue()), wx.TextAttr(wx.NullColour, wx.WHITE))
        else:
            self.matches = []
            self.SetStatusText("", 1)
            self.tc.SelectNone()
            self.tc.SetStyle(0, len(self.tc.GetValue()), wx.TextAttr(wx.NullColour, wx.WHITE))
        self.set_status_content()

    # 跳转到上一个匹配项
    def OnPrevMatch(self, event):
        flags = 0 if self.IsCaseSensitive else re.IGNORECASE
        text_to_find = r'\b' + text_to_find + r'\b' if self.IsWholeWord else text_to_find
        try:
            self.matches = [match.span() for match in re.finditer(self.searchCtrl.GetValue(), self.tc.GetValue(), flags)]
        except re.error:
            self.matches = []
            self.SetStatusText("正则表达式无效", 1)
            return
        if self.matches:
            self.current_match_index = (self.current_match_index - 1) % len(self.matches)
            self.clear_highlight()
            self.highlight_all_matches()
            self.select_current_match()
            self.SetStatusText(f"{self.current_match_index + 1}/{len(self.matches)}个匹配", 1)

    # 跳转到下一个匹配项
    def OnNextMatch(self, event):
        flags = 0 if self.IsCaseSensitive else re.IGNORECASE
        text_to_find = r'\b' + text_to_find + r'\b' if self.IsWholeWord else text_to_find
        try:
            self.matches = [match.span() for match in re.finditer(self.searchCtrl.GetValue(), self.tc.GetValue(), flags)]
        except re.error:
            self.matches = []
            self.SetStatusText("正则表达式无效", 1)
            return
        if self.matches:
            self.current_match_index = (self.current_match_index + 1) % len(self.matches)
            self.clear_highlight()
            self.highlight_all_matches()
            self.select_current_match()
            self.SetStatusText(f"{self.current_match_index + 1}/{len(self.matches)}个匹配", 1)
    
    # 高亮所有匹配
    def highlight_all_matches(self):
        for start, end in self.matches:
            self.tc.SetStyle(start, end, wx.TextAttr(wx.NullColour, YELLOW))

    # 选中当前匹配项
    def select_current_match(self):
        if self.current_match_index != -1:
            try:
                start, end = self.matches[self.current_match_index]
            except IndexError: # 最后一个匹配项消失时前移一位
                self.current_match_index -= 1
                start, end = self.matches[self.current_match_index]
            self.tc.SetSelection(start, end)
            self.tc.SetStyle(start, end, wx.TextAttr(wx.NullColour, BLUE))
            self.tc.ShowPosition(start)

    # 清除多余高亮
    def clear_highlight(self):
        self.tc.SetStyle(0, len(self.tc.GetValue()), wx.TextAttr(wx.NullColour, wx.WHITE))

    # 替换
    def OnReplace(self, event):
        text_to_find = self.searchCtrl.GetValue()
        replace_text = self.replaceCtrl.GetValue()
        if self.current_match_index != -1 and self.matches:
            start, end = self.matches[self.current_match_index]
            current_text = self.tc.GetValue()[start:end]
            if self.IsRegexSearch:
                replace_text = self.fix_regex_capture_group(replace_text)
                flags = 0 if self.IsCaseSensitive else re.IGNORECASE
                text_to_find = r'\b' + text_to_find + r'\b' if self.IsWholeWord else text_to_find
                try:
                    new_text = re.sub(text_to_find, replace_text, current_text, flags=flags)
                except re.error:
                    self.SetStatusText("正则表达式无效", 1)
                    return
            else:
                new_text = replace_text
                
            #self.tc.SetSelection(start, end)
            self.tc.Replace(start, end, new_text)
            self.OnSearch(None)
            if self.matches:
                self.clear_highlight()
                self.highlight_all_matches()
                self.current_match_index = (self.current_match_index)# % len(self.matches)
                self.select_current_match()
        
    # 替换全部
    def OnReplaceAll(self, event):
        text_to_find = self.searchCtrl.GetValue()
        replace_text = self.replaceCtrl.GetValue()
        if text_to_find:
            current_pos = self.tc.GetInsertionPoint()
            if self.IsRegexSearch:
                replace_text = self.fix_regex_capture_group(replace_text)
                flags = 0 if self.IsCaseSensitive else re.IGNORECASE
                text_to_find = r'\b' + text_to_find + r'\b' if self.IsWholeWord else text_to_find
                try:
                    new_value = re.sub(text_to_find, replace_text, self.tc.GetValue(), flags=flags)
                except re.error:
                    self.SetStatusText("正则表达式无效", 1)
                    return
            else:
                new_value = re.sub(re.escape(text_to_find), replace_text, self.tc.GetValue())
            self.tc.SetValue(new_value)
            self.tc.SetInsertionPoint(current_pos)
            self.OnSearch(None)  

    # 正则引用捕获组修复(对查找无效)
    def fix_regex_capture_group(self, text_to_find):
        r'''\number -> \g<number>'''
        result =  re.sub(r'\\(\d)', r'\\g<\1>', text_to_find)
        return result
              
    # 切换查找
    def OnToggleSearch(self, event):
        if self.searchCtrl.IsShown():
            self.searchbox.ShowItems(False)
            self.clear_highlight()
            self.searchCtrl.SetFocus()
        else:
            def OnShowReplace(event):
                self.rbox.ShowItems(True)
                self.replaceBtn.Unbind(wx.EVT_BUTTON, handler=OnShowReplace)
                self.replaceBtn.Bind(wx.EVT_BUTTON, self.OnReplace)
                self.replaceAllBtn.Enable(True)
                self.pnl.Layout()
            self.searchbox.ShowItems(True)
            self.rbox.ShowItems(False)
            self.replaceAllBtn.Enable(False)
            self.replaceBtn.Unbind(wx.EVT_BUTTON, handler=self.OnReplace)
            self.replaceBtn.Bind(wx.EVT_BUTTON, OnShowReplace)
            self.searchCtrl.SetFocus()
        self.pnl.Layout()


    # 切换替换
    def OnToggleReplace(self, event):
        if self.replaceCtrl.IsShown():
            self.searchbox.ShowItems(False)
            self.replaceCtrl.SetFocus()
        else:
            self.replaceAllBtn.Enable(True)
            self.replaceBtn.Bind(wx.EVT_BUTTON, self.OnReplace)
            self.searchbox.ShowItems(True)
        self.pnl.Layout()

    # 切换区分大小写
    def OnToggleCase(self, event):
        self.IsCaseSensitive = not self.IsCaseSensitive
        if self.IsCaseSensitive:
            self.caseBtn.SetBackgroundColour(BLUE)
        else:
            self.caseBtn.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.OnSearch(None)
    
    # 切换全词匹配
    def OnToggleWord(self, event):
        self.IsWholeWord = not self.IsWholeWord
        if self.IsWholeWord:
            self.wordBtn.SetBackgroundColour(BLUE)
        else:
            self.wordBtn.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.OnSearch(None)
    
    # 切换正则搜索
    def OnToggleRegex(self, event):
        self.IsRegexSearch = not self.IsRegexSearch
        if self.IsRegexSearch:
            self.regexBtn.SetBackgroundColour(BLUE)
        else:
            self.regexBtn.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.OnSearch(None)



class GotoDialog(wx.Dialog):
    def __init__(self, parent, lines, nowline):
        wx.Dialog.__init__(self, None, -1, "转到", size=(250, 150))
        self.nowline = nowline
        self.lines = lines
        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        st_line = wx.StaticText(self, label=f"行号：(1..{self.lines})")
        vbox.Add(st_line, flag=wx.ALL | wx.ALIGN_LEFT, border=10)
        self.line_input = wx.TextCtrl(self, -1, str(self.nowline), style=wx.TE_PROCESS_ENTER)
        vbox.Add(self.line_input, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(self, label="确定")
        btn_cancel = wx.Button(self, label="取消")
        hbox.Add(btn_ok)
        hbox.Add(btn_cancel, flag=wx.LEFT, border=5)
        vbox.Add(hbox, flag=wx.ALIGN_RIGHT | wx.TOP | wx.BOTTOM | wx.RIGHT, border=10)
        self.SetSizer(vbox)

        btn_ok.Bind(wx.EVT_BUTTON, self.OnOK)
        btn_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        self.line_input.Bind(wx.EVT_TEXT_ENTER, self.OnOK)

    def GetValue(self):
        return int(self.line_input.GetValue())

    def OnOK(self, event):
        line_num = self.line_input.GetValue()
        if line_num.isdigit():
            line_to_go = int(line_num)
            if line_to_go > 0 and line_to_go <= self.lines:
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox("请输入有效的行号", "错误", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("请输入有效的行号", "错误", wx.OK | wx.ICON_ERROR)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)
    


class AboutDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None,-1, title="关于",size=(300, 200))
        self.OKBtn = wx.Button(self,-1,"确定",pos=(100,90))
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        st = wx.StaticText(self, label="Notepad-wxpython")
        vbox.Add(st, 0, wx.TOP|wx.LEFT, 15)
        st.SetFont(wx.Font(12,wx.DEFAULT,wx.NORMAL,wx.NORMAL,False,"微软雅黑"))
        st.SetForegroundColour(wx.Colour(0,51,158))
        st = wx.StaticText(self, label="by z7572\n在以下平台灌注我！")
        vbox.Add(st, 1, wx.LEFT, 15)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(hbox, 0, wx.CENTER)
        
        for icon in ["github","bilibili","x","telegram"]:
            path = os.path.join(os.path.dirname(__file__), "res", icon + ".ico")
            ico = wx.Bitmap(path,wx.BITMAP_TYPE_ICO)
            btn = wx.BitmapButton(self, -1, ico, size=(32, 32))
            btn.SetWindowStyle(wx.BORDER_NONE)
            hbox.Add(btn, 0, wx.ALL, 18)
            btn.Bind(wx.EVT_BUTTON, self.OnIconClick(icon)) # 给出返回值，不是绑定函数

        self.SetSizer(vbox)
        self.OKBtn.Bind(wx.EVT_MOUSE_EVENTS, self.OnMove)
        self.OKBtn.Bind(wx.EVT_MOUSE_CAPTURE_CHANGED, self.OnMove)
        self.OKBtn.Bind(wx.EVT_BUTTON, self.OnOK, self.OKBtn)

    def OnIconClick(self, icon):
        def handler(event): # 所以需要闭包函数，实现函数传参
            if icon == "github":
                webbrowser.open("https://github.com/zjx7572/notepad-wxpython")
            elif icon == "bilibili":
                webbrowser.open("https://b23.tv/YbNLXsS")
            elif icon == "x":
                webbrowser.open("https://x.com/z7572_")
            elif icon == "telegram":
                webbrowser.open("https://t.me/z_7572")
        return handler # 返回值是函数体

    # 「ゴールド・エクスペリエンス・レクイエム」！你永远无法到达点到按钮的真实！
    def OnMove(self, event):
        import random
        x ,y = self.OKBtn.GetPosition()
        self.OKBtn.SetPosition(
            (x + random.randint(-20, 20), y + random.randint(-20, 20)))
        # 超出边界后从另一侧返回
        x ,y = self.OKBtn.GetPosition()
        if x < 0:
            self.OKBtn.SetPosition((250, y))
        elif x > 250:
            self.OKBtn.SetPosition((0, y))
        if y < 0:
            self.OKBtn.SetPosition((x, 150))
        elif y > 150:
            self.OKBtn.SetPosition((x, 0))
        event.Skip()
    def OnOK(self, event):
        self.Close()

if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame(None, title="无标题 - 记事本")
    frame.SetSize((720, 480))
    frame.Show()
    app.MainLoop()
