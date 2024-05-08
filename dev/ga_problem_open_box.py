import numpy as np
from numpy.typing import NDArray

from gacvm import Domains, ProblemDefinition, Parameters, GeneticAlgorithm
from gaapp import QSolutionToSolvePanel

from uqtwidgets import QImageViewer, create_scroll_real_value

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QGroupBox, QGridLayout, QSizePolicy
from PySide6.QtGui import QImage, QPainter, QColor, QPolygonF, QPen, QBrush, QFont
from PySide6.QtCore import Slot, Qt, QSize, QPointF, QRectF, QSizeF

from __feature__ import snake_case, true_property



#     ___                     _                                 _     _                
#    / _ \ _ __   ___ _ __   | |__   _____  __  _ __  _ __ ___ | |__ | | ___ _ __ ___  
#   | | | | '_ \ / _ \ '_ \  | '_ \ / _ \ \/ / | '_ \| '__/ _ \| '_ \| |/ _ \ '_ ` _ \ 
#   | |_| | |_) |  __/ | | | | |_) | (_) >  <  | |_) | | | (_) | |_) | |  __/ | | | | |
#    \___/| .__/ \___|_| |_| |_.__/ \___/_/\_\ | .__/|_|  \___/|_.__/|_|\___|_| |_| |_|
#         |_|                                  |_|                                     



