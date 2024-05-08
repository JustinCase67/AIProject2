from abc import ABC, abstractmethod

from gacvm import GeneticAlgorithm, Observer, ProblemDefinition, Parameters
from gacvm import SelectionStrategy, CrossoverStrategy, MutationStrategy
from gacvm import RouletteWheelSelectionStrategy, WeightedAverageCrossoverStrategy, GeneMutationStrategy

import uqtwidgets

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, QObject, Signal, Slot, QPointF, QMargins, QSignalBlocker
from PySide6.QtWidgets import  (QApplication, QMainWindow, QWidget,
                                QLabel, QComboBox, QPushButton, QPlainTextEdit, QCheckBox,
                                QGroupBox, QSplitter, QTabWidget,
                                QGridLayout, QHBoxLayout, QVBoxLayout, QFormLayout, QSizePolicy,
                                QMessageBox,
                                QSizePolicy)
from PySide6.QtGui import QIcon, QPainter, QPen, QColor

from __feature__ import snake_case, true_property




# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#     ___  ____        _       _   _           _____    ____        _           ____                  _                            
#    / _ \/ ___|  ___ | |_   _| |_(_) ___  _ _|_   _|__/ ___|  ___ | |_   _____|  _ \ __ _ _ __   ___| |                           
#   | | | \___ \ / _ \| | | | | __| |/ _ \| '_ \| |/ _ \___ \ / _ \| \ \ / / _ \ |_) / _` | '_ \ / _ \ |                           
#   | |_| |___) | (_) | | |_| | |_| | (_) | | | | | (_) |__) | (_) | |\ V /  __/  __/ (_| | | | |  __/ |                           
#    \__\_\____/ \___/|_|\__,_|\__|_|\___/|_| |_|_|\___/____/ \___/|_| \_/ \___|_|   \__,_|_| |_|\___|_|                           
#     | |                                                                                                                          
#     | |                                                                                                                          
#     | |                                                                                                                          
#   __| |__                                                                                                                        
#   \ \_/ /                                                                                                                        
#    \ V /                                                                                                                         
#    _\_/                                                        _ _           _   _  __              _            _             _ 
#   |  _ \ __ _ _ __  _ __   ___  __ _ _   _    __ _ _ __  _ __ | (_) ___ __ _| |_(_)/ _|  _ __  _ __(_)_ __   ___(_)_ __   __ _| |
#   | |_) / _` | '_ \| '_ \ / _ \/ _` | | | |  / _` | '_ \| '_ \| | |/ __/ _` | __| | |_  | '_ \| '__| | '_ \ / __| | '_ \ / _` | |
#   |  __/ (_| | | | | | | |  __/ (_| | |_| | | (_| | |_) | |_) | | | (_| (_| | |_| |  _| | |_) | |  | | | | | (__| | |_) | (_| | |
#   |_|   \__,_|_| |_|_| |_|\___|\__,_|\__,_|  \__,_| .__/| .__/|_|_|\___\__,_|\__|_|_|   | .__/|_|  |_|_| |_|\___|_| .__/ \__,_|_|
#                                                   |_|   |_|                             |_|                       |_|            
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class QSolutionToSolvePanel(QWidget): # to do : should inherit from ABC : see https://stackoverflow.com/questions/28799089/python-abc-multiple-inheritance
    """
    Classe abstraite représentant un panneau de l'interface utilisateur 
    permettant de résoudre un problème spécifique.
    
    Cette classe est destinée à être héritée afin de définir des panneaux 
    personnalisés représentant différents types de problèmes. 

    Chaque sous-classe doit impérativement implémenter les propriétés et méthodes abstraites
    suivantes pour assurer une intégration correcte :
        - name (propriété) : Un nom court et descriptif du problème.
        - summary (propriété) : Un résumé concis du problème, généralement de 1 à 3 phrases.
        - description (propriété) : Un texte détaillé expliquant le problème en profondeur.
        - problem_definition (propriété) : Un objet définissant le problème à résoudre.
        - default_parameters (propriété) : Les paramètres par défaut pour l'algorithme génétique.
        - _update_from_simulation (méthode) : Une méthode protégée pour mettre à jour l'interface utilisateur en fonction de l'état actuel de la simulation.

    Remarques :
        - L'implémentation détaillée de chaque propriété et méthode abstraite 
          dépendra de la nature spécifique du problème à résoudre.
        - Les méthodes et propriétés abstraites assurent que chaque sous-classe 
          fournit les informations nécessaires pour une intégration cohérente 
          dans l'application graphique.
        - La méthode _update_from_simulation doit être conçue pour gérer les cas 
          où l'objet 'ga' (représentant l'algorithme génétique) est None, 
          permettant ainsi une initialisation de l'interface lors de 
          l'initialisation (avant l'évolution).
    """    
    def __init__(self, parent : QWidget = None) -> None: 
        super().__init__(parent)

    @property
    @abstractmethod
    def name(self) -> str:
        '''
        Retourne un nom court et compact représentant le problème à résoudre.
        Ce nom est affiché dans l'onglet de sélection de problème.
        '''
        raise NotImplementedError()

    @property
    @abstractmethod
    def summary(self) -> str:
        '''
        Retourne un court texte décrivant les grandes lignes du problèmes - typiquement 1 à 3 phrases.
        Ce sommaire est affiché en haut de la fenêtre de résolution du problème.
        '''
        raise NotImplementedError()

    @property
    @abstractmethod
    def description(self) -> str:
        '''
        Retourne un texte descriptif expliquant les détails du problème.
        Cette description est affichée dans une autre fenêtre lorsqu'on appui sur le bouton en haut à droite.
        '''
        raise NotImplementedError()

    @property
    @abstractmethod
    def problem_definition(self) -> ProblemDefinition:
        '''
        Retourne un objet complet de définition du problème. L'objet retourné est celui qui sera résoud par l'algorithme génétique.
        '''
        raise NotImplementedError()

    @property
    @abstractmethod
    def default_parameters(self) -> Parameters:
        '''
        Retourne un objet de paramètres de l'algorithme génétique. Ces valeurs seront utilisée pour initialiser la liste des paramètres à gauche dans l'interface utilisateur.
        '''
        raise NotImplementedError()

    @abstractmethod
    def _update_from_simulation(self, ga : GeneticAlgorithm | None) -> None:
        '''
        Fonction utilitaire permettant de donner du 'feedback' pour chaque pas de simulation. Il faut gérer le cas où ga est None. Lorsque ga est None, on donne un feedback d'initialisation sans aucune évolution.
        '''
        raise NotImplementedError()

    @Slot()
    def update_solution(self, ga : GeneticAlgorithm) -> None:
        """Slot provoquant la mise à jour de l'interface utilisateur du panneau.
        
        Attention, cette fonction n'est pas destinée à être 'override'."""
        self._update_from_simulation(ga)








# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#       _       _             _        _                                  
#      / \   __| | __ _ _ __ | |_ __ _| |_ ___ _   _ _ __                 
#     / _ \ / _` |/ _` | '_ \| __/ _` | __/ _ \ | | | '__|                
#    / ___ \ (_| | (_| | |_) | || (_| | ||  __/ |_| | |                   
#   /_/   \_\__,_|\__,_| .__/ \__\__,_|\__\___|\__,_|_|                   
#                      |_|               __               __     ___  _   
#     __ _  __ _  _____   ___ __ ___    / /____ _____ ____\ \   / _ \| |_ 
#    / _` |/ _` |/ __\ \ / / '_ ` _ \  / /_____|_____|_____\ \ | | | | __|
#   | (_| | (_| | (__ \ V /| | | | | | \ \_____|_____|_____/ / | |_| | |_ 
#    \__, |\__,_|\___| \_/ |_| |_| |_|  \_\               /_/   \__\_\\__|
#    |___/                                                                
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Classe permettant de faire le lien entre 2 bibliothèques pas 
# nécessairement destinées à être utilisée ensemble : 
# - gacvm : bibliothèque de calculs pour les algorithmes génétiques
# - PySide6 : bibliothèque de développement d'interfaces graphiques Qt
# 
# Qt offre un système de signaux et de slots pour la communication qui n'est 
# pas exploité dans gacvm. QGAAdapter s'occupe d'encapsuler la logique de 
# gacvm dans un objet qui émet des signaux Qt pour communiquer avec 
# l'interface utilisateur.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class QGAAdapter(QObject):
    """
    Cette classe sert d'adaptateur pour intégrer un algorithme génétique, 
    défini dans la bibliothèque 'gacvm', dans une application Qt. Elle hérite 
    de QObject pour permettre une intégration fluide avec le système de 
    signaux et de slots de Qt.

    Attributs:
        genetic_algorithm (gacvm.GeneticAlgorithm): Instance de l'algorithme 
        génétique utilisé pour les opérations d'évolution.
    
    Signaux:
        started: Signal émis au début du processus d'évolution.
        ended: Signal émis à la fin du processus d'évolution.
        evolved: Signal émis à chaque mise à jour de l'état de l'algorithme génétique.
        reseted: Signal émis lors de la réinitialisation de l'algorithme avec de nouveaux paramètres ou une nouvelle définition de problème.

    Propriétés:
        parameters: Accès en lecture/écriture aux paramètres de l'algorithme génétique.
        problem_definition: Accès en lecture/écriture à la définition du problème pour l'algorithme génétique.
        state: Accès en lecture à l'état courant de l'algorithme génétique.
        has_evolved: Accès en lecture à l'indicateur de progression de l'algorithme génétique.

    Méthodes Publiques:
        evolve(): Lance le processus d'évolution de l'algorithme génétique.
        evolve_one_step(): Effectue une seule itération d'évolution de l'algorithme génétique.
        stop(): Arrête l'exécution de l'algorithme génétique.
        pause(): Met en pause l'exécution de l'algorithme génétique.
        resume(): Reprend l'exécution de l'algorithme génétique après une pause.
        reset(default_parameters, problem_definition): Réinitialise l'algorithme avec de nouveaux paramètres et une nouvelle définition du problème.

    Sous-classes:
        _SignalEmitter: Classe interne servant de pont entre les mises à jour de l'algorithme génétique et les signaux Qt.
    """

    started = Signal()
    ended = Signal()
    evolved = Signal()
    reseted = Signal()

    class _SignalEmitter(Observer):
        def __init__(self, adapter):
            super().__init__()
            self._adapter = adapter

        def update(self, engine):
            if self._adapter.state != GeneticAlgorithm.State.PAUSED: # prevent useless update if paused
                self._adapter.evolved.emit()
            QApplication.process_events() # monothread simplification -> should be multithreaded or, at least, managed with Qt's signal

    def __init__(self) -> None:
        super().__init__()
        self.genetic_algorithm = GeneticAlgorithm()
        self.genetic_algorithm.add_observer(QGAAdapter._SignalEmitter(self))

    @property
    def parameters(self) -> Parameters:
        return self.genetic_algorithm.parameters

    @parameters.setter
    def parameters(self, value : Parameters) -> None:
        self.genetic_algorithm.parameters = value

    @property
    def problem_definition(self) -> ProblemDefinition:
        return self.genetic_algorithm.problem_definition

    @problem_definition.setter
    def problem_definition(self, value : ProblemDefinition) -> None:
        self.genetic_algorithm.problem_definition = value

    @property
    def state(self) -> GeneticAlgorithm.State:
        return self.genetic_algorithm.state
    
    @property
    def has_evolved(self) -> bool:
        return self.genetic_algorithm.has_evolved

    def evolve(self) -> None:
        self.started.emit()
        self.genetic_algorithm.evolve()
        self.ended.emit()
        
    def evolve_one_step(self) -> None:
        self.genetic_algorithm.evolve_one()

    def stop(self) -> None:
        self.genetic_algorithm.stop()

    def pause(self) -> None:
        self.genetic_algorithm.pause()

    def resume(self) -> None:
        self.genetic_algorithm.resume()

    def reset(self, default_parameters : Parameters, problem_definition : ProblemDefinition) -> None:
        self.parameters = default_parameters
        self.problem_definition = problem_definition
        self.genetic_algorithm.reset()
        self.reseted.emit()







# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#    ____                                                      _            _                        
#   |  _ \ __ _ _ __  _ __   ___  __ _ _   ___  __  _ __  _ __(_)_ __   ___(_)_ __   __ _ _   ___  __
#   | |_) / _` | '_ \| '_ \ / _ \/ _` | | | \ \/ / | '_ \| '__| | '_ \ / __| | '_ \ / _` | | | \ \/ /
#   |  __/ (_| | | | | | | |  __/ (_| | |_| |>  <  | |_) | |  | | | | | (__| | |_) | (_| | |_| |>  < 
#   |_|   \__,_|_| |_|_| |_|\___|\__,_|\__,_/_/\_\ | .__/|_|  |_|_| |_|\___|_| .__/ \__,_|\__,_/_/\_\
#                                                  |_|                       |_|                     
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -



class QGAControlWidget(QGroupBox):

    # Signals are available from this control panel
    # But, in most case, the user should use the signals emitted from QGAAdapter!
    started = Signal()
    stopped = Signal()
    paused = Signal()
    resumed = Signal()

    def __init__(self, ga_adapter, solution_panels, parent=None):
        super().__init__(parent)

        self.title = 'Control'
        self._ga_adapter = ga_adapter
        self._solution_panels = solution_panels

        self._state_machine_info = {
                # index, start_btn_enab, pause_btn_enab, start_btn_txt, pause_btn_txt, start_nxt_state, pause_nxt_state, text 
                GeneticAlgorithm.State.IDLE : (0, True, False, 'Start', 'Pause', 'RUNNING', 'IDLE', 'Idle'),
                GeneticAlgorithm.State.RUNNING : (1, True, True, 'Stop', 'Pause', 'IDLE', 'PAUSED', 'Running'),
                GeneticAlgorithm.State.PAUSED : (2, True, True, 'Stop', 'Resume', 'IDLE', 'RUNNING', 'Paused')                    
            }

        self._start_stop_button = QPushButton()
        self._pause_resume_button = QPushButton()
        self._single_step_button = QPushButton()
        self._start_stop_button.size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._pause_resume_button.size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._single_step_button.size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._current_state_label = QLabel()
        self._current_state_label.alignment = Qt.AlignCenter
        self._current_epoch_label = QLabel()
        self._current_epoch_label.alignment = Qt.AlignCenter

        button_layout = QHBoxLayout()
        button_layout.add_widget(self._start_stop_button)
        button_layout.add_widget(self._pause_resume_button)
        button_layout.add_widget(self._single_step_button)

        layout = QVBoxLayout(self)
        layout.add_layout(button_layout)
        layout.add_widget(self._current_state_label)
        layout.add_widget(self._current_epoch_label)

        self._start_stop_button.clicked.connect(self._next_start_stop_state)
        self._pause_resume_button.clicked.connect(self._next_pause_resume_state)
        self._single_step_button.clicked.connect(self._single_step_simulation)

        self._ga_adapter.started.connect(self._update_since_evolution)
        self._ga_adapter.ended.connect(self._update_since_evolution_ended)
        self._ga_adapter.evolved.connect(self._update_since_evolution)

        self._update_gui()

    def _update_gui(self):
        state_info = self._state_machine_info[self._ga_adapter.state]
        self._start_stop_button.enabled = state_info[1]
        self._pause_resume_button.enabled = state_info[2]
        self._single_step_button.enabled = False # not state_info[2] and not self._ga_adapter.has_evolved
        self._start_stop_button.text = state_info[3]
        self._pause_resume_button.text = state_info[4]
        self._single_step_button.text = 'Single step'

        self._current_state_label.text = state_info[7]

        epoch_prefix = 'Current epoch : '
        epoch_detail = f'{ "-na-" if self._ga_adapter.state is GeneticAlgorithm.State.IDLE else self._ga_adapter.genetic_algorithm.current_epoch }'
        self._current_epoch_label.text = f'{epoch_prefix}{epoch_detail}'

    @Slot()
    def _next_start_stop_state(self):
        if self._ga_adapter.state is not GeneticAlgorithm.State.IDLE:
            self._ga_adapter.stop()
            self.stopped.emit()
        else:
            self._ga_adapter.problem_definition = self._solution_panels.problem_definition
            self.started.emit()
            self._ga_adapter.evolve()

        self._update_gui()

    @Slot()
    def _next_pause_resume_state(self):
        if self._ga_adapter.state is GeneticAlgorithm.State.RUNNING:
            self._ga_adapter.pause()
            self.paused.emit()
        elif self._ga_adapter.state is GeneticAlgorithm.State.PAUSED:
            self._ga_adapter.resume()
            self.resumed.emit()

        self._update_gui()
        
    @Slot()
    def _single_step_simulation(self):
        self._ga_adapter.evolve_one_step()

    @Slot()
    def _update_since_evolution_ended(self):
        self._update_gui()

    @Slot()
    def _update_since_evolution(self):
        self._update_gui()



