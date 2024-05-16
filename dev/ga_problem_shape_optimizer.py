import random
import math
import numpy as np
from numpy.typing import NDArray

from gaapp import QSolutionToSolvePanel
from gacvm import ProblemDefinition, Domains, Parameters, GeneticAlgorithm
from uqtgui import process_area
from uqtwidgets import QImageViewer, create_scroll_int_value

from PySide6.QtCore import Qt, Slot, QPointF, QSize, QRectF, QRect
from PySide6.QtGui import QPolygonF, QTransform, QImage, QPainter, QColor, \
    QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, \
    QGroupBox, QFormLayout, QSizePolicy, QComboBox

from __feature__ import snake_case, true_property


class QShapeOptimizerProblemPanel(QSolutionToSolvePanel):

    """_background_color = QColor(48, 48, 48)
    _shape_color = QColor(148, 164, 222)
    _obstacle_color = QColor(255, 255, 255)
    _obstacle_length = 5
    Il faudrait des variables de classe, voir QUnknownProblem"""

    _population_solution_pen_color = QColor(128, 128, 128)
    _population_solution_pen_width = 1.0
    _population_solution_pen = QPen(_population_solution_pen_color, _population_solution_pen_width)

    def __init__(self, width: int = 500, height: int = 250,
                 max_obst: int = 100,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.__initialized = False
        self.__width = width
        self.__height = height
        self.__canvas_area = self.__width * self.__height  # est-ce vraiment utile ?
        self.__points_list = []
        self.__current_shape = None

        self.__triangle_center =QPointF(0.5, -0.334)
        self.__etoile_center = QPointF(0.5, -0.5)
        self.__u_center = QPointF(0.5, (52/125) )
        self.__shapes = {'Triangle': QPolygonF((QPointF(0, 0) - self.__triangle_center, 
                                                QPointF(0.5, -1) - self.__triangle_center, 
                                                QPointF(1, 0) - self.__triangle_center)),
                         'Etoile': QPolygonF((QPointF(0, -0.5) - self.__etoile_center, QPointF(0.4, -0.4) - self.__etoile_center, QPointF(0.5, 0) - self.__etoile_center, 
                                              QPointF(0.6, -0.4) - self.__etoile_center, QPointF(1, -0.5) - self.__etoile_center, QPointF(0.6, -0.6) - self.__etoile_center, 
                                              QPointF(0.5, -1) - self.__etoile_center, QPointF(0.4, -0.6) - self.__etoile_center)),
                         'The U': QPolygonF((QPointF(0,0) - self.__u_center,
                                                QPointF(0, 1) - self.__u_center ,
                                                QPointF(1, 1) - self.__u_center, 
                                                QPointF(1,0) - self.__u_center, 
                                                QPointF((5/6),0) - self.__u_center, 
                                                QPointF((5/6),(5/6)) - self.__u_center, 
                                                QPointF((1/6),(5/6)) - self.__u_center, 
                                                QPointF((1/6),0) - self.__u_center)),
                         
                         'Test U': QPolygonF((QPointF(0,0),
                                                QPointF(0, 150),
                                                QPointF(150, 150), 
                                                QPointF(150,0), 
                                                QPointF(125,0), 
                                                QPointF((125),(125)), 
                                                QPointF((25),(125)), 
                                                QPointF((25),0)))}

        # Création des widgets et du layout global
        self._canvas_value = QLabel(f"{self.__width} x {self.__height}")
        self._obstacle_scroll_bar, obstacle_layout = create_scroll_int_value(
            1, 25, max_obst)
        self._obstacle_scroll_bar.valueChanged.connect(
            self.__set_obstacle_count)

        self._shape_picker = QComboBox()
        self._shape_picker.add_items(self.__shapes.keys())
        self._shape_picker.activated.connect(
            lambda: self.__set_current_shape(self._shape_picker.current_text))

        param_group_box = QGroupBox('Parameters')
        param_layout = QFormLayout(param_group_box)
        param_layout.add_row('Canvas size', self._canvas_value)
        param_layout.add_row('Obstacle count', obstacle_layout)
        param_layout.add_row('Shape', self._shape_picker)
        param_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred,
                                                  QSizePolicy.Maximum)

        self._visualization_widget = QImageViewer(True)

        main_layout = QVBoxLayout(self)
        main_layout.add_widget(param_group_box)
        main_layout.add_widget(self._visualization_widget)

        self._background_color = QColor(48, 48, 48)
        self._shape_color = QColor(148, 164, 222)
        self._obstacle_color = QColor(255, 255, 255)
        self._obstacle_length = 5

        self.__initialize_values()

    def __initialize_values(self) -> None:
        self.__set_current_shape(self._shape_picker.current_text)
        self.__set_obstacle_count(self._obstacle_scroll_bar.value)
        self.__initialized = True

    @Slot()
    def __set_obstacle_count(self, count: int) -> None:
        self.__points_list.clear()
        for _ in range(count):
            self.__points_list.append(self.get_random_2D_point(self.__width,
                                                               self.__height))
        if self.__initialized:
            self._update_from_simulation(None)

    @Slot()
    def __set_current_shape(self, choice: str) -> None:
        self.__current_shape = self.__shapes[choice]
        if self.__initialized:
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
                             [1.0, min(self.__width, self.__height)]]
        domains = Domains(np.array(dimensions_values), (
            'Translation en X', 'Translation en Y', 'Rotation', 'Homéothétie'))

        def objective_fonction(chromosome: NDArray) -> float:
            evolved_shape = self.transform_shape(self.__current_shape,
                                                 chromosome)

            if self.contains(evolved_shape, self.__points_list):
                return 0
            elif self.contains(QRectF(0, 0, self.__width, self.__height),
                               [evolved_shape.bounding_rect()]):
                return process_area(evolved_shape) / self.__canvas_area * 10000
            else:
                return 0

        return ProblemDefinition(domains, objective_fonction)

    @staticmethod
    def contains(container: QPolygonF | QRectF,
                 contained: list[QPointF | QRect]) -> bool:
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
        x = random.randint(min_x, max_x)
        y = random.randint(min_y, max_y)
        return QPointF(x, y)

    @staticmethod
    def transform_shape(shape: QPolygonF,
                        transformations: NDArray) -> QPolygonF:
        t = QTransform().translate(transformations[0],
                                   transformations[1]).rotate(
            transformations[2]).scale(transformations[3], transformations[3])
        return t.map(shape)

    def _draw_polygon(self, painter: QPainter, polygon: QPolygonF,
                      temp, pen: QPen = Qt.NoPen) -> None:
        painter.save()
        if temp:
            painter.translate(painter.device().rect().center())
            painter.scale(125,125)
        painter.set_pen(pen)
        painter.set_brush(Qt.NoBrush if pen != Qt.NoPen else self._shape_color)
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

    def draw_bbox(self, painter: QPainter, polygon: QPolygonF):
        painter.save()
        painter.set_pen(Qt.NoPen)
        painter.set_brush(QColor("Red"))
        painter.draw_polygon(polygon.bounding_rect())
        painter.restore()

    def _update_from_simulation(self, ga: GeneticAlgorithm | None) -> None:
        image = QImage(QSize(self.__width - 1, self.__height - 1),
                       QImage.Format_ARGB32)

        image.fill(self._background_color)
        painter = QPainter(image)
        painter.set_pen(Qt.NoPen)

        form = self.__current_shape

        if ga:
            # Dessine toute la population sauf la meilleure solution
            pen = QPen(Qt.white, 2, Qt.DotLine)  # Set the pen to a dashed line
            for chromosome in ga.population[1:]:  # ga.population[1:] si on ne veut pas dessiner la première car 0 est la meilleure solution
                rejected_form = self.transform_shape(form, chromosome)
                self._draw_polygon(painter,rejected_form,0, pen)

            best = ga.history.best_solution # meilleur de l'historique
            # best = ga.population[0] # meilleur de l'époque actuelle
            form = self.transform_shape(form, best)
            #self.draw_bbox(painter, form)  # pour debug le bounding box
            self._draw_polygon(painter, form, 0)
        else:
            self._draw_polygon(painter, form, 1)            
            pass

        self._draw_obstacles(painter)
        painter.end()
        self._visualization_widget.image = image
