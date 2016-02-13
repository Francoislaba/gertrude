# -*- coding: utf-8 -*-

#    This file is part of Gertrude.
#
#    Gertrude is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    Gertrude is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

import datetime
from globals import *
from constants import *
from parameters import *
from functions import *
from sqlobjects import *
from controls import *
from planning import PlanningWidget, LigneConge, COMMENTS, ACTIVITES, TWO_PARTS, DEPASSEMENT_CAPACITE, SUMMARY_ENFANT, SUMMARY_SALARIE
from ooffice import *
from doc_planning_detaille import PlanningDetailleModifications

TABLETTE_MARGE_ARRIVEE = 10


class DayPlanningPanel(PlanningWidget):
    def __init__(self, parent, activity_combobox):
        PlanningWidget.__init__(self, parent, activity_combobox, COMMENTS|ACTIVITES|TWO_PARTS|DEPASSEMENT_CAPACITE, self.CheckLine)

    def CheckLine(self, line, plages_selectionnees):
        lines = self.GetSummaryLines()
        activites, activites_sans_horaires = GetActivitiesSummary(creche, lines)
        for start, end in plages_selectionnees:
            for i in range(start, end):
                if activites[0][i][0] > creche.GetCapacite(line.day):
                    dlg = wx.MessageDialog(None, u"Dépassement de la capacité sur ce créneau horaire !", u"Attention", wx.OK|wx.ICON_WARNING)
                    dlg.ShowModal()
                    dlg.Destroy()
                    self.state = None
                    return

    def UpdateContents(self):
        if self.date in creche.jours_fermeture:
            conge = creche.jours_fermeture[self.date]
            if conge.options == ACCUEIL_NON_FACTURE:
                self.SetInfo(conge.label)
            else:
                if conge.label:
                    self.Disable(conge.label)
                else:
                    self.Disable(u"Etablissement fermé")
                return
        else:
            self.SetInfo("")

        self.lignes_enfants = []
        for inscrit in creche.inscrits:
            inscription = inscrit.GetInscription(self.date)
            if inscription is not None and (len(creche.sites) <= 1 or inscription.site is self.site) and (self.groupe is None or inscription.groupe == self.groupe):
                if creche.conges_inscription == GESTION_CONGES_INSCRIPTION_SIMPLE and self.date in inscrit.jours_conges:
                    line = LigneConge(inscrit.jours_conges[self.date].label)
                elif self.date in inscrit.journees:
                    line = inscrit.journees[self.date]
                    if creche.conges_inscription == GESTION_CONGES_INSCRIPTION_AVEC_SUPPLEMENT and self.date in inscrit.jours_conges:
                        line.reference = JourneeReferenceInscription(None, 0)
                        if not line.commentaire:
                            line.commentaire = inscrit.jours_conges[self.date].label
                    else:
                        line.reference = inscription.GetJourneeReference(self.date)
                    line.insert = None
                    line.key = self.date
                elif creche.conges_inscription == GESTION_CONGES_INSCRIPTION_AVEC_SUPPLEMENT and self.date in inscrit.jours_conges:
                    reference = JourneeReferenceInscription(None, 0)
                    line = Journee(inscrit, self.date, reference)
                    line.reference = reference
                    line.commentaire = inscrit.jours_conges[self.date].label
                    line.insert = inscrit.journees
                    line.key = self.date
                else:
                    line = inscription.GetJourneeReferenceCopy(self.date)
                    line.reference = inscription.GetJourneeReference(self.date)
                    line.insert = inscrit.journees
                    line.key = self.date

                line.label = GetPrenomNom(inscrit)
                line.sublabel = ""
                line.inscription = inscription
                line.options |= COMMENTS | ACTIVITES
                line.summary = SUMMARY_ENFANT

                def GetHeuresEnfant(line):
                    heures = line.GetNombreHeures()
                    if line.reference:
                        heures_reference = line.reference.GetNombreHeures()
                    else:
                        heures_reference = 0
                    if heures > 0 or heures_reference > 0:
                        return GetHeureString(heures) + '/' + GetHeureString(heures_reference)
                    else:
                        return None

                line.GetDynamicText = GetHeuresEnfant
                if creche.temps_facturation == FACTURATION_FIN_MOIS:
                    date = GetMonthStart(self.date)
                else:
                    date = GetNextMonthStart(self.date)
                if date in inscrit.factures_cloturees:
                    line.readonly = True
                line.day = self.date.weekday()
                self.lignes_enfants.append(line)

        if creche.tri_planning & TRI_GROUPE:
            self.lignes_enfants = GetEnfantsTriesParGroupe(self.lignes_enfants)
        else:
            self.lignes_enfants.sort(key=lambda line: line.label)

        self.lignes_salaries = []
        for salarie in creche.salaries:
            contrat = salarie.GetContrat(self.date)
            if contrat is not None and (len(creche.sites) <= 1 or contrat.site is self.site):
                if self.date in salarie.journees:
                    line = salarie.journees[self.date]
                    line.reference = contrat.GetJourneeReference(self.date)
                    line.insert = None
                else:
                    line = contrat.GetJourneeReferenceCopy(self.date)
                    line.insert = salarie.journees
                    line.key = self.date
                line.salarie = salarie
                line.label = GetPrenomNom(salarie)
                line.options |= COMMENTS
                line.sublabel = contrat.fonction
                line.contrat = contrat
                line.day = self.date.weekday()

                def GetHeuresSalarie(line):
                    debut_semaine = line.date - datetime.timedelta(line.date.weekday())
                    fin_semaine = debut_semaine + datetime.timedelta(6)
                    debut_mois = GetMonthStart(line.date)
                    fin_mois = GetMonthEnd(line.date)
                    heures_semaine = 0
                    heures_mois = 0
                    date = min(debut_semaine, debut_mois)
                    fin = max(fin_semaine, fin_mois)
                    while date <= fin_mois:
                        if date in line.salarie.journees:
                            heures = line.salarie.journees[date].GetNombreHeures()
                        else:
                            heures = line.contrat.GetJourneeReference(date).GetNombreHeures()
                        if date == line.date:
                            heures_jour = heures
                        if debut_semaine <= date <= fin_semaine:
                            heures_semaine += heures
                        if date.month == line.date.month:
                            heures_mois += heures
                        date += datetime.timedelta(1)
                    return GetHeureString(heures_jour) + '/' + GetHeureString(heures_semaine) + '/' + GetHeureString(heures_mois)

                line.GetDynamicText = GetHeuresSalarie
                line.summary = SUMMARY_SALARIE
                self.lignes_salaries.append(line)
        self.lignes_salaries.sort(key=lambda line: line.label)

        lines = self.lignes_enfants[:]
        if self.lignes_salaries:
            lines.append(u"Salariés")
            lines += self.lignes_salaries
        self.SetLines(lines)

    def GetSummaryDynamicText(self):
        heures = 0.0
        for line in self.lignes_enfants:
            if not isinstance(line, basestring):
                heures += line.GetNombreHeures()
                day = line.day

        if heures > 0:
            text = GetHeureString(heures)
            if self.site:
                den = self.site.capacite * creche.GetAmplitudeHoraire()
            else:
                den = creche.GetHeuresAccueil(day)
            if den > 0:
                text += " /  %.1f%%" % (heures * 100 / den)
            return text
        else:
            return None

    def SetData(self, site, groupe, date):
        self.site = site
        self.groupe = groupe
        self.date = date
        self.UpdateContents()


