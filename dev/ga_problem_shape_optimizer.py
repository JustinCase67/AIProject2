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


class QShapeOptimizerProblemPanel(QSolutionToSolvePanel):

    def __init__(self, width: int = 500, height: int = 250,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.__width = width
        self.__height = height
        self.__canvas_area = self.__width * self.__height
        self.__triangle_center = QPointF(43.33, 75)
        self.__etoile_center = QPointF(37.5, 12.184)
        self.__shapes = {'Triangle': QPolygonF((QPointF(0, 0)-self.__triangle_center, QPointF(0, 150)-self.__triangle_center, QPointF(130, 75)-self.__triangle_center)),
                         'Etoile': QPolygonF((QPointF(0, 0)-self.__etoile_center, QPointF(75, 0)-self.__etoile_center, QPointF(14.324, 44.089)-self.__etoile_center, 
                                              QPointF(37.5, -27.246)-self.__etoile_center, QPointF(60.676, 44.089)-self.__etoile_center)),
                         'Shape3':[] }
        self.__points_list = []
        self.__current_shape = self.__shapes["Triangle"] # changer pour none
        # Création des widgets de paramétrage et de leur layout
        self._canvas_value = QLabel(f"{self.__width} x {self.__height}")
        self._obstacle_scroll_bar, obstacle_layout = create_scroll_int_value(
            1, 25, 100)  # Passer en paramètre le maximum
        self._obstacle_scroll_bar.valueChanged.connect(
            self.__set_obstacle_count)

        self._shape_picker = QComboBox()
        self._shape_picker.add_items(self.__shapes.keys())
        self._shape_picker.activated.connect(
            lambda: self._update_from_simulation(None))
        #On doit faire le connect du Combox

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

        # faire une premiere initialisation ici pour shape et points
        self._background_color = QColor(48, 48, 48)
        self._shape_color = QColor(148, 164, 222)
        self._obstacle_color = QColor(255, 255, 255)
        self._obstacle_length = 5

    @Slot()
    def __set_obstacle_count(self, count: int) -> None:
        self.__points_list.clear()
        for _ in range(count):
            self.__points_list.append(self.get_random_2D_point(self.__width,
                                                                self.__height))
        self._update_from_simulation(None)

    @Slot()
    def __set_current_shape(self, choice: str) -> None:
        self.__current_shape = self.__shapes[choice]
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
        dimensions_values = [[0, self.__width],
                             [0, self.__height],
                             [0, 360],
                             [0, math.sqrt(((
                                                self.__canvas_area) / process_area(
                                 self.__current_shape)))]]
        domains = Domains(np.array(dimensions_values), (
            'Translation en X', 'Translation en Y', 'Rotation', 'Homéothétie'))

        def objective_fonction(chromosome: NDArray) -> float:
            evolved_shape = self.transform_shape(self.__current_shape, chromosome)

            if self.contains(evolved_shape, self.__points_list):
                return 0
            elif self.contains(QRectF(0, 0, self.__width, self.__height),
                               [evolved_shape.bounding_rect()]):
                return process_area(evolved_shape) / self.__canvas_area * 10000
            else:
                return 0

        return ProblemDefinition(domains, objective_fonction)

    @staticmethod
    def contains(container: QPolygonF | QRectF, contained: list[QPointF | QRect]) -> bool:
        if isinstance(container, QPolygonF):
            for c in contained:
                if container.contains_point(c, Qt.OddEvenFill):
                    return True
        else:
            if container.contains(contained[0]):
                return True
        return False

    @property
    def default_parameters(self) -> Parameters:
        engine_parameters = Parameters()
        # Utiliser Mutate all genes
        engine_parameters.maximum_epoch = 350
        engine_parameters.mutation_rate = 0.6
        return engine_parameters

    @staticmethod
    def get_random_2D_point(max_x: int, max_y: int, min_x: int = 0,
                            min_y: int = 0) -> QPointF:
        x = random.randint(0, max_x)
        y = random.randint(0, max_y)
        return QPointF(x, y)

    @staticmethod
    def transform_shape(shape: QPolygonF,
                        transformations: NDArray) -> QPolygonF:
        t = QTransform().translate(transformations[0], transformations[1]).rotate(transformations[2]).scale(transformations[3], transformations[3])
        return t.map(shape)

    def _draw_polygon(self, painter: QPainter, polygon: QPolygonF) -> None:
        painter.save()
        painter.translate(painter.device().rect().center())
        painter.set_pen(Qt.NoPen)
        painter.set_brush(self._shape_color)
        painter.draw_polygon(polygon)
        painter.restore()

    def _draw_obstacles(self, painter: QPainter):
        painter.save()
        painter.set_pen(Qt.NoPen)
        painter.set_brush(self._obstacle_color)
        for obstacle in self.__points_list:
            painter.draw_ellipse(obstacle.x(), obstacle.y(),
                                 self._obstacle_length, self._obstacle_length)
        painter.restore()

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
            self._draw_polygon(painter, form)


        else:
            form = self.__shapes[self._shape_picker.current_text]
            self._draw_polygon(painter, form)

        self._draw_obstacles(painter)
        painter.end()
        self._visualization_widget.image = image