class QOpenBoxProblemPanel(QSolutionToSolvePanel):
    """Panel to solve the open box problem."""

    def __init__(self, width : int = 10., height : int = 5., parent : QWidget | None = None) -> None:
        super().__init__(parent)

        # create scroll bars and layouting
        self._width_scroll_bar, width_layout = create_scroll_real_value(0.1, width, 10., 1, value_suffix = ' m')
        self._height_scroll_bar, height_layout = create_scroll_real_value(0.1, height, 10., 1, value_suffix = ' m')

        param_group_box = QGroupBox('Parameters')
        param_layout = QFormLayout(param_group_box)
        param_layout.add_row('Width', width_layout)
        param_layout.add_row('Height', height_layout)
        param_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        self._width_scroll_bar.valueChanged.connect(self._update_from_configuration)
        self._height_scroll_bar.valueChanged.connect(self._update_from_configuration)

        # create visualization widget and layouting
        visualization_group_box = QGroupBox('Visualization')
        visualization_group_box.size_policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        visualization_layout = QGridLayout(visualization_group_box)
        self._visualization_widget = QImageViewer(True)
        visualization_layout.add_widget(self._visualization_widget)

        # final layouting
        layout = QVBoxLayout(self)
        layout.add_widget(param_group_box)
        layout.add_widget(visualization_group_box)
        
        # define colors for the visualization
        self._background_color = QColor(48, 48, 48)
        self._box_color = QColor(148, 164, 222)
        self._box_visualization_ratio = 0.9        

    @property
    def name(self) -> str:
        """Retourne le nom du problème."""
        return 'Open box'

    @property
    def summary(self) -> str:
        """Retourne un résumé du problème."""
        return '''Le problème de la boîte ouverte est un problème d'optimisation bien connu qui consiste à maximiser le volume d'une boiîte pouvant être formée à partir d'une surface rectangulaire.'''

    @property
    def description(self) -> str:
        """Retourne une description détaillée du problème."""
        return '''On cherche à obtenir la plus grande boîte sans couvert à partir d'une surface rectangulaire de taille fixe et connue : largeur et hauteur. L'idée consiste à déterminer la taille des coins carrés à découper pour permettre la formation de la boîte en repliant les 4 côtés restants. 

Données initiales du problème :
    - largeur et hauteur de la surface rectangulaire 
    - les deux sont définies par l'utilisateur via des barres de défilement
Dimension du problème : 1D
    - d = 1
    - d1 = ]0, coupe_maximum[
      où coupe_maximum = min(largeur, hauteur) / 2
Structure du chromosome :
    - 1 gène représentant la taille de la coupe    
Fonction objective : 
    - si la valeur recherchée est hors de la plage de recherche, la fitness est de 0 
    - le volume de la boîte obtenue en fonction de :
        - données connues : largeur x hauteur (w x h)
        - chromosome : taille de la découpe (c)
        - volume = (w - 2c) * (h - 2c) * c
'''

    @property
    def width(self) -> int:
        """Retourne la largeur de la surface rectangulaire."""
        return self._width_scroll_bar.get_real_value()

    @property
    def height(self) -> int:
        """Retourne la hauteur de la surface rectangulaire."""
        return self._height_scroll_bar.get_real_value()
    
    @property
    def maximum_cutout_size(self) -> float:
        """Retourne la taille maximale de la découpe."""
        return np.minimum(self.width, self.height) / 2. # to do : très lent pour self.width et self.height, devrait être stocké dans des variables privées

    # Voici un exemple de méthode transformant un objet de cette classe en 
    # 'callable'. Ainsi, l'instance de cette classe peut être exécutée comme
    # une fonction. On nomme ce type de méthode un 'functor'.
    #
    # On remarque que la méthode __call__ prend en argument le 'self' et est 
    # utilisé ainsi lors de son usage. 
    # panel = QOpenBoxProblemPanel()
    # panel(solution)  # <<< appel de la méthode __call__ avec 'panel' en tant 
    #                        que 'self'
    def __call__(self, chromosome : NDArray) -> float:
        """Retourne le volume de la boîte obtenue en fonction de la taille de la découpe."""
        
        cutout_size = chromosome[0]
        
        if not (0.0 < cutout_size < self.maximum_cutout_size): 
            return 0.0 # la valeur recherchée est hors de la plage de recherche, elle n'est pas intéressante
        
        return (self.width - 2. * cutout_size) * (self.height - 2. * cutout_size) * cutout_size

    @property
    def problem_definition(self) -> ProblemDefinition:
        """Retourne la définition du problème.
        
        La définition du problème inclu les domaines des chromosomes et la fonction objective.
        """
        domains = Domains(np.array([[0., self.maximum_cutout_size]]), ('Size of cutout',))
        return ProblemDefinition(domains, self)

    @property
    def default_parameters(self) -> Parameters:
        """Retourne les paramètres par défaut de l'algorithme génétique.
        
        Ces paramètres sont utilisés pour initialiser les paramètres de l'interface graphique 
        et remplace ceux en place.
        """
        engine_parameters = Parameters()
        engine_parameters.maximum_epoch = 100
        engine_parameters.population_size = 20
        engine_parameters.elitism_rate = 0.1
        engine_parameters.selection_rate = 0.75
        engine_parameters.mutation_rate = 0.25
        return engine_parameters

    def _draw_uncut_box(self, painter : QPainter, box_size : QSizeF) -> None:
        """Dessine le rectangle non coupé."""
        # calcule la moitié de la largeur et de la hauteur de la boîte pour faciliter le dessin par la suite
        box_half_width = box_size.width() / 2.
        box_half_height = box_size.height() / 2.
        
        # effectue une transformation du référentiel, dans ce cas-ci une simple translation
        painter.save()
        painter.translate(painter.device().rect().center())
        
        # dessine le rectangle
        painter.set_pen(Qt.NoPen)
        painter.set_brush(self._box_color)
        painter.draw_rect(QRectF(-box_half_width, -box_half_height, box_size.width(), box_size.height()))

        # restaure la transformation du référentiel
        painter.restore()
        
    def _draw_cut_box_v1(self, painter : QPainter, box_size : QSizeF, cutout_size : float) -> None:
        """Dessine le rectangle avec des coins coupés.
        
        Cette approche fait le dessin en 2 passes principales :
         1) dessine un rectangle principal représentant la zone rectangulaire de la boîte.
         2) dessine 4 rectangles correspondant aux coins coupés en remplissant la couleur de fond.
        """
        # calcule la moitié de la largeur et de la hauteur de la boîte pour faciliter le dessin par la suite
        box_half_width = box_size.width() / 2.
        box_half_height = box_size.height() / 2.
        
        # effectue une transformation du référentiel, dans ce cas-ci une simple translation
        painter.save()
        painter.translate(painter.device().rect().center())
        
        # 1) dessine le rectangle principal de la boîte
        painter.set_pen(Qt.NoPen)
        painter.set_brush(self._box_color)
        painter.draw_rect(QRectF(-box_half_width, -box_half_height, box_size.width(), box_size.height()))
        
        # 2) dessine les coins coupés
        painter.set_brush(self._background_color)
        painter.draw_rect(QRectF(-box_half_width              , -box_half_height              , cutout_size, cutout_size))
        painter.draw_rect(QRectF( box_half_width - cutout_size, -box_half_height              , cutout_size, cutout_size))
        painter.draw_rect(QRectF(-box_half_width              ,  box_half_height - cutout_size, cutout_size, cutout_size))
        painter.draw_rect(QRectF( box_half_width - cutout_size,  box_half_height - cutout_size, cutout_size, cutout_size))

        # restaure la transformation du référentiel
        painter.restore()
        
    def _draw_cut_box_v2(self, painter : QPainter, box_size : QSizeF, cutout_size : float) -> None:
        """Dessine le rectangle avec des coins coupés.
        
        Cette approche fait le dessin en 2 étapes :
         1) crée un polygone à 12 côtés représentant la forme rectangulaire découpée.
         2) dessine le polygone par la couleur de fond.
        """
        # calcule la moitié de la largeur et de la hauteur de la boîte pour faciliter le dessin par la suite
        box_half_width = box_size.width() / 2.
        box_half_height = box_size.height() / 2.
        
        # effectue une transformation du référentiel, dans ce cas-ci une simple translation
        painter.save()
        painter.translate(painter.device().rect().center())
        
        # 1) crée un polygone à 12 côtés représentant la forme rectangulaire découpée
        cut_polygon = QPolygonF()
        cut_polygon.append(QPointF(-box_half_width + cutout_size, -box_half_height + cutout_size))
        cut_polygon.append(QPointF(-box_half_width + cutout_size, -box_half_height              ))
        cut_polygon.append(QPointF( box_half_width - cutout_size, -box_half_height              ))
        cut_polygon.append(QPointF( box_half_width - cutout_size, -box_half_height + cutout_size))
        cut_polygon.append(QPointF( box_half_width              , -box_half_height + cutout_size))
        cut_polygon.append(QPointF( box_half_width              ,  box_half_height - cutout_size))
        cut_polygon.append(QPointF( box_half_width - cutout_size,  box_half_height - cutout_size))
        cut_polygon.append(QPointF( box_half_width - cutout_size,  box_half_height              ))
        cut_polygon.append(QPointF(-box_half_width + cutout_size,  box_half_height              ))
        cut_polygon.append(QPointF(-box_half_width + cutout_size,  box_half_height - cutout_size))
        cut_polygon.append(QPointF(-box_half_width              ,  box_half_height - cutout_size))
        cut_polygon.append(QPointF(-box_half_width              , -box_half_height + cutout_size))
        
        # 2) dessine le polygone par la couleur de fond
        painter.set_pen(Qt.NoPen)
        painter.set_brush(self._box_color)
        painter.draw_polygon(cut_polygon)
        
        # restaure la transformation du référentiel
        painter.restore()

    def _update_from_simulation(self, ga : GeneticAlgorithm | None) -> None:
        """Met à jour la visualisation de la boîte en fonction de la simulation.
        
        Note : Cette fonction est un override!.
        """
        image = QImage(QSize(self._visualization_widget.width - 1, self._visualization_widget.height - 1), QImage.Format_ARGB32)
        image.fill(self._background_color)
        painter = QPainter(image)
        painter.set_pen(Qt.NoPen)

        ratio = min(self._visualization_widget.width / self.width, self._visualization_widget.height / self.height) * self._box_visualization_ratio
        box_visualization_size = QSizeF(self.width * ratio, self.height * ratio)

        if ga: # evolving, displaying best solution
            cutout_size = ga.history.best_solution[0]
            cutout_visualization_size = cutout_size * ratio

            # self._draw_cut_box_v1(painter, box_visualization_size, cutout_visualization_size)
            self._draw_cut_box_v2(painter, box_visualization_size, cutout_visualization_size)

        else: # not evolving, meaning configuration is in process! displaying uncut box
            self._draw_uncut_box(painter, box_visualization_size)


        painter.end()
        self._visualization_widget.image = image
        
        
    @Slot()
    def _update_from_configuration(self):
        """Met à jour la visualisation de la boîte en fonction de la configuration."""
        self._update_from_simulation(None)
    