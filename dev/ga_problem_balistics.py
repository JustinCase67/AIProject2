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

    def __init__(self, width: int = 500, height: int = 250, longeur_bat : int = 20,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self._posX = 25
        self._posY = 25
        self._nb_batiments = 5
        self._zone_protege = 20
        self._width = width
        self._height = height
        
        
        #self._drone = QRectF(QPointF(0,0), QPointF(0, ))
        

        #DÉBUT DES PARAMÈTRES--------------------------------------------------------------------------------------------------
        # Création des widgets de paramétrage et de leur layout  
        self._positionX_scroll_bar, positionX_layout = create_scroll_int_value( 0, self._posX, width)
        self._positionX_scroll_bar.valueChanged.connect(lambda : self.__set_position(self._positionX_scroll_bar.value, 0))
        self._positionY_scroll_bar, positionY_layout = create_scroll_int_value(0, self._posY, height)
        self._positionY_scroll_bar.valueChanged.connect(lambda : self.__set_position(self._positionY_scroll_bar.value, 1))

        self._nb_batiments_scroll_bar, nb_batiments_layout = create_scroll_int_value(1, self._nb_batiments, width/longeur_bat)
        self._nb_batiments_scroll_bar.valueChanged.connect(self._set_nb_batiments)
        self._zone_protege_scroll_bar, zone_protege_layout = create_scroll_int_value(0, self._zone_protege, 100 , value_suffix="%")
        self._zone_protege_scroll_bar.valueChanged.connect(self._set_zone_protege)

        
        self.__gravity = {'Terre': 9.81 ,
                         'Mars': 3.71,
                         'Saturn': 10.44,
                         'Soleil': 274.00 }
        
        self._gravity_picker = QComboBox()
        self._gravity_picker.add_items(self.__gravity.keys())
        self._gravity_picker.activated.connect(  lambda: self._update_from_simulation(None))
        #On doit faire le connect du Combox

        param_group_box = QGroupBox('Parameters')
        param_layout = QFormLayout(param_group_box)
        #param_layout.add_row('Obstacle count', obstacle_layout)
        param_layout.add_row ("Position Initiale X", positionX_layout)
        param_layout.add_row ("Position Initiale Y", positionY_layout)
        param_layout.add_row ("Nombre de Batîments", nb_batiments_layout)
        param_layout.add_row ("Nombre de Zone Protégée", zone_protege_layout)
        param_layout.add_row('Gravity', self._gravity_picker)
        param_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum)

        #FIN DES PARAMÈTRES-----------------------------------------------------------------------------------------------------
        # Création de la zone de visualisation
        self._visualization_widget = QImageViewer(True)

        # Création du layout principal
        main_layout = QVBoxLayout(self)
        main_layout.add_widget(param_group_box)
        main_layout.add_widget(self._visualization_widget)

    def _draw_rectangle(self, painter: QPainter, rectangle: QRectF, pen: QPen = Qt.NoPen):
        painter.save()
        painter.set_pen(pen)
        painter.set_brush(Qt.white)
        painter.draw_rect(rectangle)
        painter.restore()


    @Slot()
    def __set_position(self,value, axis):
        if axis==0 :
            self._posX = value
        else : 
            self._posY = value
            
        self._update_from_simulation(None)
        
    @Slot()
    def _set_nb_batiments(self,value):
        self._nb_batiments = value
        self._update_from_simulation(None)
        
    @Slot()
    def _set_zone_protege(self, value):
        self._zone_protege = round((value/100)*self._nb_batiments)#IL EST POSSIBLE QUE ÇA NOUS DONNE 0 CIBLE
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


    def _update_from_simulation(self, ga: GeneticAlgorithm | None) -> None:
        image = QImage(QSize(self._width - 1, self._height - 1),
                       QImage.Format_ARGB32)

        image.fill(QBalisticProblem._background_color)
        painter = QPainter(image)
        painter.set_pen(Qt.NoPen)

        #form = self.__shapes[self._shape_picker.current_text]

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
            pen = QPen(Qt.white)
            pen.set_width(10)
            painter.set_pen(pen)
            drone = QPointF(self._posX, self._posY)
            painter.draw_point(drone)
            
            
            pass

        painter.end()
        self._visualization_widget.image = image
