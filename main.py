'''
TODO:
    查找 正则搜索 替换 (√)
    显示行号 ( )
    Ctrl+ZYACVX (√)
    右键菜单(字体，查找) ( )
'''

import wx
import wx.richtext
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
        self.selectedText = ""
        self.selectedTextLength = 0
        self.matches = []  # 存储所有匹配项的位置
        self.current_match_index = -1  # 当前选中的匹配项索引
        self.IsRegexSearch = False # 正则搜索开关

    def InitUI(self):

        self.tc = wx.TextCtrl(self.pnl, -1 , '',
            style=wx.TE_DONTWRAP | wx.TE_MULTILINE | wx.TE_RICH)

        self.tc.Bind(wx.EVT_TEXT, self.OnEdited)
        self.tc.Bind(wx.EVT_KEY_UP, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_LEFT_UP,self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_MOTION, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_TEXT, self.KeyMouseEvent)
        self.tc.Bind(wx.EVT_KEY_DOWN, self.KeyMouseEvent)
        
        # 菜单栏
        self.makeMenuBar()
        
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetFieldsCount(3)
        self.statusBar.SetStatusWidths([-1, 100, 100])
        self.SetStatusContent()
        
        # 布局
        # vbox(tc,searchbox(sbox,rbox,bbox))
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.searchbox = wx.BoxSizer(wx.VERTICAL)
        
        sbox = wx.BoxSizer(wx.HORIZONTAL)
        self.rbox = wx.BoxSizer(wx.HORIZONTAL)
        self.bbox = wx.BoxSizer(wx.HORIZONTAL)
        
        self.searchbox.Add(sbox, 0, wx.EXPAND)
        self.searchbox.Add(self.rbox, 0, wx.EXPAND)
        self.searchbox.Add(self.bbox, 0, wx.EXPAND)
        
        self.vbox.Add(self.tc, 1, wx.EXPAND)
        self.vbox.Add(self.searchbox, 0, wx.EXPAND)
        
        st = wx.StaticText(self.pnl, -1, '查找')
        sbox.Add(st, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        
        self.searchCtrl = wx.TextCtrl(self.pnl, -1, '', style=wx.TE_PROCESS_ENTER)
        sbox.Add(self.searchCtrl, 1, wx.ALL, 5)
        
        st = wx.StaticText(self.pnl, -1, '替换')
        self.rbox.Add(st, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        
        self.replaceCtrl = wx.TextCtrl(self.pnl, -1, '', style=wx.TE_PROCESS_ENTER)
        self.rbox.Add(self.replaceCtrl, 1, wx.ALL, 5)
        
        self.prevBtn = wx.Button(self.pnl, -1, '上个')
        self.bbox.Add(self.prevBtn, 1, wx.ALIGN_LEFT | wx.ALL, 5)
        self.nextBtn = wx.Button(self.pnl, -1, '下个')
        self.bbox.Add(self.nextBtn, 1, wx.ALIGN_LEFT | wx.ALL, 5)
        self.replaceBtn = wx.Button(self.pnl, -1, '替换')
        self.bbox.Add(self.replaceBtn, 1, wx.ALIGN_LEFT | wx.ALL, 5)
        self.replaceAllBtn = wx.Button(self.pnl, -1, '全部')
        self.bbox.Add(self.replaceAllBtn, 1, wx.ALIGN_LEFT | wx.ALL, 5)
        self.regexBtn = wx.Button(self.pnl, -1, '.*', size=(25, 25))
        self.regexBtn.SetToolTip('正则表达式 (Alt+R)')
        self.bbox.Add(self.regexBtn, 0, wx.ALIGN_LEFT | wx.TOP, 5)
        self.closeBtn = wx.Button(self.pnl, -1, '✘', size=(25, 25))
        self.bbox.Add(self.closeBtn, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        
        Btns = [self.prevBtn, self.nextBtn, self.replaceBtn,
                self.replaceAllBtn, self.regexBtn, self.closeBtn]
        for btn in Btns:
            btn.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        
        self.searchCtrl.Bind(wx.EVT_TEXT,self.OnSearch)
        self.searchCtrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.prevBtn.Bind(wx.EVT_BUTTON, self.OnPrevMatch)
        self.nextBtn.Bind(wx.EVT_BUTTON, self.OnNextMatch)
        self.replaceBtn.Bind(wx.EVT_BUTTON, self.OnReplace)
        self.replaceAllBtn.Bind(wx.EVT_BUTTON, self.OnReplaceAll)
        self.regexBtn.Bind(wx.EVT_BUTTON, self.OnToggleRegex)
        self.closeBtn.Bind(wx.EVT_BUTTON, self.OnToggleSearch)
        self.pnl.SetSizer(self.vbox)
        
        # 快捷键绑定
        self.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('R'), self.regexBtn.GetId()),
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
        selectallItem = editMenu.Append(wx.ID_SELECTALL, '全选(&A)\tCtrl+A')
        copyItem = editMenu.Append(wx.ID_COPY, '复制(&C)\tCtrl+C')
        pasteItem = editMenu.Append(wx.ID_PASTE, '粘贴(&P)\tCtrl+V')
        cutItem = editMenu.Append(wx.ID_CUT, '剪切(&T)\tCtrl+X')
        editMenu.AppendSeparator()
        searchItem = editMenu.Append(-1, '查找(&F)\tCtrl+F')
        replaceItem = editMenu.Append(-1, '替换(&R)\tCtrl+H')
        gotoItem = editMenu.Append(-1, '转到(&G)\tCtrl+G')
        
        pasteItem.Enable(False) # 禁用粘贴菜单项
        cutItem.Enable(False) # 禁用剪切菜单项
        copyItem.Enable(False) # 禁用复制菜单项
        
        self.Bind(wx.EVT_MENU, self.OnUndo, undoItem)
        self.Bind(wx.EVT_MENU, self.OnRedo, redoItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAll, selectallItem)
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

    # 基本文件功能
    def OnUndo(self,event):
        self.tc.Undo()
    def OnRedo(self,event):
        self.tc.Redo()
    def OnSelectAll(self,event):
        self.tc.SelectAll()
    def OnCopy(self,event):
        self.tc.Copy()
        self.menuBar.FindItemById(wx.ID_PASTE).Enable(True)
    def OnPaste(self,event):
        self.tc.Paste()
    def OnCut(self,event):
        self.tc.Cut()
        self.menuBar.FindItemById(wx.ID_PASTE).Enable(True)
    def OnDelete(self,event):
        pass
    def OnGoto(self,event):
        pass
    
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
        self.SetStatusContent()
        self.SetMenuItem()
        
    def SetMenuItem(self):
        if self.selectedText:
            self.MenuBar.FindItemById(wx.ID_CUT).Enable(True)
            self.MenuBar.FindItemById(wx.ID_COPY).Enable(True)
        else:
            self.MenuBar.FindItemById(wx.ID_CUT).Enable(False)
            self.MenuBar.FindItemById(wx.ID_COPY).Enable(False)
        
    # 获取光标位置
    # 根据换行符计算行数，显示真实行数列数
    def GetCursorPos(self):
        pos = self.tc.GetInsertionPoint()  # 获得光标索引值
        text = self.tc.GetValue()[:pos]
        line = text.count('\n') + 1  # 计算行数
        
        last_newline_pos = text.rfind('\n')  # 上一个换行符的位置
        if last_newline_pos == -1:
            col = pos + 1  # 如果没有换行符，则为光标在当前行的位置加1
        else:
            col = pos - last_newline_pos # 否则为光标在当前行的位置

        return line, col

    def GetSelectedText(self):
        if self.tc.GetSelection() == (0, 0):
            self.selectedText = ""
            self.selectedTextLength = 0
        else:
            self.selectedText = self.tc.GetStringSelection()
            self.selectedTextLength = len(self.selectedText)

    # 状态栏内容
    def SetStatusContent(self):
        line, col = self.GetCursorPos()
        self.GetSelectedText()
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
            self.SetStatusContent()
            self.StatusBar.Show()
        self.Layout()

    # 自动换行
    def OnWrap(self, event):
        tc_size = self.tc.GetSize()
        value = self.tc.GetValue()
        font = self.tc.GetFont()
        current_style = self.tc.GetWindowStyleFlag()
        if current_style & wx.TE_DONTWRAP:
            new_style = current_style & ~wx.TE_DONTWRAP # 移除 TE_DONTWRAP 样式来启用自动换行
        else:
            new_style = current_style | wx.TE_DONTWRAP # 添加 TE_DONTWRAP 样式来禁用自动换行
        self.tc.Destroy()
        
        self.tc= wx.TextCtrl(self.pnl, -1, '', style=new_style)
        self.vbox.Add(self.tc, 1, wx.EXPAND)
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
            if self.IsRegexSearch:
                try:
                    self.matches = [match.span() for match in re.finditer(text_to_find, self.tc.GetValue())]
                except re.error:
                    self.matches = []
                    self.SetStatusText("正则表达式无效", 1)
                    return
            else:
                self.matches = [match.span() for match in re.finditer(re.escape(text_to_find), self.tc.GetValue())]

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
        self.SetStatusContent()

    # 跳转到上一个匹配项
    # (已修复): 输入新内容时不能正确循环滚动
    def OnPrevMatch(self, event):
        try:
            self.matches = [match.span() for match in re.finditer(self.searchCtrl.GetValue(), self.tc.GetValue())]
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
            self.select_current_match()

    # 跳转到下一个匹配项
    def OnNextMatch(self, event):
        try:
            self.matches = [match.span() for match in re.finditer(self.searchCtrl.GetValue(), self.tc.GetValue())]
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
            start, end = self.matches[self.current_match_index]
            self.tc.SetSelection(start, end)
            self.tc.SetStyle(start, end, wx.TextAttr(wx.NullColour, BLUE))
            self.tc.ShowPosition(start)

    # 清除多余高亮
    def clear_highlight(self):
        self.tc.SetStyle(0, len(self.tc.GetValue()), wx.TextAttr(wx.NullColour, wx.WHITE))

    # 替换
    # (已修复): 替换后固定选中第二个匹配项而不是当前匹配项
    def OnReplace(self, event):
        replace_text = self.replaceCtrl.GetValue()
        text_to_find = self.searchCtrl.GetValue()
        if self.current_match_index != -1 and self.matches:
            start, end = self.matches[self.current_match_index]
            current_text = self.tc.GetValue()[start:end]
            if self.IsRegexSearch:
                try:
                    new_text = re.sub(text_to_find, replace_text, current_text)
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
                try:
                    new_value = re.sub(text_to_find, replace_text, self.tc.GetValue())
                except re.error:
                    self.SetStatusText("正则表达式无效", 1)
                    return
            else:
                new_value = re.sub(re.escape(text_to_find), replace_text, self.tc.GetValue())
            self.tc.SetValue(new_value)
            self.tc.SetInsertionPoint(current_pos)
            self.OnSearch(None)  
              
    # 切换搜索
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

    # 切换正则搜索
    def OnToggleRegex(self, event):
        if self.regexBtn.GetBackgroundColour() == BLUE:
            self.regexBtn.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            self.IsRegexSearch = False
        else:
            self.regexBtn.SetBackgroundColour(BLUE)
            self.IsRegexSearch = True
        self.OnSearch(None)



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
