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

import __builtin__
from constants import *
import datetime
from functions import GetInscriptions, GetDateIntersection, GetDateMinus


def GetAlertes(fresh_only=False):
    alertes = []

    def add_alerte(date, message):
        ack = message in creche.alertes
        if not fresh_only or not ack:
            alertes.append((date, message, ack))

    today = datetime.date.today()
    for inscription in GetInscriptions(today, today):
        inscrit = inscription.inscrit
        if (creche.masque_alertes & ALERTE_3MOIS_AVANT_AGE_MAXIMUM) and inscrit.naissance:
            date = GetDateMinus(inscrit.naissance, years=-creche.age_maximum, months=3)
            if today > date:
                message = "%s %s aura %d ans dans 3 mois" % (inscrit.prenom, inscrit.nom, creche.age_maximum)
                add_alerte(date, message)
        if (creche.masque_alertes & ALERTE_1AN_APRES_INSCRIPTION) and inscription.debut:
            date = datetime.date(inscription.debut.year+1, inscription.debut.month, inscription.debut.day)
            if today > date:
                message = "L'inscription de %s %s passe un an aujourd'hui" % (inscrit.prenom, inscrit.nom)
                add_alerte(date, message)
        if (creche.masque_alertes & ALERTE_2MOIS_AVANT_FIN_INSCRIPTION) and inscription.fin:
            date = GetDateMinus(inscription.fin, years=0, months=2)
            if today > date:
                message = "L'inscription de %s %s se terminera dans 2 mois" % (inscrit.prenom, inscrit.nom)
                add_alerte(date, message)

    for inscrit in creche.inscrits:
        for inscription in inscrit.inscriptions:
            if inscription.debut and inscription.fin and inscription.fin < inscription.debut:
                message = "Période incorrecte pour %s %s" % (inscrit.prenom, inscrit.nom)
                add_alerte(inscription.debut, message)
        date = GetDateIntersection(inscrit.inscriptions)
        if date:
            add_alerte(date, "Les inscriptions de %s %s se chevauchent" % (inscrit.prenom, inscrit.nom))

    for salarie in creche.salaries:
        for contrat in salarie.contrats:
            if contrat.debut and contrat.fin and contrat.fin < contrat.debut:
                message = "Période incorrecte pour %s %s" % (salarie.prenom, salarie.nom)
                add_alerte(contrat.debut, message)
        date = GetDateIntersection(salarie.contrats)
        if date:
            add_alerte(date, "Les contrats de %s %s se chevauchent" % (salarie.prenom, salarie.nom))

    alertes.sort(key=lambda (date, message, ack): date)
    return alertes

