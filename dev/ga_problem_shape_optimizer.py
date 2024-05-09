import numpy as np
from PySide6.QtCore import Qt, Slot, QPointF
from PySide6.QtGui import QPolygonF, QTransform
from numpy.typing import NDArray

from gaapp import QSolutionToSolvePanel
from gacvm import ProblemDefinition, Domains, Parameters, GeneticAlgorithm

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, \
    QGroupBox, QFormLayout, QSizePolicy, QComboBox

from __feature__ import snake_case, true_property

from uqtgui import process_area
from uqtwidgets import create_scroll_real_value, QImageViewer, \
    create_scroll_int_value


class QShapeOptimizerProblemPanel(QSolutionToSolvePanel):

    def __init__(self, width: int = 500, height: int = 250,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.__width = width
        self.__height = height
        temp_points = [QPointF(250, 50), QPointF(175, 200), QPointF(325, 200)]
        self.temp_current = QPolygonF(temp_points)
        self.__shapes = {'Triangle': QPolygonF(temp_points), 'Shape2': [], 'Shape3': []}
        # Création des widgets de paramétrage et de leur layout
        self._canvas_value = QLabel(f"{self.__width}x{self.__height}")
        self._obstacle_scroll_bar, obstacle_layout = create_scroll_int_value(
            1, 25, 100)
        self._obstacle_scroll_bar.valueChanged.connect(
            self.__set_obstacle_count)
        self._shape_picker = QComboBox()
        self._shape_picker.add_items(self.__shapes.keys())
        self._shape_picker.activated.connect(
            self._update_from_simulation(None))

        param_group_box = QGroupBox('Parameters')
        param_layout = QFormLayout(param_group_box)
        param_layout.add_row('Canvas size', self._canvas_value)
        param_layout.add_row('Obstacle count', obstacle_layout)
        param_layout.add_row('Shape', self._shape_picker)
        param_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred,
                                                  QSizePolicy.Maximum)

        # Création de la zone de visualisation
        self._visualization_widget = QImageViewer(True)

        # Création du layout principal
        main_layout = QVBoxLayout(self)
        main_layout.add_widget(param_group_box)
        main_layout.add_widget(self._visualization_widget)

    @Slot()
    def __set_obstacle_count(self, count: int):
        print(count)
        # génère les valeurs aléatoires et les stocke dans variable?
        self._update_from_simulation(None)

    @property
    def name(self) -> str:
        return 'Shape Optimizer'

    @property
    def summary(self) -> str:
        return '''On recherche les transformations à appliquer sur une forme afin de maximiser son aire sur une surface donnée sans collision.'''

    @property
    def description(self) -> str:
        return '''Description, voir modèle.'''

    @property
    def problem_definition(self) -> ProblemDefinition:
        dimensions_values = [[-(self.__width / 2), self.__width / 2],
                             [-(self.__height / 2), self.__height / 2],
                             [0, 360],
                             [0,
                              0]]  # à changer avec le calcul. borne exclue calculable? sinon score 0.
        # Contradiction entre typehiting et docstring ?
        domains = Domains(np.array(dimensions_values), (
            'Translation en X', 'Translation en Y', 'Rotation', 'Homéothétie'))

        def objective_fonction(chromosome: NDArray) -> float:
            transformations = QTransform().translate(chromosome[0], chromosome[1]).rotate(chromosome[2]).scale(chromosome[3], chromosome[3])


            current_shape = transformations.map(self.temp_current)
            print(type(current_shape))
            area = process_area(current_shape)


            # fonction qui vérifie si dans le cadre, si oui -> 0
            # fonction qui vérifie si obstacle dedans, si oui -> 0
            # calcule aire de la forme avec les transformations / aire totale -> score
            print(area)

        return ProblemDefinition(domains, objective_fonction)

    @property
    def default_parameters(self) -> Parameters:
        engine_parameters = Parameters()
        # paramètres par défault à changer éventuellement
        return engine_parameters

    def _update_from_simulation(self, ga: GeneticAlgorithm | None) -> None:
        print('Je suis un override pour le dessin')
