import random
import math
import numpy as np
from PySide6.QtCore import Qt, Slot, QPointF,  QSize, QRect
from PySide6.QtGui import QPolygonF, QTransform , QImage, QPainter, QColor, QPolygonF, QPen, QBrush, QFont

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
        self.__shapes = {'Triangle': QPolygonF((QPointF(250, 50), QPointF(175, 200), QPointF(325, 200))),
                         'Shape2': [],
                         'Shape3':[] }
        self.__points_list = []
        #On doit créer un polygon default
        # Création des widgets de paramétrage et de leur layout
        self.temp_current = self.__shapes["Triangle"]
        area = process_area(self.temp_current)
        self._canvas_value = QLabel(f"{self.__width} x {self.__height}")
        self._obstacle_scroll_bar, obstacle_layout = create_scroll_int_value(
            1, 25, 100) #Passer en paramètre le maximum
        self._obstacle_scroll_bar.valueChanged.connect(
            self.__set_obstacle_count)
    
        self._shape_picker = QComboBox()
        self._shape_picker.add_items(self.__shapes.keys())
        self._shape_picker.activated.connect(
            self._update_from_simulation(None))
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
        
        
        
        self._background_color = QColor(48, 48, 48)
        self._shape_color = QColor(148, 164, 222)

    @Slot()
    def __set_obstacle_count(self, count: int):
        print(count)
        self.__points_list.clear()
        #Méthode create_random_point()
        for _ in range(count):
            x = random.randint(0, self.__width)
            y = random.randint(0, self.__height)
            self.__points_list.append(QPointF(x, y))
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
                             [0,math.sqrt(((self.__canvas_area)/process_area(self.temp_current)))]] 
        domains = Domains(np.array(dimensions_values), (
            'Translation en X', 'Translation en Y', 'Rotation', 'Homéothétie'))

        def objective_fonction(chromosome: NDArray) -> float:
            t1 = QTransform().translate(chromosome[0], chromosome[1]).rotate(chromosome[2]).scale(chromosome[3], chromosome[3])
            
            #t2= QTransform().rotate(chromosome[2])
            #t3= QTransform().scale(chromosome[3], chromosome[3])
            
            #t1 = QTransform().translate(52, 65)
            #t2= QTransform().rotate(290)
            #t3= QTransform().scale(6.5, 6.5)


            current_shape = t1.map(self.temp_current)
            #current_shape = t2.map(current_shape)
            #current_shape = t3.map(current_shape)

            if self.contains(current_shape, self.__points_list):
                return 0
            elif self.contains(QRect(0 , 0 , self.__width , self.__height),[current_shape]):
                return process_area(current_shape)/self.__canvas_area
            else :
                return 0

        return ProblemDefinition(domains, objective_fonction)
    
    def contains(container, containees):
        for c in containees:
            if container.contains(c):
                return True
            
        return False
            
        

    @property
    def default_parameters(self) -> Parameters:
        engine_parameters = Parameters()
        # paramètres par défault à changer éventuellement
        return engine_parameters
    
    def _draw_triangle(self, painter : QPainter, polygon : QPolygonF ) -> None:
        painter.set_pen(Qt.NoPen)
        painter.set_brush(self._shape_color)
        painter.draw_polygon(polygon)

    def _update_from_simulation(self, ga: GeneticAlgorithm | None) -> None:
        print('Je suis un override pour le dessin')
        image = QImage(QSize(self.__width - 1, self.__height - 1), QImage.Format_ARGB32)
        
        image.fill(self._background_color)
        painter = QPainter(image)
        painter.set_pen(Qt.NoPen)
        
        
        if ga:
            print("ga")
            
        else:
            form = self.__shapes[self._shape_picker.current_text]
            self._draw_triangle(painter, form)     
            
        painter.end()
        self._visualization_widget.image = image

