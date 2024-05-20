import random
import math
import numpy as np
from numpy.typing import NDArray
from typing import Tuple, List

from PySide6.QtCore import Qt, Slot, QPointF, QSize, QRectF
from PySide6.QtGui import QImage, QPainter, QPainterPath, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, \
    QGroupBox, QFormLayout, QSizePolicy, QComboBox

from physics_sim import PhysSim
from uqtwidgets import QImageViewer, create_scroll_int_value, create_radio_button_group
from gaapp import QSolutionToSolvePanel
from gacvm import ProblemDefinition, Domains, Parameters, GeneticAlgorithm
from ga_strategy_genes_mutation import MultiMutationStrategy


from __feature__ import snake_case, true_property


class QBalisticProblem(QSolutionToSolvePanel):
    _background_color = QColor(48, 48, 48)
    _building_height = 10

    _drone_color = QColor(Qt.white)
    _drone_width = 30
    _drone_height = 15
    _drone_brush = QBrush(_drone_color)
    _drone_brush.set_style(Qt.Dense4Pattern)

    _protected_color = QColor(143, 188, 143)
    _protected_brush = QBrush(_protected_color)

    _target_color = QColor(220, 20, 60)
    _target_brush = QBrush(_target_color)

    _best_width = 5.
    _best_arc_color = QColor(25, 25, 112)
    _best_arc_pen = QPen(_best_arc_color, _best_width)
    _best_explo_color = QColor(137, 207, 240)
    _best_explo_pen = QPen(_best_explo_color, _best_width)

    _other_color = QColor(238, 232, 170, 125)
    _other_width = 2.
    _other_pen = QPen(_other_color, _other_width)
    _other_pen.set_style(Qt.DotLine)

    _fake_pen = QPen(QColor(Qt.red), _other_width)

    def __init__(self, width: int = 500, height: int = 250,
                 longueur_bat: int = 20,
                 cible_finale_y: int = 0,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Création des widgets de paramétrage et de leur layout
        self._canvas_value = QLabel(f"{width} x {height}")
        self._obstacle_scroll_bar, obstacle_layout = create_scroll_int_value(
            1, 25, 100)
        self._posX = 25
        self._posY = 25
        self._nb_batiments = 5
        self._nb_proteges = 2
        self._batiments = []
        self._proteges = []
        self._width = width
        self._height = height
        self._longueur_batiment = longueur_bat
        self._gravity = -9.81
        self._view = False  # correspond à affichage 'Meilleur seulement'
        self.generate_batiments()
        self._cible_finale_y = cible_finale_y

        # Création des widgets de paramétrage et de leur layout
        self._positionX_scroll_bar, positionX_layout = create_scroll_int_value(
            0, self._posX, width - self._drone_width)
        self._positionX_scroll_bar.valueChanged.connect(
            lambda: self.__set_position(self._positionX_scroll_bar.value, 0))
        self._positionY_scroll_bar, positionY_layout = create_scroll_int_value(
            0, self._posY, height / 2)
        self._positionY_scroll_bar.valueChanged.connect(
            lambda: self.__set_position(self._positionY_scroll_bar.value, 1))

        self._nb_batiments_scroll_bar, nb_batiments_layout = create_scroll_int_value(
            1, self._nb_batiments, width / longueur_bat)
        self._nb_batiments_scroll_bar.valueChanged.connect(
            self._set_nb_batiments)
        self._zone_protege_scroll_bar, zone_protege_layout = create_scroll_int_value(
            0, self._nb_proteges,
            (100 * ((self._nb_batiments - 1) / self._nb_batiments)),
            value_suffix="%")
        self._zone_protege_scroll_bar.valueChanged.connect(
            self._set_zone_protege)

        self.__gravity_values = {'Terre': -9.81,
                                 'Mars': 3.71,
                                 'Saturn': 10.44,
                                 'Soleil': 274.00}
        self._gravity_picker = QComboBox()
        self._gravity_picker.add_items(self.__gravity_values.keys())
        self._gravity_picker.activated.connect(
            lambda: self._set_gravity(self._gravity_picker.current_text))

        self._view_picker, view_picker_layout = create_radio_button_group(None,
                                                                          "Meilleur seulement",
                                                                          "Génération entière")
        for button in self._view_picker.buttons():
            if button.text == "Meilleur seulement":
                button.set_checked(True)
            button.toggled.connect(self._set_view)

        param_group_box = QGroupBox('Parameters')
        param_layout = QFormLayout(param_group_box)
        param_layout.add_row("Position initiale X", positionX_layout)
        param_layout.add_row("Position initiale Y", positionY_layout)
        param_layout.add_row("Nombre de bâtiments", nb_batiments_layout)
        param_layout.add_row("Nombre de zones protégées", zone_protege_layout)
        param_layout.add_row('Gravité', self._gravity_picker)
        param_layout.add_row('Affichage des résultats', view_picker_layout)
        param_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred,
                                                  QSizePolicy.Maximum)

        # Création de la zone de visualisation
        self._visualization_widget = QImageViewer(True)

        # Création du layout principal
        main_layout = QVBoxLayout(self)
        main_layout.add_widget(param_group_box)
        main_layout.add_widget(self._visualization_widget)

    @Slot()
    def _set_view(self) -> None:
        button = self.sender() # ref -> ChatGPT
        if button.text == "Meilleur seulement":
            self._view = False
        else:
            self._view = True

    @Slot()
    def _set_gravity(self, selection: str) -> None:
        self._gravity = self.__gravity_values[selection]

    @Slot()
    def __set_position(self, value: int, axis: int) -> None:
        if axis == 0:
            self._posX = value
        else:
            self._posY = value
        self._update_from_simulation(None)

    @Slot()
    def _set_nb_batiments(self, value: int) -> None:
        self._nb_batiments = value
        self._zone_protege_scroll_bar.set_range(0, int(100 * ((value - 1) / value)))
        self.generate_batiments()
        self._update_from_simulation(None)

    @Slot()
    def _set_zone_protege(self, value: int) -> None:
        self._nb_proteges = round((value / 100) * self._nb_batiments)
        self.generate_batiments()
        self._update_from_simulation(None)

    @property
    def name(self) -> str:
        return 'Balistic Cost Optimizer'

    @property
    def summary(self) -> str:
        return '''Un drone est dans un espace au dessus de deux types de zones. Celles-ci sont les zones cibles et les zones protégées(qui ne doivent pas être touchées). Ce drone à pour but de lancer un projectile qui se séparera en 3 pendant la trajectoire et les projectiles subséquents doivent atteindre le plus de cibles possibles en utilisant les plus petites forces de propulsions. '''

    @property
    def description(self) -> str:  # note : override
        """Description du problème."""
        return '''On cherche à obtenir un score correspondant au nombre de zones cibles touchées ainsi que la force utilisée .

    Données initiales du problème : 
        - Position Initiale en X déterminée par une barre défilement
        - Position Initiale en Y déterminée par une barre défilement
        - Nombre de bâtiments totaux déterminée par une barre défilement
        - Nombre de zones protégées en pourcentage du nombre de bâtiments déterminée par une barre de défilement
        - La gravité déterminée par une liste déroulante contenant des endroits liées à leur gravité par exemple la terre : 9.81
        - Position finale en y recherchée directement déterminée dans le constructeur
    Dimension du problème : 
        - d = 5
        - d1 = [0., 150.] ce sont des valeurs d'un vecteur de vitesse intial
        - d2 = [0., 100.] c'est la valeur en pourcentage de la trajectoire parcourue avant la détonation
        - d3 = [0., 180.] c'est l'angle de propulstion initial en degrée
        - d4 = [0., 50.] c'est le pourcentage de la force d'explosion en relation avec le vecteur de vitesse intial
        - d5 = [0., 180.] c'est l'angle de séparation du cluster d'objet
    Étape Intermédiaire pour le fitness(_translate_from_chromosome)  :
        - Les valeurs des chromosomes d2 et d4 sont transformées en la valeur correspondante du pourcentage reçu
        - Les valeurs des chromosomes et des deux nouvelles valeurs calculées avec le pourcentage de d2 et d4 sont ensuite mise dans une fonction qui simulera la trajectoire
        de la position initiale jusqu'a l'explosion et puis les trajectoires resultantes des nouveaux projectiles jusqu'au point en y posé.
        - ces trois nouvelles coordonnées vont ensuite être utilisées pour la fonction objective
    Fonction objective :
        - si la valeur recherchée est hors de la plage de recherche, la fitness est de 0 
        - Si un des projectiles touche une zone protégée le score sera de zéro
        - Si aucune cible est atteinte le score sera de zéro
        - On recherche le plus de cibles diferentes atteintes en minimisant la force totale utilisée (force totale est la somme de la force initiale et d'explosion)
        - Pour ce faire on prends le nombre de cibles diferentes atteintes * 1000 et on ajoute la force économisée par le tir, c'est à dire, la force maximale potentielle - la force utilisée, donc une force utilisée plus faibel rapporte plus de points
    '''

    @property
    def problem_definition(self) -> ProblemDefinition:
        dimensions_values = [[0., 150.],
                             # Force impulsion initiale (valeur arbitraire)
                             [0., 100.],
                             # % de la trajectoire parcouru avant la detonation (donne le temps de detonation
                             [0., 180.],  # angle de propulsion (en degre)
                             [0., 50.],
                             # La force d'explosion est un % de la propulsion initiale (valeur arbitraire)
                             [0., 90.]]  # angle de separation du spray

        domains = Domains(np.array(dimensions_values), ('Force de propulsion', 'Trajectoire parcouru en pourcentage avant la detonation', 'Angle de propulsion',
             "Force de separation en pourcentage l'initiale,",
            'angle de separation'))

        def objective_fonction(chromosome: NDArray) -> float:
            force_init = chromosome[0]
            force_split = force_init * (chromosome[3] / 100.)
            impacts = self._translate_from_chromosome(chromosome, False)
            nb_target = 0
            nb_protected = 0
            temp = self._batiments.copy()
            for impact in impacts[1]:
                if self.is_pos_in_ranges(impact, self._proteges,
                                         self._height - QBalisticProblem._building_height):
                    nb_protected += 1
                elif self.is_pos_in_ranges(impact, temp,
                                           self._height - QBalisticProblem._building_height):
                    nb_target += 1
                    temp.pop(self.index_batiment(impact[0], temp))
            if nb_target == 0 or nb_protected > 0:
                return 0
            else:
                return (nb_target * 1000) + ((150 + (150 * 50 / 100)) - (
                        force_init + force_split))

        return ProblemDefinition(domains, objective_fonction)

    @staticmethod
    def index_batiment(posX: float, temp: List[Tuple[int, int]]) -> int:
        i = 0
        for batiment in temp:
            if batiment[0] <= posX <= batiment[1]:
                return i
            i += 1

    @property
    def default_parameters(self) -> Parameters:
        engine_parameters = Parameters()
        strategy = MultiMutationStrategy()
        engine_parameters.maximum_epoch = 1000
        engine_parameters.population_size = 100
        engine_parameters.elitism_rate = 0.10
        engine_parameters.selection_rate = 0.75
        engine_parameters.mutation_rate = 0.50
        engine_parameters.mutation_strategy = strategy
        return engine_parameters

    def _translate_from_chromosome(self, chromo: NDArray, all: bool) -> tuple:
        force_init = chromo[0]
        temps_split = (PhysSim.time_at_yf(
            chromo[0] * math.sin(math.radians(chromo[2])),
            self._gravity,
            self._positionY_scroll_bar.value, 0) * chromo[1] / 100.0)
        angle_init = chromo[2]
        force_split = force_init * chromo[3] / 100.
        angle_split = chromo[4]
        coordo = (self._posX, self._height - self._posY)
        if all:
            return PhysSim.get_all_points_from_start_data(force_init,
                                                          temps_split, coordo,
                                                          angle_init,
                                                          self._gravity,
                                                          force_split,
                                                          angle_split, 3, self._cible_finale_y, 1)
        else:
            return PhysSim.get_final_coordinates_from_start_data(force_init,
                                                                 temps_split,
                                                                 coordo,
                                                                 angle_init,
                                                                 self._gravity,
                                                                 force_split,
                                                                 angle_split,
                                                                 3, self._cible_finale_y)

    @staticmethod
    def is_pos_in_ranges(point: tuple[float, float], batiments: List[Tuple[int, int]], height: int) -> bool:
        temp = False
        for batiment in batiments:
            if batiment[0] <= point[0] <= batiment[1]:
                if point[1] > height:
                    temp = False
                else:
                    temp = True
        return temp

    @staticmethod
    def _draw_rectangle(painter: QPainter, rectangle: QRectF, radius: int = 0,
                        pen: QPen = Qt.NoPen,
                        brush: QBrush = Qt.NoBrush) -> None:
        painter.save()
        painter.set_pen(pen)
        painter.set_brush(brush)
        painter.draw_rounded_rect(rectangle, radius, radius)
        painter.restore()

    def generate_batiments(self) -> None:
        segments = [(x, x + self._longueur_batiment) for x in
                    range(0, 500, self._longueur_batiment)]
        random.shuffle(segments)
        liste_zones_protege = segments[:self._nb_proteges]
        liste_batiments = segments[:self._nb_batiments]

        self._batiments, self._proteges = liste_batiments, liste_zones_protege

    def _find_path_for_trajectory(self, traj) -> Tuple[QPainterPath, QPainterPath, QPainterPath]:
        arc_path = QPainterPath()
        explo = QPainterPath()
        main_explo = QPainterPath()
        arc_path.move_to(QPointF(traj[0][0][0], self._height - traj[0][0][1]))
        for p in traj[0]:
            arc_path.line_to(QPointF(p[0], 250 - p[1]))
        for i, traj in enumerate(traj[1]):
            if i == 0:
                main_explo.move_to(
                    QPointF(traj[0][0], self._height - traj[0][1]))
                for index, p in enumerate(traj):
                    main_explo.line_to(QPointF(p[0], self._height - p[1]))
            else:
                explo.move_to(
                    QPointF(traj[0][0], self._height - traj[0][1]))
                for index, p in enumerate(traj):
                    explo.line_to(QPointF(p[0], self._height - p[1]))
        return arc_path, main_explo, explo

    def _update_from_simulation(self, ga: GeneticAlgorithm | None) -> None:
        image = QImage(QSize(self._width - 1, self._height - 1),
                       QImage.Format_ARGB32)
        image.fill(QBalisticProblem._background_color)

        painter = QPainter(image)
        painter.set_pen(Qt.NoPen)
        painter.set_render_hint(QPainter.Antialiasing)

        drone = QRectF(self._posX, self._posY, QBalisticProblem._drone_width,
                       QBalisticProblem._drone_height)
        QBalisticProblem._draw_rectangle(painter, drone, 10,
                                         brush=self._drone_brush)
        for b in self._batiments:
            rect = QRectF(b[0], self._height - self._building_height,
                          self._longueur_batiment, self._building_height)
            if b in self._proteges:
                QBalisticProblem._draw_rectangle(painter, rect,
                                                 brush=QBalisticProblem._protected_brush)
            else:
                QBalisticProblem._draw_rectangle(painter, rect,
                                                 brush=QBalisticProblem._target_brush)

        if ga:
            if self._view:
                painter.set_pen(QBalisticProblem._other_pen)
                for chromosome in ga.population[1:]:
                    traj = self._translate_from_chromosome(chromosome, True)
                    paths = self._find_path_for_trajectory(traj)
                    for path in paths:
                        painter.draw_path(path)

            traj = self._translate_from_chromosome(ga.history.best_solution,True)
            paths = self._find_path_for_trajectory(traj)
            painter.set_pen(QBalisticProblem._best_arc_pen)
            for i, path in enumerate(paths):
                if i == len(paths) - 1:
                    painter.set_pen(QBalisticProblem._best_explo_pen)
                    painter.draw_path(path)
                else:
                    painter.draw_path(path)

        painter.end()
        self._visualization_widget.image = image
