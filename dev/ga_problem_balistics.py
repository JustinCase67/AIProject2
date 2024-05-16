import random
import math
import numpy as np

from PySide6.QtCore import Qt, Slot, QPointF, QSize, QRectF, QRect, QLine
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
    _building_height = 8

    _drone_color = QColor(Qt.white)
    _drone_width = 30
    _drone_height = 15
    _drone_brush = QBrush(_drone_color)
    _drone_brush.set_style(Qt.Dense4Pattern)

    _protected_color = QColor(143, 188, 143)
    _protected_brush = QBrush(_protected_color)

    _target_color = QColor(220, 20, 60)
    _target_brush = QBrush(_target_color)

    _best_color = QColor(218, 165, 32)
    _best_width = 5. # combiner en une variable si reste identique
    _best_pen = QPen(_best_color, _best_width)

    _other_color = QColor(238, 232, 170)
    _other_width = 5. # combiner en une variable si reste identique
    _other_pen = QPen(_other_color, _other_width)

    def __init__(self, width: int = 500, height: int = 250, longueur_bat : int = 20,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._posX = 25
        self._posY = 25
        self._nb_batiments = 5 # valeur par défaut
        self._nb_proteges = 2 # valeur par défaut
        # VALEURS TEMPORAIRES POUR LA VISUALISATION
        self._batiments = [[0, 40], [40, 80], [160, 200], [440, 480]]
        self._proteges = [[40, 80], [440, 480]]
        self._trajectoires = [[[162, 75], [163, 76], [164, 77], [165, 78], [166, 79], [167, 80], [168, 81], [171, 84], [175, 88]],
                              [[162, 75], [163, 74], [164, 73], [165, 72], [166, 71], [167, 70], [168, 69], [169, 68], [174, 83]]]
        self._best = [[[162, 75], [163, 74], [164, 73], [165, 72], [166, 71], [167, 70], [168, 69], [169, 68], [174, 83]]]
        # BATIMENTS ET PROTEGES VIENNENT DE METHODES CONNECTED
        # TRAJECTOIRES ET BEST VIENNENT DE L'ÉTAPE INTERMÉDIAIRE DANS LA FITNESS
        self._width = width
        self._height = height
        self._longueur_batiment = longueur_bat
        self._gravity = 9.81 # valeur par défaut


        #DÉBUT DES PARAMÈTRES--------------------------------------------------------------------------------------------------
        # Création des widgets de paramétrage et de leur layout  
        self._positionX_scroll_bar, positionX_layout = create_scroll_int_value( 0, self._posX, width)
        self._positionX_scroll_bar.valueChanged.connect(lambda : self.__set_position(self._positionX_scroll_bar.value, 0))
        self._positionY_scroll_bar, positionY_layout = create_scroll_int_value(0, self._posY, height)
        self._positionY_scroll_bar.valueChanged.connect(lambda : self.__set_position(self._positionY_scroll_bar.value, 1))

        self._nb_batiments_scroll_bar, nb_batiments_layout = create_scroll_int_value(1, self._nb_batiments, width/longueur_bat)
        self._nb_batiments_scroll_bar.valueChanged.connect(self._set_nb_batiments)
        #self._nb_batiments_scroll_bar.valueChanged.connect(self._set_max_protege)
        self._zone_protege_scroll_bar, zone_protege_layout = create_scroll_int_value(0, self._nb_proteges, (100*((self._nb_batiments-1)/self._nb_batiments)) , value_suffix="%")
        self._zone_protege_scroll_bar.valueChanged.connect(self._set_zone_protege)

        self.__gravity_values = {'Terre': 9.81,
                                 'Mars': 3.71,
                                 'Saturn': 10.44,
                                 'Soleil': 274.00}

        self._gravity_picker = QComboBox()
        self._gravity_picker.add_items(self.__gravity_values.keys())
        self._gravity_picker.activated.connect(lambda: self._set_gravity(self._gravity_picker.current_text))

        param_group_box = QGroupBox('Parameters')
        param_layout = QFormLayout(param_group_box)
        param_layout.add_row ("Position initiale X", positionX_layout)
        param_layout.add_row ("Position initiale Y", positionY_layout)
        param_layout.add_row ("Nombre de bâtiments", nb_batiments_layout)
        param_layout.add_row ("Nombre de zones protégées", zone_protege_layout)
        param_layout.add_row('Gravité', self._gravity_picker)
        param_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum)

        #FIN DES PARAMÈTRES-----------------------------------------------------------------------------------------------------
        # Création de la zone de visualisation
        self._visualization_widget = QImageViewer(True)

        # Création du layout principal
        main_layout = QVBoxLayout(self)
        main_layout.add_widget(param_group_box)
        main_layout.add_widget(self._visualization_widget)

    @Slot()
    def _set_gravity(self, selection: str) -> None:
        self._gravity = self.__gravity_values[selection]

    @Slot()
    def __set_position(self, value, axis):
        if axis == 0:
            self._posX = value
        else:
            self._posY = value
        self._update_from_simulation(None)

    @Slot()
    def _set_nb_batiments(self,value):
        self._nb_batiments = value
        self._zone_protege_scroll_bar.set_range(0, int(100*((value-1)/value)))
        self._update_from_simulation(None)


    @Slot()
    def _set_zone_protege(self, value):
        self._nb_proteges = round((value/100)*self._nb_batiments)#IL EST POSSIBLE QUE ÇA NOUS DONNE 0 CIBLE
        self._update_from_simulation(None)

    @property
    def name(self) -> str:
        return 'Balistic Cost Optimizer'

    @property
    def summary(self) -> str:
        return '''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus vitae neque sit amet odio dictum consectetur. Curabitur in eros nec nunc consectetur posuere nec nec.'''

    @property
    def description(self) -> str:
        return '''Description, voir modèle.'''

    #PROBLEM DEFINITION WITH OBJECTIVE FUNCTION-------------------------------------------------------------------------------------------------
    @property
    def problem_definition(self) -> ProblemDefinition:



        def objective_fonction(chromosome: NDArray) -> float:
           return 0

        return ProblemDefinition([],objective_fonction)

    @property
    def default_parameters(self) -> Parameters:
        pass
        #return engine_parameters

    @staticmethod
    def _draw_rectangle(painter: QPainter, rectangle: QRectF, radius: int = 0, pen: QPen = Qt.NoPen, brush: QBrush = Qt.NoBrush) -> None:
        painter.save()
        painter.set_pen(pen)
        painter.set_brush(brush)
        painter.draw_rounded_rect(rectangle, radius, radius)
        painter.restore()

    def generate_batiments(self):
        #segment_width = self._longueur_batiment
        #num_batiments = self._nb_batiments
        segments = [((x, 0), (x + self._longueur_batiment, 0)) for x in range(0, 500, self._longueur_batiment)]
        #num_protected_zones = int(num_batiments * self._zone_protege / 100)
        random.shuffle(segments)
        liste_zones_protege = segments[:self._nb_proteges]
        liste_batiments = segments[:self._nb_batiments]

        self._batiments, self._proctected_zones = liste_batiments, liste_zones_protege
        self._update_from_simulation()


    def _update_from_simulation(self, ga: GeneticAlgorithm | None) -> None:
        image = QImage(QSize(self._width - 1, self._height - 1),
                       QImage.Format_ARGB32)
        image.fill(QBalisticProblem._background_color)
        painter = QPainter(image)
        painter.set_pen(Qt.NoPen)
        painter.set_render_hint(QPainter.Antialiasing)

        drone = QRectF(self._posX, self._posY, QBalisticProblem._drone_width,
                       QBalisticProblem._drone_height)
        QBalisticProblem._draw_rectangle(painter, drone, 0, brush=self._drone_brush)
        for b in self._batiments:
            rect = QRectF(b[0], self._height - self._building_height, self._longueur_batiment, self._building_height)
            if b in self._proteges:
                QBalisticProblem._draw_rectangle(painter, rect, brush=QBalisticProblem._protected_brush)
            else:
                QBalisticProblem._draw_rectangle(painter, rect, brush=QBalisticProblem._target_brush)

        # EST TEMPORAIREMENT ICI POUR LA VISUALISATION
        for trajectoire in self._trajectoires:
            if trajectoire in self._best:
                painter.set_pen(QBalisticProblem._best_pen)
            else:
                painter.set_pen(QBalisticProblem._other_pen)
            for point in trajectoire:
                point = QPointF(point[0], point[1])
                painter.draw_point(point)
        # VA SEULEMENT DANS LE IF GA, À RETIRER QUAND GA FONCTIONNEL

        if ga:
            for trajectoire in self._trajectoires:
                if trajectoire in self._best:
                    painter.set_pen(QBalisticProblem._best_pen)
                else:
                    painter.set_pen(QBalisticProblem._other_pen)
                for point in trajectoire:
                    point = QPointF(point[0], point[1])
                    painter.draw_point(point)

        painter.end()
        self._visualization_widget.image = image
