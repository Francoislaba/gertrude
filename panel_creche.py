# -*- coding: cp1252 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, write to the Free Software
##    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os.path
import datetime
from common import *
from gpanel import GPanel
from controls import *

class CrecheTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
        sizer2.AddGrowableCol(1, 1)
        sizer2.AddMany([wx.StaticText(self, -1, u'Nom de la cr�che :'), (AutoTextCtrl(self, creche, 'nom'), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Adresse :'), (AutoTextCtrl(self, creche, 'adresse'), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Code Postal :'), (AutoNumericCtrl(self, creche, 'code_postal', precision=0), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Ville :'), (AutoTextCtrl(self, creche, 'ville'), 0, wx.EXPAND)])       
        sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)

class EmployesTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.employes_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, employe in enumerate(creche.employes):
            self.display_employe(i)
        self.sizer.Add(self.employes_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvel employ�')
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.employe_add, button_add)
        self.SetSizer(self.sizer)

    def display_employe(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Pr�nom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, creche, 'employes[%d].prenom' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, creche, 'employes[%d].nom' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Arriv�e :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoDateCtrl(self, creche, 'employes[%d].date_embauche' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Domicile :"), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoPhoneCtrl(self, creche, 'employes[%d].telephone_domicile' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Portable :"), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoPhoneCtrl(self, creche, 'employes[%d].telephone_portable' % index), 1, wx.EXPAND)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.employe_del, delbutton)
        self.employes_sizer.Add(sizer, 0, wx.EXPAND)

    def employe_add(self, event):
        creche.employes.append(Employe())
        self.display_employe(len(creche.employes) - 1)
        self.sizer.Layout()

    def employe_del(self, event):
        index = event.GetEventObject().index
        sizer = self.employes_sizer.GetItem(len(creche.employes)-1)
        sizer.DeleteWindows()
        self.employes_sizer.Detach(len(creche.employes)-1)
        creche.employes[index].delete()
        del creche.employes[index]
        self.sizer.Layout()
        self.UpdateContents()
        
class ResponsabilitesTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        parents = self.GetNomsParents()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, creche, 'bureaux', Bureau), 0, wx.TOP, 5)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
        sizer2.AddGrowableCol(1, 1)
        self.responsables_ctrls = []
        self.responsables_ctrls.append(AutoChoiceCtrl(self, creche, 'bureaux[self.parent.periode].president', items=parents))
        sizer2.AddMany([wx.StaticText(self, -1, u'Pr�sident :'), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, creche, 'bureaux[self.parent.periode].vice_president', items=parents))
        sizer2.AddMany([wx.StaticText(self, -1, u'Vice pr�sident :'), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, creche, 'bureaux[self.parent.periode].tresorier', items=parents))
        sizer2.AddMany([wx.StaticText(self, -1, u'Tr�sorier :'), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, creche, 'bureaux[self.parent.periode].secretaire', items=parents))        
        sizer2.AddMany([wx.StaticText(self, -1, u'Secr�taire :'), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
        sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        parents = self.GetNomsParents()
        for ctrl in self.responsables_ctrls:
            ctrl.SetItems(parents)
        AutoTab.UpdateContents(self)

    def GetNomsParents(self):
        result = []
        parents = []
        for inscrit in creche.inscrits:
            for parent in (inscrit.papa, inscrit.maman):
                if parent.prenom and parent.nom:
                    tmp = parent.prenom + ' ' + parent.nom
                    if not tmp in parents:
                        parents.append(tmp)
                        result.append((tmp, parent))
        result.sort(cmp=lambda x,y: cmp(x[0].lower(), y[0].lower()))
        return result

class CafTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, creche, 'baremes_caf', BaremeCAF), 0, wx.TOP, 5)
        sizer2 = wx.FlexGridSizer(4, 2, 5, 5)
        sizer2.AddMany([wx.StaticText(self, -1, 'Plancher :'), AutoNumericCtrl(self, creche, 'baremes_caf[self.parent.periode].plancher', precision=2)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Plafond :'), AutoNumericCtrl(self, creche, 'baremes_caf[self.parent.periode].plafond', precision=2)])
        sizer.Add(sizer2, 0, wx.ALL, 5)
        sizer.Fit(self)
        self.SetSizer(sizer)
        
class GeneralNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(CrecheTab(self), u'Cr�che')
        self.AddPage(EmployesTab(self), u'Employ�s')
        self.AddPage(ResponsabilitesTab(self), u'Responsabilit�s')
        self.AddPage(CafTab(self), 'C.A.F.')        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanged(self, event):
        page = self.GetPage(event.GetSelection())
        page.UpdateContents()
        event.Skip()

    def UpdateContents(self):
        page = self.GetCurrentPage()
        page.UpdateContents()
     
class CrechePanel(GPanel):
    bitmap = './bitmaps/creche.png'
    index = 50
    profil = PROFIL_BUREAU
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Cr�che')
        self.notebook = GeneralNotebook(self)
	self.sizer.Add(self.notebook, 1, wx.EXPAND)
            
    def UpdateContents(self):
        self.notebook.UpdateContents()

panels = [CrechePanel]