class QHistoryGraph(QChartView):
    def __init__(self, ga_adapter, parent=None):
        super().__init__(parent)
        
        self._ga_adapter = ga_adapter

        # Initialisation du graphique
        self.chart = QChart()
        self.chart.legend().visible = True
        self.chart.legend().alignment = Qt.AlignBottom
        self.chart.title = "Graphique linéaire mis à jour dynamiquement"
        
        # Préparer les séries pour les données
        self.series_best = QLineSeries()
        self.series_worst = QLineSeries()
        self.series_average = QLineSeries()
        
        self.series_best.name = "Best"
        self.series_worst.name = "Worst"
        self.series_average.name = "Average"

        self.series_best.set_pen(QPen(QColor(0, 196, 0), 1.0))
        self.series_worst.set_pen(QPen(QColor(196, 0, 0), 1.0))
        self.series_average.set_pen(QPen(QColor(96, 0, 255), 1.0))
        
        self.chart.add_series(self.series_best)
        self.chart.add_series(self.series_worst)
        self.chart.add_series(self.series_average)
        
        # Configurer les axes
        self.axisX = QValueAxis()
        self.axisY = QValueAxis()
        self.chart.add_axis(self.axisX, Qt.AlignBottom)
        self.chart.add_axis(self.axisY, Qt.AlignLeft)

        self.series_best.attach_axis(self.axisX)
        self.series_worst.attach_axis(self.axisX)
        self.series_average.attach_axis(self.axisX)
        self.series_best.attach_axis(self.axisY)
        self.series_worst.attach_axis(self.axisY)
        self.series_average.attach_axis(self.axisY)

        self.set_render_hint(QPainter.TextAntialiasing)
        self.set_chart(self.chart)

    def _update_chart(self):
        data_series_best = [QPointF(x, y) for x, y in enumerate(self._ga_adapter.genetic_algorithm.history.history[:,0])] # best
        data_series_worst = [QPointF(x, y) for x, y in enumerate(self._ga_adapter.genetic_algorithm.history.history[:,1])] # worst
        data_series_average = [QPointF(x, y) for x, y in enumerate(self._ga_adapter.genetic_algorithm.history.history[:,2])] # average
        self.series_best.replace(data_series_best)
        self.series_worst.replace(data_series_worst)
        self.series_average.replace(data_series_average)
        
        maximum = self._ga_adapter.genetic_algorithm.history.history[:,0].max()
        
        self.axisX.set_range(0, self._ga_adapter.genetic_algorithm.history.history.shape[0])
        self.axisY.set_range(0, maximum * 1.05)
        
        self.update()

    @Slot()
    def update_history(self):
        self._update_chart()

    @Slot()
    def updateGraph(self, value):
        pass

