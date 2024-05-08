import numpy as np
from numpy.typing import NDArray

from gacvm import Domains, ProblemDefinition, Parameters, GeneticAlgorithm
from gaapp import QSolutionToSolvePanel

from uqtwidgets import QImageViewer, create_scroll_real_value
from umath import clamp

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QImage, QPainter, QColor, QBrush, QPen, QFontMetrics, QPolygonF, QResizeEvent
from PySide6.QtCore import Qt, QPointF, QRectF

from __feature__ import snake_case, true_property



#    _   _       _                                                      _                                 _     _                
#   | | | |_ __ | | ___ __   _____      ___ __    _ __  _   _ _ __ ___ | |__   ___ _ __   _ __  _ __ ___ | |__ | | ___ _ __ ___  
#   | | | | '_ \| |/ / '_ \ / _ \ \ /\ / / '_ \  | '_ \| | | | '_ ` _ \| '_ \ / _ \ '__| | '_ \| '__/ _ \| '_ \| |/ _ \ '_ ` _ \ 
#   | |_| | | | |   <| | | | (_) \ V  V /| | | | | | | | |_| | | | | | | |_) |  __/ |    | |_) | | | (_) | |_) | |  __/ | | | | |
#    \___/|_| |_|_|\_\_| |_|\___/ \_/\_/ |_| |_| |_| |_|\__,_|_| |_| |_|_.__/ \___|_|    | .__/|_|  \___/|_.__/|_|\___|_| |_| |_|
#                                                                                        |_|                                     



