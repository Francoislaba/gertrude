# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

import datetime
from constants import *
from cotisation import *

class FactureFinMois(object):
    def __init__(self, inscrit, annee, mois, options=0):
        self.inscrit = inscrit
        self.annee = annee
        self.mois = mois
        self.debut_recap = datetime.date(annee, mois, 1)
        self.fin_recap = getMonthEnd(self.debut_recap)
        self.date = self.fin_recap
        self.options = options
        self.cotisation_mensuelle = 0.0
        self.report_cotisation_mensuelle = 0.0
        self.heures_facturees_par_mode = [0.0] * 33
        self.heures_contractualisees = 0.0
        self.heures_realisees = 0.0
        self.total_realise = 0.0
        self.supplement = 0.0
        self.deduction = 0.0
        self.jours_presence_selon_contrat = {}
        self.jours_supplementaires = {}
        self.heures_supplementaires = 0.0
        self.jours_maladie = []
        self.jours_maladie_deduits = []
        self.jours_vacances = []
        self.raison_deduction = ""
        self.supplement_activites = 0.0
        self.previsionnel = False

        jours_ouvres = 0
        jours_fermeture = 0
        cotisations_mensuelles = {}
        heures_hebdomadaires = {}
        last_cotisation = None

        date = datetime.date(annee, mois, 1)
        while date.month == mois:
            if not (date in creche.jours_fermeture or date in inscrit.jours_conges):
                jours_ouvres += 1
                inscription = inscrit.GetInscription(date)
                if inscription:
                    if last_cotisation and last_cotisation.Include(date):
                        cotisation = last_cotisation
                        cotisation.jours_ouvres += 1
                    else:
                        cotisation = Cotisation(inscrit, date, options=NO_ADDRESS|self.options)
                        cotisation.jours_ouvres = 1
                        cotisation.heures_realisees = 0
                        cotisation.nombre_jours_maladie_deduits = 0
                        last_cotisation = cotisation
                        self.montant_heure_garde = cotisation.montant_heure_garde
                        if options & TRACES: print u"cotisation mensuelle à partir de %s" % date, cotisation.cotisation_mensuelle
                        
                    state, heures_reference, heures_realisees, heures_supplementaires = inscrit.getState(date)
                                       
                    if (cotisation.mode_inscription, cotisation.cotisation_mensuelle) in cotisations_mensuelles:
                        cotisation = cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)]
                        cotisation.heures_reference += heures_reference
                    else:
                        cotisation.heures_reference = heures_reference
                        cotisation.heures_maladie = 0.0
                        cotisation.heures_contractualisees = 0.0
                        cotisation.heures_supplementaires = 0.0
                        cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)] = cotisation
                    
                    if (cotisation.mode_inscription, cotisation.heures_semaine) in heures_hebdomadaires:
                        heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] += 1
                    else:
                        heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] = 1

                    if state == MALADE:
                        if heures_reference > 0:
                            self.jours_maladie.append(date)
                        if creche.mode_facturation != FACTURATION_HORAIRES_REELS or inscription.mode == MODE_FORFAIT_HORAIRE:
                            # recherche du premier et du dernier jour
                            premier_jour_maladie = tmp = date
                            nombre_jours_ouvres_maladie = 0
                            while tmp > inscrit.inscriptions[0].debut:
                                if not tmp in creche.jours_fermeture:
                                    nombre_jours_ouvres_maladie += 1
                                tmp -= datetime.timedelta(1)
                                state = inscrit.getState(tmp)[0]
                                if state == MALADE:
                                    premier_jour_maladie = tmp
                                else:
                                    break
                            if creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES:
                                nb_jours_maladie = nombre_jours_ouvres_maladie
                            elif creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES:
                                nb_jours_maladie = (date - premier_jour_maladie).days + 1
                            else:
                                dernier_jour_maladie = tmp = date
                                while not inscrit.inscriptions[-1].fin or tmp < inscrit.inscriptions[-1].fin:
                                    tmp += datetime.timedelta(1)
                                    state = inscrit.getState(tmp)[0]
                                    if state == MALADE:
                                        dernier_jour_maladie = tmp
                                    else:
                                        break
                                nb_jours_maladie = (dernier_jour_maladie - premier_jour_maladie).days + 1
                            
                            if nb_jours_maladie > creche.minimum_maladie:
                                self.jours_maladie_deduits.append(date)
                                cotisation.nombre_jours_maladie_deduits += 1
                                if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                    self.deduction += 10 * cotisation.montant_heure_garde
                                elif inscription.mode != MODE_FORFAIT_HORAIRE:
                                    self.deduction += cotisation.montant_heure_garde * heures_reference
                                cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)].heures_maladie += heures_reference
                                self.raison_deduction = u'(maladie > %dj consécutifs)' % creche.minimum_maladie
                    elif state == VACANCES:
                        if heures_reference > 0:
                            self.jours_vacances.append(date)
                    elif state > 0:
                        if state & PREVISIONNEL:
                            self.previsionnel = True

                        if heures_supplementaires > 0:
                            self.jours_supplementaires[date] = heures_realisees
                        else:
                            self.jours_presence_selon_contrat[date] = heures_realisees
                            
                        if heures_supplementaires > 0:
                            if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                self.supplement += 10 * cotisation.montant_heure_garde
                            else:
                                cotisation.heures_supplementaires += heures_supplementaires
                                self.heures_supplementaires += heures_supplementaires
                                self.supplement += cotisation.montant_heure_garde * heures_supplementaires

                    if creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE or (creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE_PERIODE_ADAPTATION and inscription.IsInPeriodeAdaptation(date)):
                        activites = inscrit.GetExtraActivites(date)
                        for value in activites:
                            activite = creche.activites[value]
                            self.supplement_activites += activite.tarif

                    self.heures_realisees += heures_realisees
                    cotisation.heures_realisees += heures_realisees
                    if cotisation.inscription.mode != MODE_FORFAIT_HORAIRE:
                        cotisation.heures_contractualisees += heures_reference
                        self.heures_contractualisees += heures_reference
                        if creche.mode_facturation == FACTURATION_HORAIRES_REELS or (creche.facturation_periode_adaptation == FACTURATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(date)):
                            self.heures_facturees_par_mode[cotisation.mode_garde] += heures_realisees
                        else:
                            self.heures_facturees_par_mode[cotisation.mode_garde] += heures_reference + heures_supplementaires                    
                    self.total_realise += heures_realisees * cotisation.montant_heure_garde
                    
            date += datetime.timedelta(1)

        for mode_inscription, montant in cotisations_mensuelles:
            cotisation = cotisations_mensuelles[mode_inscription, montant]
            if cotisation.inscription.mode == MODE_FORFAIT_HORAIRE:
                self.cotisation_mensuelle += montant * cotisation.jours_ouvres / jours_ouvres
                cotisation.heures_contractualisees = cotisation.inscription.forfait_heures_presence * cotisation.jours_ouvres / jours_ouvres
                self.heures_contractualisees += cotisation.heures_contractualisees
                if cotisation.nombre_jours_maladie_deduits > 0:
                    self.deduction += montant * cotisation.nombre_jours_maladie_deduits / cotisation.jours_ouvres
                    heures_contractualisees = cotisation.heures_contractualisees * (cotisation.jours_ouvres - cotisation.nombre_jours_maladie_deduits) / cotisation.jours_ouvres
                else:
                    heures_contractualisees = cotisation.heures_contractualisees
                if cotisation.heures_realisees > heures_contractualisees:
                    cotisation.heures_supplementaires = cotisation.heures_realisees - heures_contractualisees
                    self.heures_facturees_par_mode[cotisation.mode_garde] += cotisation.heures_realisees 
                    self.heures_supplementaires += cotisation.heures_supplementaires
                    self.supplement += cotisation.heures_supplementaires * cotisation.montant_heure_garde
                else:
                    self.heures_facturees_par_mode[cotisation.mode_garde] += heures_contractualisees
            elif creche.mode_facturation == FACTURATION_HORAIRES_REELS or (creche.facturation_periode_adaptation == FACTURATION_HORAIRES_REELS and cotisation.inscription.IsInPeriodeAdaptation(cotisation.debut)):
                self.report_cotisation_mensuelle += (cotisation.heures_realisees - cotisation.heures_supplementaires) * cotisation.montant_heure_garde
            elif self.heures_contractualisees:
                self.cotisation_mensuelle += montant * cotisation.heures_reference / self.heures_contractualisees   
        
        self.heures_facturees = sum(self.heures_facturees_par_mode)
        if creche.temps_facturation == FACTURATION_FIN_MOIS:
            self.cotisation_mensuelle += self.report_cotisation_mensuelle
            self.report_cotisation_mensuelle = 0.0
            
        # arrondi de tous les champs en euros
        self.cotisation_mensuelle = round(self.cotisation_mensuelle, 2)
        self.report_cotisation_mensuelle = round(self.report_cotisation_mensuelle, 2)
        self.supplement = round(self.supplement, 2)
        self.supplement_activites = round(self.supplement_activites, 2)
        self.deduction = round(self.deduction, 2)
        self.total_realise = round(self.total_realise, 2)
        
        self.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction
        if options & TRACES:
            print inscrit.prenom
            for var in ["heures_contractualisees", "heures_facturees", "heures_supplementaires", "cotisation_mensuelle", "supplement", "deduction", "total"]:
                print " ", var, eval("self.%s" % var)
                