class QEvolutionInfoWidget(QGroupBox):
    def __init__(self, ga_adapter, parent=None):
        super().__init__(parent)
        self._ga_adapter = ga_adapter

        self.title = 'Evolution information'

        self._info_widget = QPlainTextEdit()

        my_font = self._info_widget.font
        my_font.set_family('Courier New')
        self._info_widget.font = my_font

        self._info_widget.read_only = True
        self._info_widget.placeholder_text = 'No evolution'

        layout = QGridLayout(self)
        layout.add_widget(self._info_widget)

        self.update()

    @Slot()
    def clear(self):
        self._info_widget.plain_text = ''

    @Slot()
    def update(self):
        if self._ga_adapter.genetic_algorithm.current_epoch == 0:
            self._info_widget.plain_text = ''
        else:
            solution_info = 'Solution : '
            for i in range(self._ga_adapter.problem_definition.domains.dimension):
                solution_info += f'\n    - {self._ga_adapter.problem_definition.domains.names[i]} : {self._ga_adapter.genetic_algorithm.history.best_solution[i]}'

            self._info_widget.plain_text = f'''Current epoch : {self._ga_adapter.genetic_algorithm.current_epoch}
Problem dimension : {self._ga_adapter.genetic_algorithm.problem_definition.domains.dimension}
Fitness : 
    - best    : {self._ga_adapter.genetic_algorithm.history.best_fitness:>16.6f}
    - worst   : {self._ga_adapter.genetic_algorithm.history.worst_fitness:>16.6f}
    - average : {self._ga_adapter.genetic_algorithm.history.average_fitness:>16.6f}
    - std dev : {self._ga_adapter.genetic_algorithm.history.standard_deviation_fitness:>16.6f}
    - median  : {self._ga_adapter.genetic_algorithm.history.median_fitness:>16.6f}
{solution_info}'''