class QUnknownNumberProblemPanel(QSolutionToSolvePanel):
    """Panneau de résolution du problème de recherche d'un nombre réel inconnu.
    
    Ce panneau permet de définir le problème de recherche d'un nombre réel 
    inconnu. Une barre de défilement permet de définir la valeur recherchée 
    dans un intervalle donné.
    
    L'algorithme génétique doit trouver la valeur recherchée. Cet exemple de 
    problème à 1D est certainement le plus simple imaginable.
    """
    _background_color = QColor(48, 48, 48)
    
    _axis_text_color = QColor(22, 126, 202)
    _axis_text_width = 1.0
    _axis_pen_color = QColor(124, 192, 242)
    _axis_pen_width = 1.0
    _axis_pen = QPen(_axis_pen_color, _axis_pen_width)
    
    _best_solution_pen_color = QColor(114, 227, 86)
    _best_solution_pen_width = 1.5
    _best_solution_pen = QPen(_best_solution_pen_color, _best_solution_pen_width)
    _best_solution_brush = Qt.NoBrush
    
    _value_shape_brush = QBrush(QColor(115, 191, 96))
    _value_shape_pen = Qt.NoPen
    _value_text_color = QColor(77, 128, 64)
    _value_text_width = 1.0
    _value_test_pen = QPen(_value_text_color, _value_text_width)
    # _value_pen_color = _value_text_color.lighter(125)
    # _value_pen_width = 3.0
    # _value_pen = QPen(_value_pen_color, _value_pen_width)

    _population_solution_pen_color = QColor(128, 128, 128)
    _population_solution_pen_width = 1.0
    _population_solution_pen = QPen(_population_solution_pen_color, _population_solution_pen_width)
    
    _ref_shape_width = 35.0
    _ref_shape_height = 35.0
    _ref_shape = QPolygonF([QPointF(0.0, 0.0),
                            QPointF(-_ref_shape_width / 2.0, _ref_shape_height),
                            QPointF( _ref_shape_width / 2.0, _ref_shape_height)]) 
    

    def __init__(self, min_value : float = -1., unknown_value : float = 0., max_value : float = 1., parent : QWidget | None = None) -> None:
        """Initialise le panneau de résolution du problème de recherche d'un nombre réel inconnu.
        
        Args:
            min_value (float): Valeur minimale de la plage de recherche. Defaut à -1.0.
            value (float): Valeur recherchée. Defaut à 0.0.
            max_value (float): Valeur maximale de la plage de recherche. Defaut à 1.0.
            parent (QWidget | None): Widget parent. Defaut à None.
        """
        # Appel du constructeur de la classe parent
        super().__init__(parent)
        
        # Initialisation des valeurs minimale et maximale. La valeur recherchée 
        # est limitée à l'intervalle [min_value, max_value].
        self._min_value = min_value
        self._max_value = max(min_value, max_value)
        unknown_value = max(self._min_value, min(unknown_value, self._max_value))

        # Création de la barre de défilement pour la valeur recherchée
        self._value_scroll_bar, value_layout = create_scroll_real_value(self._min_value, unknown_value, self._max_value, 1, title = 'Valeur recherchée')
        self._value_scroll_bar.valueChanged.connect(lambda : self._update_from_simulation(None))
        # Création de la zone de visualisation
        self._visualization_widget = QImageViewer(True)
        
        # Mise en place de la disposition des widgets
        main_layout = QVBoxLayout(self)
        main_layout.add_layout(value_layout)
        main_layout.add_widget(self._visualization_widget)

    @property
    def unknown_value(self) -> float:
        """La valeur recherchée par l'algorithme génétique."""
        return self._value_scroll_bar.get_real_value()

    @property
    def name(self) -> str: # note : override
        """Nom du problème."""
        return 'Unknown Number'

    @property
    def summary(self) -> str: # note : override
        """Résumé du problème."""
        return '''On recherche une valeur réelle prédéterminée mais inconue par l'algorithme génétique.'''

    @property
    def description(self) -> str: # note : override
        """Description du problème."""
        return '''On cherche à obtenir une valeur réelle prédéterminée mais inconnue.

Données initiales du problème : 
    - zone de recherche : donnée à même le constructeur par les arguments 'min_value' et "max_value"
    - unknown : la valeur à rechercher (un réel) déterminé par la barre de défilement
Dimension du problème : 
    - d = 1
    - d1 = [min_value, max_value]
Structure du chromosome :
    - 1 gène représentant la valeur recherchée
Fonction objective :
    - si la valeur recherchée est hors de la plage de recherche, la fitness est de 0 
    - la distance entre unknown et la solution courante
    - puisqu'on recherche la distance la plus petite, cette dernière est inversée pour garantir une maximisation
'''

    @property
    def problem_definition(self) -> ProblemDefinition: # note : override
        # Voici un exemple de définition de fonction interne permettant de 
        # définir la fonction objective. Cette fonction est définie dans la 
        # méthode problem_definition. Elle est utilisée pour définir la 
        # fonction objective du problème. Elle est définie ici pour des raisons 
        # de clarté et de localité.
        #
        # On remarque que cette fonction n'est pas une méthode. De plus, elle 
        # exploite le concept de fermeture pour accéder à la valeur de 
        # unknown_value. La notion de fermeture ('closure' en anglais) est un 
        # concept de programmation fonctionnelle permettant la capture de 
        # variables locales d'un contexte pour les utiliser ultérieurement et,
        # dans ce cas-ci, dans une fonction imbriquée. C'est un sujet plus 
        # avancé qui sera abordé à la prochaine session.
        def objective_fonction(chromosome : NDArray) -> float: # fonction objective
            """Évalue un chromosome. 
            
            La fonction de fitness est la distance entre la valeur recherchée et le
            chromosome. Puisque la fonction objective doit être maximisée, vers le 
            maximum, la distance est inversée en fonction de ladistance maximale 
            possible.
            """
            unknown_value = self.unknown_value
            if not (self._min_value <= unknown_value <= self._max_value):
                return 0.0 # la valeur recherchée est hors de la plage de recherche, elle n'est pas intéressante
            
            maximum_distance = max(abs(self._min_value - unknown_value), abs(self._max_value - unknown_value))
            current_value_estimation = chromosome[0]
            return max(0., maximum_distance - abs(unknown_value - current_value_estimation))        
        
        domains = Domains(np.array([[self._min_value, self._max_value]]), ('Valeur recherchée',))
        return ProblemDefinition(domains, objective_fonction)

    @property
    def default_parameters(self) -> Parameters: # note : override
        engine_parameters = Parameters()
        engine_parameters.maximum_epoch = 50
        engine_parameters.population_size = 10
        engine_parameters.elitism_rate = 0.1
        engine_parameters.selection_rate = 0.9
        engine_parameters.mutation_rate = 0.1
        return engine_parameters
    
    def resize_event(self, event : QResizeEvent) -> None: # note : override venant de QWidget
        """Appelé lors du redimensionnement du panneau -> on redessine puisque le dessin est proportionnel au widget."""
        super().resize_event(event)
        self._update_from_simulation(None)
    
    def _update_from_simulation(self, ga : GeneticAlgorithm | None = None) -> None: # note : override
        # Création de l'image de visualisation
        image = QImage(self._visualization_widget.size, QImage.Format_ARGB32)
        image.fill(QUnknownNumberProblemPanel._background_color)
        painter = QPainter(image)

        # Dessine les textes
        self._draw_axis_text(painter)

        # Calcul les éléments de transformation pour simplifier les calculs ultérieurs
        x_scale = image.width() / (self._max_value - self._min_value)
        y_scale = image.height() / 2.
        x_translate = image.width() / 2.0
        y_translate = image.height() / 2.0
        
        # Dessine l'axe horizontal de référence
        painter.set_pen(QUnknownNumberProblemPanel._axis_pen)
        QUnknownNumberProblemPanel._draw_line(painter, self._min_value, 0., self._max_value, 0., x_translate, y_translate, x_scale, y_scale)
        
        # Dessine le triangle pointant la valeur recherchée
        painter.set_pen(QUnknownNumberProblemPanel._value_shape_pen)
        painter.set_brush(QUnknownNumberProblemPanel._value_shape_brush)
        QUnknownNumberProblemPanel._draw_ref_shape(painter, self.unknown_value, x_translate, y_translate, x_scale, y_scale, False)
        # Dessine le texte
        painter.set_pen(QUnknownNumberProblemPanel._value_test_pen)
        value_text = f'Unknown : {self.unknown_value:0.1f}'
        font_metrics = QFontMetrics(painter.font())
        text_width = font_metrics.horizontal_advance(value_text)
        text_half_width = text_width / 2.
        text_position = QUnknownNumberProblemPanel._to_point(self.unknown_value, 0.0, x_translate, y_translate, x_scale, y_scale)
        text_position += QPointF(-text_half_width, QUnknownNumberProblemPanel._ref_shape_height + font_metrics.height())
        text_position.set_x(clamp(0.0, text_position.x(), self._visualization_widget.width - text_width))
        painter.draw_text(text_position, value_text)   
        

        if ga:
            # Dessine toute la population sauf la meilleure solution
            painter.set_pen(QUnknownNumberProblemPanel._population_solution_pen)
            for chromosome in ga.population: # ga.population[1:] si on ne veut pas dessiner la première car 0 est la meilleure solution
                current_value = chromosome[0]
                QUnknownNumberProblemPanel._draw_line(painter, current_value, -0.75, current_value, 0.75, x_translate, y_translate, x_scale, y_scale)
            
            # Dessine la meilleure solution
            painter.set_pen(QUnknownNumberProblemPanel._best_solution_pen)
            painter.set_brush(QUnknownNumberProblemPanel._best_solution_brush)
            best_solution = ga.population[0] # les données sont triées par ordre décroissant de fitness
            # vvv une autre approche pour obtenir la meilleure solution vvv
            # best_solution = ga.history.best_solution # on prends la meilleure solution de l'historique
            # ^^^                                                       ^^^
            best_value = best_solution[0]
            QUnknownNumberProblemPanel._draw_ref_shape(painter, best_value, x_translate, y_translate, x_scale, y_scale, True)

        painter.end()

        self._visualization_widget.image = image
    
    # vvvvv fonctions privées utilitaires pour les dessins vvvvv
    @staticmethod
    def _to_point(x : float, y : float, xtranslate : float, ytranslate : float, xscale : float, yscale : float) -> QPointF:
        return QPointF(x * xscale + xtranslate, y * yscale + ytranslate)

    @staticmethod
    def _to_points(x1 : float, y1 : float, x2 : float, y2 : float, xtranslate : float, ytranslate : float, xscale : float, yscale : float) -> tuple[QPointF, QPointF]:
        return (QUnknownNumberProblemPanel._to_point(x1, y1, xtranslate, ytranslate, xscale, yscale),
                QUnknownNumberProblemPanel._to_point(x2, y2, xtranslate, ytranslate, xscale, yscale))

    @staticmethod
    def _draw_line(painter : QPainter, x1 : float, y1 : float, x2 : float, y2 : float, xtranslate : float, ytranslate : float, xscale : float, yscale : float) -> None:
        p1, p2 = QUnknownNumberProblemPanel._to_points(x1, y1, x2, y2, xtranslate, ytranslate, xscale, yscale)
        painter.draw_line(p1, p2)
        
    @staticmethod
    def _draw_ref_shape(painter : QPainter, x_position : float, x_translate : float, y_translate : float, x_scale : float, y_scale : float, vflip : bool) -> None:
        painter.save()
        ref_shape_x_pos = QUnknownNumberProblemPanel._to_point(x_position, 0.0, x_translate, y_translate, x_scale, y_scale)
        painter.translate(ref_shape_x_pos.x(), ref_shape_x_pos.y())
        if vflip:
            painter.scale(1.0, -1.0)
        painter.draw_polygon(QUnknownNumberProblemPanel._ref_shape)
        painter.restore()    

    def _draw_axis_text(self, painter : QPainter) -> None:
        painter.set_pen(QPen(QUnknownNumberProblemPanel._axis_text_color, 
                             QUnknownNumberProblemPanel._axis_text_width))
        rect = QRectF(0., self._visualization_widget.height / 2., self._visualization_widget.width, self._visualization_widget.height / 2.)
        painter.draw_text(rect, Qt.AlignLeft | Qt.AlignTop, f'{self._min_value:0.1f}') # le texte à gauche
        painter.draw_text(rect, Qt.AlignHCenter | Qt.AlignTop, f'{(self._max_value + self._min_value) / 2.:0.1f}') # le texte au centre
        painter.draw_text(rect, Qt.AlignRight | Qt.AlignTop, f'{self._max_value:0.1f}') # le texte à droite


