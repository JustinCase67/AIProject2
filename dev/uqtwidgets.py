#     ___  _ __        ___     _            _               _   _ _ _ _   _           
#    / _ \| |\ \      / (_) __| | __ _  ___| |_ ___   _   _| |_(_) (_) |_(_) ___  ___ 
#   | | | | __\ \ /\ / /| |/ _` |/ _` |/ _ \ __/ __| | | | | __| | | | __| |/ _ \/ __|
#   | |_| | |_ \ V  V / | | (_| | (_| |  __/ |_\__ \ | |_| | |_| | | | |_| |  __/\__ \
#    \__\_\\__| \_/\_/  |_|\__,_|\__, |\___|\__|___/  \__,_|\__|_|_|_|\__|_|\___||___/
#                                |___/                                                



from math import log10
from umath import clamp
from random import randint, uniform

from PySide6.QtCore import Qt, Slot, Signal, QSize, QPointF
from PySide6.QtWidgets import (QWidget, QLabel, QScrollBar, QPushButton,
                               QHBoxLayout, QSizePolicy)
from PySide6.QtGui import QPaintEvent, QPainter, QPen, QBrush, QColor, QImage

from __feature__ import snake_case, true_property




def create_scroll_int_value(minimum_value : int,
                            initial_value : int, 
                            maximum_value : int, 
                            title : None | str | tuple[str, str] | list[str, str] = None, # tuple[str, str] = (title, tooltip)
                            value_prefix : str = "", 
                            value_suffix : str = "", 
                            sb_min_width : int = 150, 
                            value_width : int = 50, 
                            default_width : int = 25) -> tuple[QScrollBar, QHBoxLayout]:
    """
    Crée et retourne un assemblage de widgets facilitant la gestion d'un nombre entier.
    
    L'assemblage contient :
    - optionnellement, un titre (QLabel)
    - une barre de défilement horizontale (QScrollBar)
    - une étiquette de valeur (QLabel)
    - deux boutons (QPushButton) permettant définir la valeur par défaut et
      une valeur aléatoires
    - le tout assemblé dans un QHBoxLayout.
    
    L'objectif est de gérer facilement une valeur entière entre 'minimum_value' et 
    'maximum_value'. Les valeurs 'minimum_value' et 'maximum_value' sont ajustées pour 
    s'assurer que 'minimum_value' ne soit pas supérieure à 'maximum_value' et que 
    'initial_value' se situe entre ces deux limites. 
    
    Optionnellement, il est possible d'afficher un préfixe et un suffixe 
    personnalisés avec l'affichage du nombre.

    Paramètres :
        min_val (int): La valeur minimale autorisée pour la barre de défilement.
        init_val (int): La valeur initiale de la barre de défilement. Ajustée entre min_val et max_val si nécessaire.
        max_val (int): La valeur maximale autorisée pour la barre de défilement.
        title (str, optionnel): Titre à afficher avant la barre de défilement. Si 'None', aucun titre n'est ajouté. Par défaut, aucun titre.
        value_prefix (str, optionnel): Préfixe à afficher devant la valeur sur le QLabel. Par défaut, aucune chaîne.
        value_suffix (str, optionnel): Suffixe à afficher après la valeur sur le QLabel. Par défaut, aucune chaîne.
        sb_min_width (int, optionnel): Largeur minimale pour la QScrollBar. Par défaut, 150 pixels.
        value_width (int, optionnel): Largeur fixe pour le QLabel. Par défaut, 50 pixels.
        default_width (int, optionnel): Largeur fixe pour les QPushButton. Par défaut, 25 pixels.

    Retour :
        tuple: Contient la QScrollBar et le QHBoxLayout configurés avec les widgets intégrés.
        Le QScrollBar permet d'accéder à la valeur et le 'layout' facilite l'intégration dans une interface graphique. 

    Exemple d'utilisation :
        scroll_bar, layout = create_scroll_int_value(0, 50, 100)
    """    
    
    minimum_value = min(minimum_value, maximum_value)
    maximum_value = max(minimum_value, maximum_value)
    initial_value = clamp(minimum_value, initial_value, maximum_value)

    scroll_bar = QScrollBar()
    scroll_bar.orientation = Qt.Horizontal
    scroll_bar.set_range(minimum_value, maximum_value)
    scroll_bar.minimum_width = sb_min_width
    scroll_bar.value = initial_value

    value_label = QLabel()
    value_label.set_fixed_width(value_width)
    value_label.alignment = Qt.AlignCenter
    value_label.set_buddy(scroll_bar)

    default_button = QPushButton('!')
    default_button.set_fixed_width(default_width)
    default_button.tool_tip = f'Reset to default value : {initial_value}'

    random_button = QPushButton('?')
    random_button.set_fixed_width(default_width)
    random_button.tool_tip = f'Randomize value between {minimum_value} and {maximum_value}.'

    layout = QHBoxLayout()
    if title is not None:
        if isinstance(title, (tuple, list)) and len(title) == 2 and all(isinstance(t, str) for t in title):
            title_label = QLabel(title[0])
            title_label.tool_tip = title[1]
        elif isinstance(title, str):
            title_label = QLabel(title)
        else:
            raise TypeError(f'Invalid title type [None, str, tuple[str, str], list[str, str]]: {type(title)}')
        title_label.size_policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout.add_widget(title_label)
    layout.add_widget(scroll_bar)
    layout.add_widget(value_label)
    layout.add_widget(default_button)
    layout.add_widget(random_button)

    update_function = lambda value: setattr(value_label, 'text', f'{value_prefix}{value}{value_suffix}')
    update_function(initial_value)
    scroll_bar.valueChanged.connect(update_function)
    default_button.clicked.connect(lambda : setattr(scroll_bar, 'value', initial_value))
    random_button.clicked.connect(lambda : setattr(scroll_bar, 'value', randint(minimum_value, maximum_value)))

    return scroll_bar, layout


    