class QGAParametersWidget(QGroupBox):

    parameter_changed = Signal()

    def __init__(self, ga_adapter, parent=None):
        super().__init__(parent)

        self._ga_adapter = ga_adapter
        self.title = 'Parameters'
        layout = QFormLayout(self)

        self._maximum_epoch_widget, maximum_epoch_layout = uqtwidgets.create_scroll_int_value(5, 250, 100000)
        self._population_size_widget, population_size_layout = uqtwidgets.create_scroll_int_value(5, 25, 250)
        self._elitism_rate_widget, elitism_rate_layout = uqtwidgets.create_scroll_real_value(0., 0.05, 1., 2, 100., value_suffix = " %")
        self._selection_rate_widget, selection_rate_layout = uqtwidgets.create_scroll_real_value(0.01, 0.75, 1., 2, 100., value_suffix = " %")
        self._mutation_rate_widget, mutation_rate_layout = uqtwidgets.create_scroll_real_value(0., 0.10, 1., 2, 100., value_suffix = " %")
        
        self._selection_strategies = [RouletteWheelSelectionStrategy]
        self._crossover_strategies = [WeightedAverageCrossoverStrategy]
        self._mutation_strategies = [GeneMutationStrategy]

        self._selection_strategy_combo = QComboBox()
        self._crossover_strategy_combo = QComboBox()
        self._mutation_strategy_combo = QComboBox()
        self._selection_strategy_combo.add_items([strategy().name for strategy in self._selection_strategies])
        self._crossover_strategy_combo.add_items([strategy().name for strategy in self._crossover_strategies])
        self._mutation_strategy_combo.add_items([strategy().name for strategy in self._mutation_strategies])

        def create_title(title, tool_tip):
            label = QLabel(title)
            label.tool_tip = tool_tip
            return label
        
        max_epoch_title = create_title('Maximum epoch', 'Maximum number of epochs for the genetic algorithm.\nA value of 100 means that the algorithm will stop after 100 epochs.')
        population_size_title = create_title('Population size', 'Population size for the genetic algorithm.\nA value of 25 means that a population of 25 solutions is maintain and are evolving at each epoch.')
        elitism_rate_title = create_title('Elitism rate', 'Rate of elitism for the genetic algorithm (in percent).\nA value of 0 mean no elitism.')
        selection_rate_title = create_title('Selection rate', 'Rate of selection for the genetic algorithm (in percent).\nA value of 75% means that three-quarters of the population are considered for selection.')
        mutation_rate_title = create_title('Mutation rate', 'Rate of mutation for the genetic algorithm (in percent).\nA value of 10% means that each offspring has a 10% chance of mutation.')
        selection_strategy_title = create_title('Selection strategy', 'Define the selection algorithm used for the genetic algorithm.')
        crossover_strategy_title = create_title('Crossover strategy', 'Define the crossover algorithm used for the genetic algorithm.')
        mutation_strategy_title = create_title('Mutation strategy', 'Define the mutation algorithm used for the genetic algorithm.')

        layout.add_row(max_epoch_title, maximum_epoch_layout)
        layout.add_row(population_size_title, population_size_layout)
        layout.add_row(elitism_rate_title, elitism_rate_layout)
        layout.add_row(selection_rate_title, selection_rate_layout)
        layout.add_row(mutation_rate_title, mutation_rate_layout)
        layout.add_row(selection_strategy_title, self._selection_strategy_combo)
        layout.add_row(crossover_strategy_title, self._crossover_strategy_combo)
        layout.add_row(mutation_strategy_title, self._mutation_strategy_combo)

        # layout.add_row('Maximum epoch', maximum_epoch_layout)
        # layout.add_row('Population size', population_size_layout)
        # layout.add_row('Elitism rate', elitism_rate_layout)
        # layout.add_row('Selection rate', selection_rate_layout)
        # layout.add_row('Mutation rate', mutation_rate_layout)
        # layout.add_row('Selection strategy', self._selection_strategy_combo)
        # layout.add_row('Crossover strategy', self._crossover_strategy_combo)
        # layout.add_row('Mutation strategy', self._mutation_strategy_combo)

        self._maximum_epoch_widget.valueChanged.connect(self.parameter_changed)
        self._population_size_widget.valueChanged.connect(self.parameter_changed)
        self._elitism_rate_widget.valueChanged.connect(self.parameter_changed)
        self._selection_rate_widget.valueChanged.connect(self.parameter_changed)
        self._mutation_rate_widget.valueChanged.connect(self.parameter_changed)
        self._selection_strategy_combo.currentIndexChanged.connect(self.parameter_changed)
        self._crossover_strategy_combo.currentIndexChanged.connect(self.parameter_changed)
        self._mutation_strategy_combo.currentIndexChanged.connect(self.parameter_changed)

        self.parameter_changed.connect(self._update_adapter)
        self.update_from_adapter()

    def add_selection_strategy(self, strategy):
        if not issubclass(strategy, SelectionStrategy):
            raise TypeError('Invalid input parameters add_selection_strategy : strategy must be a subclass of SelectionStrategy.')
        self._selection_strategies.append(strategy)
        self._selection_strategy_combo.add_item(strategy().name)

    def add_crossover_strategy(self, strategy):
        if not issubclass(strategy, CrossoverStrategy):
            raise TypeError('Invalid input parameters add_crossover_strategy : strategy must be a subclass of CrossoverStrategy.')
        self._crossover_strategies.append(strategy)
        self._crossover_strategy_combo.add_item(strategy().name)

    def add_mutation_strategy(self, strategy):
        if not issubclass(strategy, MutationStrategy):
            raise TypeError('Invalid input parameters add_mutation_strategy : strategy must be a subclass of MutationStrategy.')
        self._mutation_strategies.append(strategy)
        self._mutation_strategy_combo.add_item(strategy().name)

    def update_from(self, parameter):
        signal_blocker = QSignalBlocker(self) # pylint: disable=unused-variable
        self._maximum_epoch_widget.value = parameter.maximum_epoch
        self._population_size_widget.value = parameter.population_size
        self._elitism_rate_widget.set_real_value(parameter.elitism_rate)
        self._selection_rate_widget.set_real_value(parameter.selection_rate)
        self._mutation_rate_widget.set_real_value(parameter.mutation_rate)

        self._selection_strategy_combo.current_text = parameter.selection_strategy.name
        self._crossover_strategy_combo.current_text = parameter.crossover_strategy.name
        self._mutation_strategy_combo.current_text = parameter.mutation_strategy.name

        signal_blocker.unblock()
        self.parameter_changed.emit()

    @Slot()
    def update_from_adapter(self):
        self.update_from(self._ga_adapter.parameters)
    
    @Slot()
    def _update_adapter(self):
        self._ga_adapter.parameters.maximum_epoch = self._maximum_epoch_widget.value
        self._ga_adapter.parameters.population_size = self._population_size_widget.value
        self._ga_adapter.parameters.elitism_rate = self._elitism_rate_widget.get_real_value()
        self._ga_adapter.parameters.selection_rate = self._selection_rate_widget.get_real_value()
        self._ga_adapter.parameters.mutation_rate = self._mutation_rate_widget.get_real_value()

        self._ga_adapter.parameters.selection_strategy = self._selection_strategies[self._selection_strategy_combo.current_index]()
        self._ga_adapter.parameters.crossover_strategy = self._crossover_strategies[self._crossover_strategy_combo.current_index]()
        self._ga_adapter.parameters.mutation_strategy = self._mutation_strategies[self._mutation_strategy_combo.current_index]()

    @property
    def maximum_epoch(self):
        return self._maximum_epoch_widget.value

    @property
    def population_size(self):
        return self._population_size_widget.value

    @property
    def elitism_rate(self):
        return self._elitism_rate_widget.get_real_value()

    @property
    def selection_rate(self):
        return self._selection_rate_widget.get_real_value()

    @property
    def mutation_rate(self):
        return self._mutation_rate_widget.get_real_value()

    @property
    def selection_strategy(self):
        return self._selection_strategies[self._selection_strategy.current_text]()

    @property
    def crossover_strategy(self):
        return self._crossover_strategies[self._crossover_strategy.current_text]()

    @property
    def mutation_strategy(self):
        return self._mutation_strategies[self._mutation_strategy.current_text]()



