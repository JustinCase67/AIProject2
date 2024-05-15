import random
import math
import numpy as np

from PySide6.QtCore import Qt, Slot, QPointF, QSize, QRectF, QRect
from PySide6.QtGui import QPolygonF, QTransform, QImage, QPainter, QColor, \
    QPolygonF, QPen, QBrush, QFont

from numpy.typing import NDArray

from gaapp import QSolutionToSolvePanel
from gacvm import ProblemDefinition, Domains, Parameters, GeneticAlgorithm
from PySide6.QtWidgets import QApplication

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, \
    QGroupBox, QFormLayout, QSizePolicy, QComboBox

from __feature__ import snake_case, true_property

from uqtgui import process_area
from uqtwidgets import create_scroll_real_value, QImageViewer, \
    create_scroll_int_value


class QBalisticProblem(QSolutionToSolvePanel):

    _background_color = QColor(48, 48, 48)

    def __init__(self, width: int = 500, height: int = 250,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._trajectoires
        
        #DÉBUT DES PARAMÈTRES--------------------------------------------------------------------------------------------------
        # Création des widgets de paramétrage et de leur layout
        self._canvas_value = QLabel(f"{width} x {height}")
        self._obstacle_scroll_bar, obstacle_layout = create_scroll_int_value(
            1, 25, 100)  # Passer en paramètre le maximum
        

        self._shape_picker = QComboBox()
        #self._shape_picker.add_items()
        #self._shape_picker.activated.connect(
          #  lambda: self._update_from_simulation(None))
        #On doit faire le connect du Combox

        param_group_box = QGroupBox('Parameters')
        param_layout = QFormLayout(param_group_box)
        param_layout.add_row('Canvas size', self._canvas_value)
        param_layout.add_row('Obstacle count', obstacle_layout)
        param_layout.add_row('Shape', self._shape_picker)
        param_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum)

        #FIN DES PARAMÈTRES-----------------------------------------------------------------------------------------------------
        # Création de la zone de visualisation
        self._visualization_widget = QImageViewer(True)

        # Création du layout principal
        main_layout = QVBoxLayout(self)
        main_layout.add_widget(param_group_box)
        main_layout.add_widget(self._visualization_widget)


    @property
    def name(self) -> str:
        return 'Balistic Cost Optimizer'

    @property
    def summary(self) -> str:
        return '''Un drone vole au dessus de batiments à détruire et doit lancer un projectile de type «Arme à sous-munitions» pour maximiser le nombre de cibles atteintes sans toucher aux batiments de type protégés (tel que des hospital de campagne), le tout en utilisant les plus petites forces de propulsions. '''

    @property
    def description(self) -> str:
        return '''Description, voir modèle.'''

    #PROBLEM DEFINITION WITH OBJECTIVE FUNCTION-------------------------------------------------------------------------------------------------
    @property
    def problem_definition(self) -> ProblemDefinition:
        dimensions_values = [[0, 150],   #Force impulsion initiale (valeur arbitraire)
                             [0, 360],  #angle de propulsion (en degre)
                             [0, 100],  #% de la trajectoire parcouru avant la detonation (donne le temps de detonation)
                             [0, 50],   #La force d'explosion est un % de la propulsion initiale (valeur arbitraire)
                             [0, 360]   #angle de separation du spray
                             ]
        domains = Domains(np.array(dimensions_values), (
            'Force de propulsion', 'Angle de propulsion', 'Trajectoire parcouru avant la detonation', 'Force de separation', 'angle de separation'))

        def objective_fonction(chromosome: NDArray) -> float:
            
            #gardeer ces commentaires
            #chromosome[2] = (phys_sim.time_at_yf(chromosome[0]*math.sin(math.radians(chromosome[1])), self._gravity, self._positionY_scroll_bar.value, 0) * chromosome[2]/100.0)
            #chromosome[3] = chromosome[0] * chromosome[3]/100.0
            chromosome = self.chromosomes_traduction(chromosome)
            
            #trajectoire = phys_sim.get_final_coordo(chromosome)
            
            nb_target = 0
            nb_war_crimes = 0
            for impact in trajectoire[1]:
                if self.is_pos_in_ranges(impact[-1][0], self._proteges):
                    nb_war_crimes += 1
                elif self.is_pos_in_ranges(impact[-1][0], self._batiments):
                    nb_target += 1
            if nb_target == 0 or nb_war_crimes > 0:
                return 0
            else:#optimisation cas 1 target et 1 warcrime donner +1000-999pts?
                return 1000 * nb_target + ((domains.ranges[0][1] + domains.ranges[3][1]/100.0 * domains.ranges[0][1]) - chromosome[0] + chromosome[3])

        return ProblemDefinition(domains, objective_fonction)

    @property
    def default_parameters(self) -> Parameters:
        pass
        #return engine_parameters

    def chromosomes_traduction(chromosome: NDArray):
        #chromosome[:, 2] = (phys_sim.time_at_yf(chromosome[:, 0]*math.sin(math.radians(chromosome[:, 1])), self._gravity, self._positionY_scroll_bar.value, 0) * chromosome[:, 2]/100.0)
        chromosome[:, 3] = chromosome[:, 0] * chromosome[:, 3]/100.0
        return chromosome

    def is_pos_in_ranges(posX, batiments):
        temp = False
        for batiment in batiments:
            if batiment[0] <= posX <= batiment[1]:
                temp = True
        return temp

    def _update_from_simulation(self, ga: GeneticAlgorithm | None) -> None:
        image = QImage(QSize(self.__width - 1, self.__height - 1),
                       QImage.Format_ARGB32)

        image.fill(self._background_color)
        painter = QPainter(image)
        painter.set_pen(Qt.NoPen)

        form = self.__shapes[self._shape_picker.current_text]

        if ga:
            best = ga._genitors[ga._genitors_fit[0]['index']]
            form = self.transform_shape(form, best)
            self.draw_bbox(painter, form)#pour debug le bounding box
            self._draw_polygon(painter, form, 0)
            for chromosome in ga.population[1:]:
                current_value = chromosome
                pop = self.transform_shape(form, current_value)
                self.draw_population(painter, pop)
            #JUSTIN ICI TU DOIS DESSINER LES AUTRES FORMES!
            #REGARDE LE CODE ON DESSINE JUSTE LE BEST' TU DOIS PULL TOUTES LES TRANSFORMATIONS, ITERER SUR LA LISTE ET DESSINER LE CONTOUR POUR CHAQUES
        else:
            #form = self.__shapes[self._shape_picker.current_text]
            self._draw_polygon(painter, form, 1)
            pass

        self._draw_obstacles(painter)
        painter.end()
        self._visualization_widget.image = image