def create_scroll_real_value(minimum_value : float, 
                             initial_value : float, 
                             maximum_value : float, 
                             precision : int, 
                             display_multiplier : float = 1., 
                             title : None | str | tuple[str, str] | list[str, str] = None, # tuple[str, str] = (title, tooltip)
                             value_prefix : str = "", 
                             value_suffix : str = "", 
                             sb_min_width : int = 150, 
                             value_width : int = 50, 
                             default_width : int = 25) -> tuple[QScrollBar, QHBoxLayout]:
    """
    Crée et retourne un assemblage de widgets facilitant la gestion d'un nombre réel.
    
    L'assemblage contient :
    - optionnellement, un titre (QLabel)
    - une barre de défilement horizontale (QScrollBar)
    - une étiquette de valeur (QLabel)
    - deux boutons (QPushButton) permettant définir la valeur par défaut et
      une valeur aléatoires
    - le tout assemblé dans un QHBoxLayout.    
    
    L'objectif est de gérer facilement une valeur réelle entre 'minimum_value' et 
    'maximum_value'. Les valeurs 'minimum_value' et 'maximum_value' sont ajustées pour 
    s'assurer que 'minimum_value' ne soit pas supérieure à 'maximum_value' et que 
    'initial_value' se situe entre ces deux limites. 
    
    Optionnellement, il est possible d'afficher un préfixe et un suffixe 
    personnalisés avec l'affichage du nombre.
    
    L'object 'scroll_bar' créé est modifié et étendu avec deux nouvelle méthodes 
    accesseur/mutateur du nombre réel  :
    - 'scroll_bar.set_real_value'
    - 'scroll_bar.get_real_value'

    Paramètres :
        minimum_value (float): La valeur minimale possible de la barre de défilement.
        initial_value (float): La valeur initiale de la barre de défilement. Sera ajustée entre min_val et max_val.
        maximum_value (float): La valeur maximale possible de la barre de défilement.
        precision (int): La précision des valeurs réelles, définissant le nombre de décimales.
        display_multiplier (float, optionnel): Un multiplicateur pour la valeur affichée. Par défaut à 1.0.
        title (str, optionnel): Titre à afficher avant la barre de défilement. Si 'None', aucun titre n'est ajouté. Par défaut, aucun titre.
        value_prefix (str, optionnel): Un préfixe à ajouter avant la valeur affichée. Par défaut, aucune chaîne.
        value_suffix (str, optionnel): Un suffixe à ajouter après la valeur affichée. Par défaut, aucune chaîne.
        sb_min_width (int, optionnel): La largeur minimale de la barre de défilement (QScrollBar). Par défaut à 150 pixels.
        value_width (int, optionnel): La largeur fixe pour l'étiquette de la valeur (QLabel). Par défaut à 50 pixels.
        default_width (int, optionnel): La largeur fixe pour les boutons (QPushButton). Par défaut à 25 pixels.

    Retour :
        tuple: Un tuple contenant la QScrollBar configurée et le QHBoxLayout avec les widgets intégrés.

    Exemple d'utilisation :
        scroll_bar, layout = create_scroll_real_value(0.0, 0.5, 1.0, 2)
    """
    minimum_value : int = min(minimum_value, maximum_value)
    maximum_value : int = max(minimum_value, maximum_value)
    initial_value = clamp(minimum_value, initial_value, maximum_value)

    resolution = 10 ** precision
    resolution_format = round(precision - log10(display_multiplier))
    format_string = f'.{resolution_format}f' if resolution_format > 0 else 'g'
    scroll_bar = QScrollBar()
    scroll_bar.orientation = Qt.Horizontal
    scroll_bar.set_range(0, round((maximum_value - minimum_value) * resolution))
    scroll_bar.minimum_width = sb_min_width

    value_label = QLabel()
    value_label.set_fixed_width(value_width)
    value_label.alignment = Qt.AlignCenter
    value_label.set_buddy(scroll_bar)

    default_button = QPushButton('!')
    default_button.set_fixed_width(default_width)
    default_button.tool_tip = f'Reset to default value : {value_prefix}{initial_value:{format_string}}{value_suffix}'

    random_button = QPushButton('?')
    random_button.set_fixed_width(default_width)
    random_button.tool_tip = f'Randomize value between {minimum_value:0.3f} and {maximum_value:0.3f}.'

    layout = QHBoxLayout()
    if title is not None:
        if isinstance(title, (tuple, list)) and len(title) == 2 and all(isinstance(t, str) for t in title):
            title_label = QLabel(title[0])
            title_label.tool_tip = title[1]
        elif isinstance(title, str):
            title_label = QLabel(title)
        else:
            raise TypeError(f'Invalid title type [None, str, tuple[str, str], list[str, str]]: {type(title)}')
        title_label.size_policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout.add_widget(title_label)
    layout.add_widget(scroll_bar)
    layout.add_widget(value_label)
    layout.add_widget(default_button)
    layout.add_widget(random_button)

    # not entirely tested... to do
    scroll_bar.set_real_value = lambda value : setattr(scroll_bar, 'value', round((value - minimum_value) * resolution))
    scroll_bar.get_real_value = lambda : scroll_bar.value / resolution + minimum_value
    update_function = lambda _: setattr(value_label, 'text', f'{value_prefix}{scroll_bar.get_real_value() * display_multiplier:{format_string}}{value_suffix}')
    
    scroll_bar.set_real_value(initial_value)
    update_function(initial_value)
    scroll_bar.valueChanged.connect(update_function)
    default_button.clicked.connect(lambda : scroll_bar.set_real_value(initial_value))
    random_button.clicked.connect(lambda : scroll_bar.set_real_value(uniform(minimum_value, maximum_value)))

    return scroll_bar, layout