class FactureDebutMois(FactureFinMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureFinMois.__init__(self, inscrit, annee, mois, options)
        if mois == 1:
            facture_precedente = FactureFinMois(inscrit, annee-1, 12, options)
        else:
            facture_precedente = FactureFinMois(inscrit, annee, mois-1, options)
        self.debut_recap = facture_precedente.debut_recap
        self.fin_recap = facture_precedente.fin_recap
        self.date = datetime.date(annee, mois, 1)
        self.cotisation_mensuelle += facture_precedente.report_cotisation_mensuelle
        self.supplement = facture_precedente.supplement
        self.deduction = facture_precedente.deduction
        self.jours_presence_selon_contrat = facture_precedente.jours_presence_selon_contrat
        self.jours_supplementaires = facture_precedente.jours_supplementaires
        self.heures_supplementaires = facture_precedente.heures_supplementaires
        self.jours_maladie = facture_precedente.jours_maladie
        self.jours_maladie_deduits = facture_precedente.jours_maladie_deduits
        self.jours_vacances = facture_precedente.jours_vacances
        self.raison_deduction = facture_precedente.raison_deduction
        self.supplement_activites = facture_precedente.supplement_activites
        self.previsionnel |= facture_precedente.previsionnel
        self.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction
        
def Facture(inscrit, annee, mois, options=0):      
    if creche.temps_facturation == FACTURATION_FIN_MOIS:
        return FactureFinMois(inscrit, annee, mois, options)
    else:
        return FactureDebutMois(inscrit, annee, mois, options)           