class PlanningBasePanel(GPanel):
    name = "Planning"
    bitmap = GetBitmapFile("planning.png")
    profil = PROFIL_ALL

    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Planning')
        self.topsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.current_site = 0

        # La combobox pour la selection du site
        self.site_choice = wx.Choice(self, -1)
        for site in creche.sites:
            self.site_choice.Append(site.nom, site)
        self.topsizer.Add(self.site_choice, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.RIGHT, 5)
        if len(creche.sites) < 2:
            self.site_choice.Show(False)
        self.site_choice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnChangementSemaine, self.site_choice)

        # Les raccourcis pour semaine précédente / suivante
        self.previous_button = wx.Button(self, -1, '<', size=(20,0), style=wx.NO_BORDER)
        self.next_button = wx.Button(self, -1, '>', size=(20,0), style=wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self.OnPreviousWeek, self.previous_button)
        self.Bind(wx.EVT_BUTTON, self.OnNextWeek, self.next_button)
        self.topsizer.Add(self.previous_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        self.topsizer.Add(self.next_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

        # La combobox pour la selection de la semaine
        self.week_choice = wx.Choice(self, -1)
        self.topsizer.Add(self.week_choice, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT, 5)
        AddWeeksToChoice(self.week_choice)
        self.Bind(wx.EVT_CHOICE, self.OnChangementSemaine, self.week_choice)

        # La combobox pour la selection du groupe (si groupes)
        self.groupe_choice = wx.Choice(self, -1)
        self.topsizer.Add(self.groupe_choice, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.Bind(wx.EVT_CHOICE, self.OnChangeGroupeDisplayed, self.groupe_choice)
        self.UpdateGroupeCombobox()

        self.sizer.Add(self.topsizer, 0, wx.EXPAND)

    def GetSelectionStart(self):
        selection = self.week_choice.GetSelection()
        return self.week_choice.GetClientData(selection)

    def UpdateGroupeCombobox(self):
        if len(creche.groupes) > 0:
            self.groupe_choice.Clear()
            for groupe, value in [("Tous groupes", None)] + [(groupe.nom, groupe) for groupe in creche.groupes]:
                self.groupe_choice.Append(groupe, value)
            self.groupe_choice.SetSelection(0)
            self.groupe_choice.Show(True)
        else:
            self.groupe_choice.Show(False)
        self.groupes_observer = counters['groupes']

    def OnPreviousWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() - 1)
        self.OnChangementSemaine()

    def OnNextWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() + 1)
        self.OnChangementSemaine()

    def OnChangeGroupeDisplayed(self, evt):
        self.OnChangementSemaine()

    def GetSelectedSite(self):
        if len(creche.sites) > 1:
            self.current_site = self.site_choice.GetSelection()
            return self.site_choice.GetClientData(self.current_site)
        else:
            return None

    def GetSelectedGroupe(self):
        if len(creche.groupes) > 1:
            selection = self.groupe_choice.GetSelection()
            return self.groupe_choice.GetClientData(selection)
        else:
            return None


class PlanningHorairePanel(PlanningBasePanel):
    def __init__(self, parent):
        PlanningBasePanel.__init__(self, parent)

        # La combobox pour la selection de l'outil (si activités)
        self.activity_choice = ActivityComboBox(self)
        self.topsizer.Add(self.activity_choice, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)

        # Le bouton d'impression
        bmp = wx.Bitmap(GetBitmapFile("printer.png"), wx.BITMAP_TYPE_PNG)
        button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
        self.topsizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.OnPrintPlanning, button)

        # Le bouton de synchro tablette
        if config.options & TABLETTE:
            bmp = wx.Bitmap(GetBitmapFile("tablette.png"), wx.BITMAP_TYPE_PNG)
            button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
            self.topsizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.OnTabletteSynchro, button)

        # Le notebook pour les jours de la semaine
        self.notebook = wx.Notebook(self, style=wx.LB_DEFAULT)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        first_monday = GetFirstMonday()
        delta = datetime.date.today() - first_monday
        semaine = int(delta.days / 7)
        for week_day in range(7):
            if IsJourSemaineTravaille(week_day):
                date = first_monday + datetime.timedelta(semaine * 7 + week_day)
                planning_panel = DayPlanningPanel(self.notebook, self.activity_choice)
                self.notebook.AddPage(planning_panel, GetDateString(date))
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnChangementSemaineday, self.notebook)
        self.sizer.Layout()

    def OnPrintPlanning(self, evt):
        site = self.GetSelectedSite()
        groupe = self.GetSelectedGroupe()
        start = self.GetSelectionStart()
        end = start + datetime.timedelta(6)
        DocumentDialog(self, PlanningDetailleModifications((start, end), site, groupe)).ShowModal()

    def OnChangementSemaineday(self, evt=None):
        self.notebook.GetCurrentPage().UpdateContents()

    def OnChangementSemaine(self, evt=None):
        self.UpdateWeek()
        self.notebook.SetSelection(0)
        self.sizer.Layout()

    def UpdateWeek(self):
        site = self.GetSelectedSite()
        groupe = self.GetSelectedGroupe()

        week_selection = self.week_choice.GetSelection()
        self.previous_button.Enable(week_selection is not 0)
        self.next_button.Enable(week_selection is not self.week_choice.GetCount() - 1)
        monday = self.week_choice.GetClientData(week_selection)
        page_index = 0
        for week_day in range(7):
            if IsJourSemaineTravaille(week_day):
                day = monday + datetime.timedelta(week_day)
                self.notebook.SetPageText(page_index, GetDateString(day))
                note = self.notebook.GetPage(page_index)
                note.SetData(site, groupe, day)
                page_index += 1

    def OnTabletteSynchro(self, evt):
        journal = config.connection.LoadJournal()

        def AddPeriodes(who, date, periodes, classeJournee):
            if date in who.journees:
                who.journees[date].RemoveActivities(0)
                who.journees[date].RemoveActivities(0 | PREVISIONNEL)
            else:
                who.journees[date] = classeJournee(who, date)
            for periode in periodes:
                AddPeriode(who, who.journees[date], periode)

        def AddPeriode(who, journee, periode):
            value = 0
            if periode.absent:
                value = VACANCES
            elif periode.malade:
                value = MALADE
            elif not periode.arrivee:
                errors.append(u"%s : Pas d'arrivée enregistrée le %s" % (GetPrenomNom(who), periode.date))
                periode.arrivee = int(creche.ouverture*(60 / BASE_GRANULARITY))
            elif not periode.depart:
                errors.append(u"%s : Pas de départ enregistré le %s" % (GetPrenomNom(who), periode.date))
                periode.depart = int(creche.fermeture*(60 / BASE_GRANULARITY))

            if value < 0:
                journee.SetState(value)
            else:
                journee.SetActivity(periode.arrivee, periode.depart, value)
            history.Append(None)

        array_enfants = {}
        array_salaries = {}
        lines = journal.split("\n")

        index = -1
        if len(creche.last_tablette_synchro) > 20:
            try:
                index = lines.index(creche.last_tablette_synchro)
            except:
                pass

        for line in lines[index+1:]:
            try:
                salarie, label, idx, date, heure = SplitLineTablette(line)
                if date >= today:
                    break
                if salarie:
                    array = array_salaries
                else:
                    array = array_enfants
                if idx not in array:
                    array[idx] = { }
                if date not in array[idx]:
                    array[idx][date] = []
                if label == "arrivee":
                    arrivee = (heure+TABLETTE_MARGE_ARRIVEE) / creche.granularite * (creche.granularite/BASE_GRANULARITY)
                    array[idx][date].append(PeriodePresence(date, arrivee))
                elif label == "depart":
                    depart = (heure+creche.granularite-TABLETTE_MARGE_ARRIVEE) / creche.granularite * (creche.granularite/BASE_GRANULARITY)
                    if len(array[idx][date]):
                        last = array[idx][date][-1]
                        if last.date == date and last.arrivee:
                            last.depart = depart
                        else:
                            array[idx][date].append(PeriodePresence(date, None, depart))
                    else:
                        array[idx][date].append(PeriodePresence(date, None, depart))
                elif label == "absent":
                    array[idx][date].append(PeriodePresence(date, absent=True))
                elif label == "malade":
                    array[idx][date].append(PeriodePresence(date, malade=True))
                else:
                    print "Ligne %s inconnue" % label
                creche.last_tablette_synchro = line
            except Exception, e:
                print e
                pass

        # print array_salaries

        errors = []
        for key in array_enfants:
            inscrit = creche.GetInscrit(key)
            if inscrit:
                for date in array_enfants[key]:
                    AddPeriodes(inscrit, date, array_enfants[key][date], Journee)
            else:
                errors.append(u"Inscrit %d: Inconnu!" % key)
        for key in array_salaries:
            salarie = creche.GetSalarie(key)
            if salarie:
                for date in array_salaries[key]:
                    # print key, GetPrenomNom(salarie), periode
                    AddPeriodes(salarie, date, array_salaries[key][date], JourneeSalarie)
            else:
                errors.append(u"Salarié %d: Inconnu!" % key)
        if errors:
            dlg = wx.MessageDialog(None, u"\n".join(errors), u'Erreurs de saisie tablette', wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        self.UpdateWeek()

    def UpdateContents(self):
        if len(creche.sites) > 1:
            self.site_choice.Show(True)
            self.site_choice.Clear()
            for site in creche.sites:
                self.site_choice.Append(site.nom, site)
            self.site_choice.SetSelection(self.current_site)
        else:
            self.site_choice.Show(False)

        self.activity_choice.Update()

        if counters['groupes'] > self.groupes_observer:
            self.UpdateGroupeCombobox()

        self.OnChangementSemaine()
        self.sizer.Layout()


class PlanningHebdomadairePanel(PlanningBasePanel):
    def __init__(self, parent):
        PlanningBasePanel.__init__(self, parent)
        self.activites = []
        self.inscrits = []
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 0)
        self.grid.SetDefaultColSize(200)
        self.grid.SetRowLabelSize(250)
        self.grid.EnableEditing(not readonly)
        self.sizer.Add(self.grid, -1, wx.EXPAND|wx.RIGHT|wx.TOP, 5)
        self.sizer.Layout()
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnCellChange, self.grid)

    def UpdateContents(self):
        self.OnChangementSemaine()

    def OnChangementSemaine(self, evt=None):
        self.grid.ClearGrid()
        site = self.GetSelectedSite()
        # groupe = self.GetSelectedGroupe()

        week_selection = self.week_choice.GetSelection()
        self.previous_button.Enable(week_selection is not 0)
        self.next_button.Enable(week_selection is not self.week_choice.GetCount() - 1)
        monday = self.GetSelectionStart()
        sunday = monday + datetime.timedelta(6)

        old_count = self.grid.GetNumberCols()
        self.activites = creche.activites.values()
        new_count = len(self.activites)
        if new_count > old_count:
            self.grid.AppendCols(new_count - old_count)
        elif old_count > new_count:
            self.grid.DeleteCols(0, old_count - new_count)

        for i, activity in enumerate(self.activites):
            self.grid.SetColLabelValue(i, activity.label)
            self.grid.SetColFormatFloat(i, precision=(0 if activity.mode == MODE_SANS_HORAIRES else 1))

        self.inscrits = [inscrit for inscrit in creche.inscrits if inscrit.IsPresent(monday, sunday, site)]
        self.inscrits = GetEnfantsTriesSelonParametreTriPlanning(self.inscrits)
        old_count = self.grid.GetNumberRows()
        new_count = len(self.inscrits)
        if new_count > old_count:
            self.grid.AppendRows(new_count - old_count)
        elif old_count > new_count:
            self.grid.DeleteRows(0, old_count - new_count)
        for row, inscrit in enumerate(self.inscrits):
            self.grid.SetRowLabelValue(row, GetPrenomNom(inscrit))
            if monday in inscrit.semaines:
                semaine = inscrit.semaines[monday]
                for i, activity in enumerate(self.activites):
                    if activity.value in semaine.activities:
                        self.grid.SetCellValue(row, i, locale.format("%f", semaine.activities[activity.value].value))
        self.sizer.Layout()

    def OnCellChange(self, evt):
        date = self.GetSelectionStart()
        value = self.grid.GetCellValue(evt.GetRow(), evt.GetCol())
        inscrit = self.inscrits[evt.GetRow()]
        if date not in inscrit.semaines:
            inscrit.semaines[date] = WeekPlanning(inscrit, date)
        history.Append(None)
        inscrit.semaines[date].SetActivity(self.activites[evt.GetCol()].value, float(value.replace(',', '.')))


if creche.mode_saisie_planning == SAISIE_HORAIRE:
    PlanningPanel = PlanningHorairePanel
else:
    PlanningPanel = PlanningHebdomadairePanel