class QImageViewer(QWidget):
    """
    Un widget spécialisé pour l'affichage d'une image.
    
    L'image est toujours centrée dans le widget et redimensionnée pour s'adapter à la taille du widget.
    
    Si aucune image n'est définie, un texte '--- no image ---' est affiché au centre du widget.

    Propriétés :
        image : Accesseur et mutateur pour l'image actuellement affichée dans le visualiseur. 
                Lorsque l'image est mise à jour, le widget est re-dessiné et le signal image_changed est émis.

    Signaux :
        imageChanged : Un signal Qt qui est émis chaque fois que l'image du visualiseur change.
        
    Connexions :
        set_image : Un slot pour définir l'image du visualiseur. Peut être connecté à un signal Qt.

    Utilisation typique :
        viewer = QImageViewer()
        viewer.image = QImage("chemin/vers/image.png")
        viewer.show()

    Note :
        La méthode `paint_event` est protégée par convention et ne devrait pas être appelée directement.
        Utilisez la méthode `update` pour déclencher un événement de mise à jour si nécessaire.

    """

    imageChanged = Signal(QImage)

    def __init__(self, smooting_image : bool = False, parent : QWidget | None = None) -> None:
        super().__init__(parent)
        self._smoothing_image_option = Qt.SmoothTransformation if smooting_image else Qt.FastTransformation
        self._default_background_brush = QBrush(QColor(64, 64, 64))
        self._no_image_text_pen = QPen(QColor(128, 128, 128))

        self.clear()
        
    @property
    def image(self) -> QImage:
        """L'image affichée au centre du widget."""
        return self._image

    @image.setter
    def image(self, value : QImage) -> None:
        self._image = value
        self.update()
        self.imageChanged.emit(self._image)

    @Slot()
    def set_image(self, image : QImage) -> None:
        """Connecteur définissant l'image à afficher."""
        self.image = image # call the setter
        
    def clear(self) -> None:
        """Efface l'image actuellement affichée."""
        self.image = QImage(QSize(), QImage.Format_ARGB32) # call the setter
    
    def paint_event(self, event : QPaintEvent) -> None:
        """Redessine le widget avec l'image actuelle ou un texte 'no image' si aucune image n'est définie.
        
        ATTENTION : Conceptuellement, cette méthode est protégée et ne devrait pas être appelée directement.
        """
        painter = QPainter(self)
        painter.set_render_hint(QPainter.Antialiasing)
        painter.set_background(self._default_background_brush)
        painter.erase_rect(self.rect)
        
        if self._image.is_null():
            painter.set_pen(self._no_image_text_pen)
            painter.draw_text(self.rect, Qt.AlignCenter, "--- no image ---")
        else:
            image = self._image.scaled(self.size, Qt.KeepAspectRatio, self._smoothing_image_option)
            painter.draw_image(QPointF((self.width - image.width())/2., (self.height - image.height())/2.), image)

        painter.end()