class QSolutionPanels(QTabWidget):

    solution_changed = Signal(int)

    class _TabWidget(QWidget):
        def __init__(self, solution_panel):
            super().__init__()

            self._solution_panel = solution_panel

            description_button = QPushButton('Description')
            label = QLabel(solution_panel.summary)
            label.word_wrap = True
            label.size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
            summary_group_box = QGroupBox('Summary')
            summary_group_layout = QHBoxLayout(summary_group_box)
            summary_group_layout.add_widget(label)
            summary_group_layout.add_widget(description_button)
            summary_group_box.size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

            description_button.clicked.connect(lambda : QMessageBox.information(self, f'{self._solution_panel.name} description', solution_panel.description))

            layout = QGridLayout(self)
            layout.add_widget(summary_group_box)
            layout.add_widget(self._solution_panel)
            solution_layout = self._solution_panel.layout()
            if solution_layout:
                solution_layout.contents_margins = QMargins(0, 0, 0, 0)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

        self.currentChanged.connect(self.change_solution)
        self.currentChanged.connect(self.solution_changed)

    def add_solution_panel(self, solution_panel):
        # TO DO - THIS IS NOT WORKING WHEN solution_panel is defined in another module
        # if not isinstance(solution_panel, QSolutionToSolvePanel):
        #     raise ValueError('Invalid input parameters in SolutionPanels.add_solution_panel : panel must be a SolutionToSolvePanel object.')

        self.add_tab(QSolutionPanels._TabWidget(solution_panel), solution_panel.name)
        self.currentChanged.connect(lambda : solution_panel._update_from_simulation(None))

    @Slot()
    def change_solution(self):
        pass

    @Slot()
    def update(self, ga):
        self.current_widget()._solution_panel.update_solution(ga)

    @property
    def default_parameters(self):
        return self.current_widget()._solution_panel.default_parameters

    @property
    def problem_definition(self):
        return self.current_widget()._solution_panel.problem_definition


