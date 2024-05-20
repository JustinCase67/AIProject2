import random
import math
import numpy as np

from PySide6.QtCore import Qt, Slot, QPointF, QSize, QRectF, QRect, QLine
from PySide6.QtGui import QPolygonF, QTransform, QImage, QPainter, QPainterPath, QColor, \
    QPolygonF, QPen, QBrush, QFont

from numpy.typing import NDArray

from gaapp import QSolutionToSolvePanel
from gacvm import ProblemDefinition, Domains, Parameters, GeneticAlgorithm
from PySide6.QtWidgets import QApplication

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, \
    QGroupBox, QFormLayout, QSizePolicy, QComboBox

from __feature__ import snake_case, true_property

from physics_sim import PhysSim
from uqtgui import process_area
from uqtwidgets import create_scroll_real_value, QImageViewer, \
    create_scroll_int_value


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

    _best_color = QColor(218, 165, 32)
    _best_width = 5.  # combiner en une variable si reste identique
    _best_pen = QPen(_best_color, _best_width)

    _other_color = QColor(238, 232, 170)
    _other_width = 5.  # combiner en une variable si reste identique
    _other_pen = QPen(_other_color, _other_width)

    _fake_pen = QPen(QColor(Qt.red), _other_width)

    def __init__(self, width: int = 500, height: int = 250,
                 longueur_bat: int = 20,
                 cible_finale_y: int = 0,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # DÉBUT DES PARAMÈTRES--------------------------------------------------------------------------------------------------
        # Création des widgets de paramétrage et de leur layout
        self._canvas_value = QLabel(f"{width} x {height}")
        self._obstacle_scroll_bar, obstacle_layout = create_scroll_int_value(
            1, 25, 100)  # Passer en paramètre le maximum
        self._posX = 25
        self._posY = 25
        self._nb_batiments = 5  # valeur par défaut
        self._nb_proteges = 2  # valeur par défaut
        # VALEURS TEMPORAIRES POUR LA VISUALISATION
        # self._batiments = [[0, 40], [40, 80], [160, 200], [440, 480]]
        # self._proteges = [[40, 80], [440, 480]]
        self._batiments = []
        self._proteges = []
        self._trajectoires = [
            [[162, 75], [163, 76], [164, 77], [165, 78], [166, 79], [167, 80],
             [168, 81], [171, 84], [175, 88]],
            [[162, 75], [163, 74], [164, 73], [165, 72], [166, 71], [167, 70],
             [168, 69], [169, 68], [174, 83]]]
        self._best = [
            [[162, 75], [163, 74], [164, 73], [165, 72], [166, 71], [167, 70],
             [168, 69], [169, 68], [174, 83]]]
        # BATIMENTS ET PROTEGES VIENNENT DE METHODES CONNECTED
        # TRAJECTOIRES ET BEST VIENNENT DE L'ÉTAPE INTERMÉDIAIRE DANS LA FITNESS
        self._width = width
        self._height = height
        self._longueur_batiment = longueur_bat
        self._gravity = -9.81
        self.generate_batiments()
        self._cible_finale_y = cible_finale_y

        # DÉBUT DES PARAMÈTRES--------------------------------------------------------------------------------------------------
        # Création des widgets de paramétrage et de leur layout
        self._positionX_scroll_bar, positionX_layout = create_scroll_int_value(
            0, self._posX, width - self._drone_width)
        self._positionX_scroll_bar.valueChanged.connect(
            lambda: self.__set_position(self._positionX_scroll_bar.value, 0))
        self._positionY_scroll_bar, positionY_layout = create_scroll_int_value(
            0, self._posY,
            height - (self._drone_height + self._building_height))
        self._positionY_scroll_bar.valueChanged.connect(
            lambda: self.__set_position(self._positionY_scroll_bar.value, 1))

        self._nb_batiments_scroll_bar, nb_batiments_layout = create_scroll_int_value(
            1, self._nb_batiments, width / longueur_bat)
        self._nb_batiments_scroll_bar.valueChanged.connect(
            self._set_nb_batiments)
        # self._nb_batiments_scroll_bar.valueChanged.connect(self._set_max_protege)
        self._zone_protege_scroll_bar, zone_protege_layout = create_scroll_int_value(
            0, self._nb_proteges,
            (100 * ((self._nb_batiments - 1) / self._nb_batiments)),
            value_suffix="%")
        self._zone_protege_scroll_bar.valueChanged.connect(
            self._set_zone_protege)

        self.__gravity_values = {'Terre': 9.81,
                                 'Mars': 3.71,
                                 'Saturn': 10.44,
                                 'Soleil': 274.00}

        self._gravity_picker = QComboBox()
        self._gravity_picker.add_items(self.__gravity_values.keys())
        self._gravity_picker.activated.connect(
            lambda: self._set_gravity(self._gravity_picker.current_text))

        param_group_box = QGroupBox('Parameters')
        param_layout = QFormLayout(param_group_box)
        param_layout.add_row("Position initiale X", positionX_layout)
        param_layout.add_row("Position initiale Y", positionY_layout)
        param_layout.add_row("Nombre de bâtiments", nb_batiments_layout)
        param_layout.add_row("Nombre de zones protégées", zone_protege_layout)
        param_layout.add_row('Gravité', self._gravity_picker)
        param_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred,
                                                  QSizePolicy.Maximum)

        # FIN DES PARAMÈTRES-----------------------------------------------------------------------------------------------------
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
    def _set_nb_batiments(self, value):
        self._nb_batiments = value
        self._zone_protege_scroll_bar.set_range(0, int(100 * (
                    (value - 1) / value)))
        self.generate_batiments()
        self._update_from_simulation(None)

    @Slot()
    def _set_zone_protege(self, value):
        self._nb_proteges = round((
                                              value / 100) * self._nb_batiments)  # IL EST POSSIBLE QUE ÇA NOUS DONNE 0 CIBLE
        self.generate_batiments()
        self._update_from_simulation(None)

    @property
    def name(self) -> str:
        return 'Balistic Cost Optimizer'

    @property
    def summary(self) -> str:
        return '''Un drone vole au dessus de batiments à détruire et doit lancer un projectile de type «Arme à sous-munitions» pour maximiser le nombre de cibles atteintes sans toucher aux batiments de type protégés (tel que des hospital de campagne), le tout en utilisant les plus petites forces de propulsions. '''

    @property
    def description(self) -> str:  # note : override
        """Description du problème."""
        return '''On cherche à obtenir une valeur .

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

    # PROBLEM DEFINITION WITH OBJECTIVE FUNCTION-------------------------------------------------------------------------------------------------
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

        domains = Domains(np.array(dimensions_values), ('Force de propulsion', 'Trajectoire parcouru avant la detonation', 'Angle de propulsion',
             "Force de separation en pourcentage l'initiale,",
            'angle de separation'))

        def objective_fonction(chromosome: NDArray) -> float:
            force_init = chromosome[0]
            temps_split = (PhysSim.time_at_yf(chromosome[0]* math.sin(math.radians(chromosome[2])), self._gravity, self._positionY_scroll_bar.value, 0) * chromosome[1]/100.0)
            angle_init = chromosome[2]
            force_split = force_init * chromosome[3] / 100.
            angle_split = chromosome[4]
            coordo = (self._posX, 250 - self._posY)
            impacts = PhysSim.get_final_coordinates_from_start_data(force_init,
                                                                    temps_split,
                                                                    coordo,
                                                                    angle_init,
                                                                    self._gravity,
                                                                    force_split,
                                                                    angle_split, 3, self._cible_finale_y)
            nb_target = 0
            nb_war_crimes = 0
            temp = self._batiments.copy()
            for impact in impacts[1]:
                if self.is_pos_in_ranges(impact[0], self._proteges):
                    nb_war_crimes += 1
                elif self.is_pos_in_ranges(impact[0], temp):
                    nb_target += 1
                    temp.pop(self.index_batiment(impact[0], temp))
            if nb_target == 0 or nb_war_crimes > 0:
                return 0
            else:
                #return (nb_target * 10000 / (force_init + force_split) * 100) + 1
                return (nb_target * 1000) + ((150 + (150 * 50 / 100)) - (
                            force_init + force_split))

        return ProblemDefinition(domains, objective_fonction)

    @staticmethod
    def index_batiment(posX, temp):
        i = 0
        for batiment in temp:
            if batiment[0] <= posX <= batiment[1]:
                return i
            i += 1

    @property
    def default_parameters(self) -> Parameters:
        engine_parameters = Parameters()
        engine_parameters.maximum_epoch = 200
        engine_parameters.population_size = 100
        return engine_parameters

    def chromosomes_traduction(chromosome: NDArray):
        # chromosome[:, 2] = (phys_sim.time_at_yf(chromosome[:, 0]*math.sin(math.radians(chromosome[:, 1])), self._gravity, self._positionY_scroll_bar.value, 0) * chromosome[:, 2]/100.0)
        chromosome[:, 3] = chromosome[:, 0] * chromosome[:, 3] / 100.0
        return chromosome

    @staticmethod
    def is_pos_in_ranges(posX, batiments):
        temp = False
        for batiment in batiments:
            if batiment[0] <= posX <= batiment[1]:
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

    def generate_batiments(self):
        # segment_width = self._longueur_batiment
        # num_batiments = self._nb_batiments
        segments = [(x, x + self._longueur_batiment) for x in
                    range(0, 500, self._longueur_batiment)]
        # segments = [((x, 0), (x + self._longueur_batiment, 0)) for x in range(0, 500, self._longueur_batiment)]
        # num_protected_zones = int(num_batiments * self._zone_protege / 100)
        random.shuffle(segments)
        liste_zones_protege = segments[:self._nb_proteges]
        liste_batiments = segments[:self._nb_batiments]

        self._batiments, self._proteges = liste_batiments, liste_zones_protege
        # self._update_from_simulation()

    def _update_from_simulation(self, ga: GeneticAlgorithm | None) -> None:
        image = QImage(QSize(self._width - 1, self._height - 1),
                       QImage.Format_ARGB32)
        image.fill(QBalisticProblem._background_color)

        painter = QPainter(image)
        painter.set_pen(Qt.NoPen)
        painter.set_render_hint(QPainter.Antialiasing)

        drone = QRectF(self._posX, self._posY, QBalisticProblem._drone_width,
                       QBalisticProblem._drone_height)
        QBalisticProblem._draw_rectangle(painter, drone, 0,
                                         brush=self._drone_brush)
        for b in self._batiments:
            rect = QRectF(b[0], self._height - self._building_height, self._longueur_batiment, self._building_height)
            if b in self._proteges:
                QBalisticProblem._draw_rectangle(painter, rect, brush=QBalisticProblem._protected_brush)
            else:
                QBalisticProblem._draw_rectangle(painter, rect, brush=QBalisticProblem._target_brush)

        if ga:
            painter.set_pen(QBalisticProblem._best_pen)
            force_init = ga.history.best_solution[0]
            temps_split = (PhysSim.time_at_yf(ga.history.best_solution[0]* math.sin(math.radians(ga.history.best_solution[2])), self._gravity, self._positionY_scroll_bar.value, 0) * ga.history.best_solution[1]/100.0)
            angle_init = ga.history.best_solution[2]
            force_split = force_init * ga.history.best_solution[3] / 100.
            angle_split = ga.history.best_solution[4]
            coordo = (self._posX, 250 - self._posY)
            traj = PhysSim.get_all_points_from_start_data(force_init,
                                                          temps_split, coordo,
                                                          angle_init,
                                                          self._gravity,
                                                          force_split,
                                                          angle_split, 3, self._cible_finale_y, 1)
            # NE DESSINE QUE LE PRINCIPAL ET UNE DES SÉPARATIONS
            path = QPainterPath()
            path2 = QPainterPath()
            path3 = QPainterPath()
            path.move_to(QPointF(traj[0][0][0], 250 - traj[0][0][1]))
            for p in traj[0]:
                path.line_to(QPointF(p[0], 250 - p[1]))
            for i, traj in enumerate(traj[1]):
                if i == 0:
                    path3.move_to(QPointF(traj[0][0], 250 - traj[0][1]))
                    for index, p in enumerate(traj):
                        path3.line_to(QPointF(p[0], 250 - p[1]))
                else:
                    path2.move_to(QPointF(traj[0][0], 250 - traj[0][1]))
                    for index, p in enumerate(traj):
                        path2.line_to(QPointF(p[0], 250 - p[1]))
            # path.line_to(QPointF(traj[1][0][-1][0], 250-traj[1][0][-1][1]))
            painter.draw_path(path)
            painter.set_pen(QBalisticProblem._other_pen)
            painter.draw_path(path2)
            painter.set_pen(QBalisticProblem._fake_pen)
            painter.draw_path(path3)
            '''
            for trajectoire in self._trajectoires:
                if trajectoire in self._best:
                    painter.set_pen(QBalisticProblem._best_pen)
                else:
                    painter.set_pen(QBalisticProblem._other_pen)
                for point in trajectoire:
                    point = QPointF(point[0], point[1])
                    painter.draw_point(point)'''

        painter.end()
        self._visualization_widget.image = image