class QGAApp(QMainWindow):
    '''
    L'application de résolution de problème par algorithme génétique.

    Cette classe possède 4 fonctions utilitaires pratiques :
        - ajout de panneau de résolution de problème : add_solution_panel
        - ajout de stratégie de sélection : add_selection_strategy
        - ajout de stratégie de croisement : add_crossover_strategy
        - ajout de stratégie de mutation : add_mutation_strategy
    '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window_title = 'Genetic Algorithm Solver'
        self.window_icon = QIcon('images/gaapp.png')

        self._ga = QGAAdapter()

        self._create_gui()


    def _create_gui(self):
        self.enabled = False

        self._solution_panels = QSolutionPanels()
        self._control_widget = QGAControlWidget(self._ga, self._solution_panels)
        self._parameter_widget = QGAParametersWidget(self._ga)
        self._evolution_info_widget = QEvolutionInfoWidget(self._ga)
        self._history_graph_widget = QHistoryGraph(self._ga)

        self._show_history_widget = QCheckBox()
        self._show_history_widget.checked = True
        show_history_layout = QHBoxLayout()
        show_history_layout.add_stretch()
        show_history_layout.add_widget(QLabel('Show history '))
        show_history_layout.add_widget(self._show_history_widget)

        show_history_group_box = QGroupBox('History')
        show_history_group_layout = QVBoxLayout(show_history_group_box)
        show_history_group_layout.add_widget(self._history_graph_widget)
        show_history_group_layout.add_layout(show_history_layout)

        self._show_history_widget.stateChanged.connect(self._history_graph_widget.updateGraph) 

        # self._parameter_widget.update_from_adapter(self._ga)
        
        self._ga.started.connect(lambda : setattr(self._parameter_widget, 'enabled', False))
        self._ga.started.connect(lambda : setattr(self._solution_panels, 'enabled', False))
        self._ga.ended.connect(lambda : setattr(self._parameter_widget, 'enabled', True))
        self._ga.ended.connect(lambda : setattr(self._solution_panels, 'enabled', True))
        self._ga.evolved.connect(self._history_graph_widget.update_history)
        self._ga.evolved.connect(self._evolution_info_widget.update)
        self._ga.evolved.connect(lambda:self._solution_panels.update(self._ga.genetic_algorithm))

        self._ga.reseted.connect(self._history_graph_widget.update_history)
        self._ga.reseted.connect(self._evolution_info_widget.update)
        self._ga.reseted.connect(self._parameter_widget.update_from_adapter)
        

        self._solution_panels.solution_changed.connect(lambda : self._ga.reset(self._solution_panels.default_parameters, self._solution_panels.problem_definition))
        # self._solution_panels.solution_changed.connect(self._evolution_info_widget.clear)
        # self._solution_panels.solution_changed.connect(self._history_graph_widget.update_history)

        left_widget = QWidget()
        left_widget.size_policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_widget)
        left_layout.add_widget(self._control_widget)
        left_layout.add_widget(self._parameter_widget)
        # left_layout.add_stretch()
        left_layout.add_widget(self._evolution_info_widget)

        self.__main_splitter = QSplitter()
        self.__main_splitter.orientation = Qt.Vertical
        self.__main_splitter.add_widget(self._solution_panels)
        self.__main_splitter.add_widget(show_history_group_box)
        
        central_widget = QWidget()
        central_layout = QHBoxLayout(central_widget)
        central_layout.add_widget(left_widget)
        central_layout.add_widget(self.__main_splitter)

        self.set_central_widget(central_widget)

    def show_event(self, event):
        self.__main_splitter.set_sizes([70, 30])

    def add_solution_panel(self, solution_panel):
        self._solution_panels.add_solution_panel(solution_panel)
        self.enabled = True

    def add_selection_strategy(self, strategy):
        self._parameter_widget.add_selection_strategy(strategy)

    def add_crossover_strategy(self, strategy):
        self._parameter_widget.add_crossover_strategy(strategy)

    def add_mutation_strategy(self, strategy):
        self._parameter_widget.add_mutation_strategy(strategy)


