import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QGroupBox,
    QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSize
from scipy import ndimage
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor
import math


class AnimatedPixelButton(QPushButton):
    def __init__(self, row, col, button_size=30):
        super().__init__()
        self.row = row
        self.col = col
        self.state = False
        self.is_hovered = False
        self.click_animation_active = False
        self.base_size = button_size
        self.setFixedSize(button_size, button_size)
        
        # Store original position and size
        self.original_geometry = None
        
        # Animation properties
        self.highlight_progress = 0.0
        self.processing_animation = False
        
        # Setup hover/click animations
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.click_animation = QPropertyAnimation(self, b"geometry")
        self.click_animation.setDuration(100)
        self.click_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Timer for processing animation
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.updateProcessingAnimation)
        self.process_timer.setInterval(5)
        
        self.setMouseTracking(True)
        self.updateStyle()

    def showEvent(self, event):
        super().showEvent(event)
        if self.original_geometry is None:
            self.original_geometry = self.geometry()

    def enterEvent(self, event):
        self.is_hovered = True
        if self.original_geometry is None:
            self.original_geometry = self.geometry()
            
        new_size = int(self.base_size * 1.1)
        new_geometry = QRect(self.original_geometry)
        new_geometry.setSize(QSize(new_size, new_size))
        new_geometry.moveCenter(self.original_geometry.center())
        
        self.hover_animation.setStartValue(self.geometry())
        self.hover_animation.setEndValue(new_geometry)
        self.hover_animation.start()
        self.updateStyle()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.hover_animation.setStartValue(self.geometry())
        self.hover_animation.setEndValue(self.original_geometry)
        self.hover_animation.start()
        self.updateStyle()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_animation_active = True
            if self.original_geometry is None:
                self.original_geometry = self.geometry()
            
            current_size = self.geometry().width()
            new_size = int(self.base_size * 0.9)
            new_geometry = QRect(self.original_geometry)
            new_geometry.setSize(QSize(new_size, new_size))
            new_geometry.moveCenter(self.original_geometry.center())
            
            self.click_animation.setStartValue(self.geometry())
            self.click_animation.setEndValue(new_geometry)
            self.click_animation.start()
            
            self.updateStyle()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_animation_active = False
            new_size = int(self.base_size * (1.1 if self.is_hovered else 1.0))
            new_geometry = QRect(self.original_geometry)
            new_geometry.setSize(QSize(new_size, new_size))
            new_geometry.moveCenter(self.original_geometry.center())
            
            self.click_animation.setStartValue(self.geometry())
            self.click_animation.setEndValue(new_geometry)
            self.click_animation.start()
            self.updateStyle()
        super().mouseReleaseEvent(event)

    def startProcessingAnimation(self, target_state):
        """Start the processing animation for morphological operations"""
        self.processing_animation = True
        self.target_state = target_state
        self.highlight_progress = 0.0
        self.process_timer.start()

    def updateProcessingAnimation(self):
        """Update the processing animation state"""
        if self.processing_animation:
            self.highlight_progress += 0.1
            if self.highlight_progress >= 1.0:
                self.highlight_progress = 0.0
                self.processing_animation = False
                self.state = self.target_state
                self.process_timer.stop()
            self.updateStyle()

    def updateStyle(self):
        # Base color calculation
        if self.processing_animation:
            # Calculate animation colors for processing
            if self.target_state:  # Transitioning to black
                r = g = b = int(255 * (1.0 - self.highlight_progress))
                highlight = QColor(0, 100, 255)  # Blue highlight
            else:  # Transitioning to white
                r = g = b = int(255 * self.highlight_progress)
                highlight = QColor(255, 100, 0)  # Orange highlight
            
            # Blend with highlight color
            blend_factor = abs(math.sin(self.highlight_progress * math.pi)) * 0.5
            base_color = QColor(
                int(r * (1 - blend_factor) + highlight.red() * blend_factor),
                int(g * (1 - blend_factor) + highlight.green() * blend_factor),
                int(b * (1 - blend_factor) + highlight.blue() * blend_factor)
            )
        else:
            # Normal state coloring
            base_intensity = 255 if not self.state else 0
            if self.is_hovered:
                if self.state:  # Dark state
                    base_color = QColor(40, 40, 60)  # Dark blue-ish
                else:  # Light state
                    base_color = QColor(220, 220, 255)  # Light blue-ish
            else:
                base_color = QColor(base_intensity, base_intensity, base_intensity)
            
            if self.click_animation_active:
                if self.state:
                    base_color = QColor(40, 60, 40)  # Dark green-ish
                else:
                    base_color = QColor(220, 255, 220)  # Light green-ish
        
        # Border style
        border_style = "2px solid #666" if self.is_hovered else "1px solid gray"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color.name()};
                border: {border_style};
                border-radius: 2px;
            }}
        """)

class EnhancedGridWidget(QWidget):
    gridChanged = pyqtSignal()

    def __init__(self, rows=10, cols=10, editable=False, button_size=30):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.editable = editable
        self.button_size = button_size
        self.buttons = []
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        layout.setSpacing(0)

        for i in range(self.rows):
            row_buttons = []
            for j in range(self.cols):
                btn = AnimatedPixelButton(i, j, self.button_size)
                if self.editable:
                    btn.clicked.connect(self.buttonClicked)
                layout.addWidget(btn, i, j)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        self.setLayout(layout)

    def buttonClicked(self):
        button = self.sender()
        button.state = not button.state
        button.updateStyle()
        self.gridChanged.emit()

    def getGrid(self):
        return np.array([[int(btn.state) for btn in row] for row in self.buttons])

    def setGrid(self, grid):
        if grid is None or len(grid) != self.rows or len(grid[0]) != self.cols:
            return
        for i in range(self.rows):
            for j in range(self.cols):
                self.buttons[i][j].state = bool(grid[i][j])
                self.buttons[i][j].updateStyle()


class OperationExplanationWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMinimumHeight(100)
        self.updateExplanation("Erosion")

    def updateExplanation(self, operation):
        explanations = {
            "Erosion": """Erosion shrinks or thins objects. It removes pixels on object boundaries,useful for eliminating small protrusions or breaking apart connected components.""",
            "Dilation": """Dilation expands or thickens objects. It adds pixels to object boundaries,useful for filling small holes or connecting nearby components.""",
            "Opening": """Opening is erosion followed by dilation. It removes small objects while preserving the shape and size of larger objects.""",
            "Closing": """Closing is dilation followed by erosion. It fills small holes and gaps while preserving the shape and size of objects.""",
        }
        self.setText(explanations.get(operation, ""))


class TextPatternGenerator:
    def __init__(self):
        # Initialize font parameters
        self.font_size = (7, 5)  # Height and width for each character

    def _get_digit_pattern(self, digit):
        """Generate pattern for a digit (0-9)"""
        grid = np.zeros(self.font_size)
        h, w = self.font_size

        if digit == "0":
            # Draw a rectangle with empty center
            grid[0, 1 : w - 1] = 1  # Top
            grid[h - 1, 1 : w - 1] = 1  # Bottom
            grid[1 : h - 1, 0] = 1  # Left
            grid[1 : h - 1, w - 1] = 1  # Right
        elif digit == "1":
            grid[:, w // 2] = 1  # Vertical line
            grid[0, w // 2 - 1 : w // 2 + 1] = 1  # Top serif
            grid[h - 1, w // 2 - 1 : w // 2 + 1] = 1  # Base
        elif digit == "2":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[1 : h // 2, w - 1] = 1  # Top right
            grid[h // 2 + 1 : h - 1, 0] = 1  # Bottom left
        elif digit == "3":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[1 : h - 1, w - 1] = 1  # Right side
        elif digit == "4":
            grid[: h // 2 + 1, 0] = 1  # Left top
            grid[h // 2, :] = 1  # Middle
            grid[:, w - 1] = 1  # Right side
        elif digit == "5":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[1 : h // 2, 0] = 1  # Top left
            grid[h // 2 + 1 : h - 1, w - 1] = 1  # Bottom right
        elif digit == "6":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[h // 2 :, w - 1] = 1  # Bottom right
        elif digit == "7":
            grid[0, :] = 1  # Top
            grid[:, w - 1] = 1  # Right side
        elif digit == "8":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
        elif digit == "9":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[: h // 2, 0] = 1  # Top left
            grid[:, w - 1] = 1  # Right side

        return grid

    def _get_letter_pattern(self, letter):
        """Generate pattern for a letter (A-Z)"""
        grid = np.zeros(self.font_size)
        h, w = self.font_size

        if letter == "A":
            grid[1:, 0] = 1  # Left side
            grid[1:, w - 1] = 1  # Right side
            grid[0, 1 : w - 1] = 1  # Top
            grid[h // 2, 1 : w - 1] = 1  # Middle
        elif letter == "B":
            grid[:, 0] = 1  # Left side
            grid[0, : w - 1] = 1  # Top
            grid[h - 1, : w - 1] = 1  # Bottom
            grid[h // 2, : w - 1] = 1  # Middle
            grid[1 : h // 2, w - 1] = 1  # Top right
            grid[h // 2 + 1 : h - 1, w - 1] = 1  # Bottom right
        elif letter == "C":
            grid[1 : h - 1, 0] = 1  # Left side
            grid[0, 1:] = 1  # Top
            grid[h - 1, 1:] = 1  # Bottom
        elif letter == "D":
            grid[:, 0] = 1  # Left side
            grid[0, : w - 1] = 1  # Top
            grid[h - 1, : w - 1] = 1  # Bottom
            grid[1 : h - 1, w - 1] = 1  # Right side
        elif letter == "E":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h - 1, :] = 1  # Bottom
            grid[h // 2, :] = 1  # Middle
        elif letter == "F":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
        elif letter == "G":
            grid[1 : h - 1, 0] = 1  # Left side
            grid[0, 1:] = 1  # Top
            grid[h - 1, 1:] = 1  # Bottom
            grid[h // 2 : h - 1, w - 1] = 1  # Bottom right
            grid[h // 2, h // 2 :] = 1  # Middle right
        elif letter == "H":
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
            grid[h // 2, :] = 1  # Middle
        elif letter == "I":
            grid[0, :] = 1  # Top
            grid[h - 1, :] = 1  # Bottom
            grid[:, w // 2] = 1  # Middle vertical
        elif letter == "J":
            grid[0, :] = 1  # Top
            grid[:, w - 1] = 1  # Right side
            grid[h - 1, : w - 1] = 1  # Bottom
            grid[h - 2, 0] = 1  # Bottom left corner
        elif letter == "K":
            grid[:, 0] = 1  # Left side
            for i in range(h):
                j = abs(i - h // 2)
                if j < w - 1:
                    grid[i, w - 1 - j] = 1
        elif letter == "L":
            grid[:, 0] = 1  # Left side
            grid[h - 1, :] = 1  # Bottom
        elif letter == "M":
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
            grid[1 : h // 2, w // 2] = 1  # Middle
            grid[0, w // 2] = 1  # Top middle
        elif letter == "N":
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
            for i in range(h):
                grid[i, i * (w - 1) // (h - 1)] = 1  # Diagonal
        elif letter == "O":
            grid[1 : h - 1, 0] = 1  # Left side
            grid[1 : h - 1, w - 1] = 1  # Right side
            grid[0, 1 : w - 1] = 1  # Top
            grid[h - 1, 1 : w - 1] = 1  # Bottom
        elif letter == "P":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[1 : h // 2, w - 1] = 1  # Top right
        elif letter == "Q":
            grid[1 : h - 1, 0] = 1  # Left side
            grid[1 : h - 1, w - 1] = 1  # Right side
            grid[0, 1 : w - 1] = 1  # Top
            grid[h - 1, 1 : w - 1] = 1  # Bottom
            grid[h - 2 : h, w - 2 : w] = 1  # Tail
        elif letter == "R":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[1 : h // 2, w - 1] = 1  # Top right
            for i in range(h // 2, h):
                j = (i - h // 2) * (w - 1) // ((h - 1) - h // 2)
                if j < w:
                    grid[i, j] = 1  # Diagonal
        elif letter == "S":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[1 : h // 2, 0] = 1  # Top left
            grid[h // 2 + 1 : h - 1, w - 1] = 1  # Bottom right
        elif letter == "T":
            grid[0, :] = 1  # Top
            grid[:, w // 2] = 1  # Middle vertical
        elif letter == "U":
            grid[: h - 1, 0] = 1  # Left side
            grid[: h - 1, w - 1] = 1  # Right side
            grid[h - 1, 1 : w - 1] = 1  # Bottom
        elif letter == "V":
            for i in range(h - 1):
                grid[i, i * (w - 1) // (h - 1)] = 1  # Left diagonal
                grid[i, w - 1 - i * (w - 1) // (h - 1)] = 1  # Right diagonal
            grid[h - 1, w // 2] = 1  # Bottom point
        elif letter == "W":
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
            grid[h // 2 :, w // 2] = 1  # Middle bottom
        elif letter == "X":
            for i in range(h):
                grid[i, i * (w - 1) // (h - 1)] = 1  # Main diagonal
                grid[i, w - 1 - i * (w - 1) // (h - 1)] = 1  # Counter diagonal
        elif letter == "Y":
            for i in range(h // 2):
                grid[i, i * (w - 1) // (h - 1)] = 1  # Left diagonal
                grid[i, w - 1 - i * (w - 1) // (h - 1)] = 1  # Right diagonal
            grid[h // 2 :, w // 2] = 1  # Bottom vertical
        elif letter == "Z":
            grid[0, :] = 1  # Top
            grid[h - 1, :] = 1  # Bottom
            for i in range(h):
                grid[i, w - 1 - i * (w - 1) // (h - 1)] = 1  # Diagonal

        return grid

    def generate_pattern(self, char, grid_size=(10, 10)):
        if not char:
            return np.zeros(grid_size)

        char = char.upper()
        if char.isdigit():
            pattern = self._get_digit_pattern(char)
        elif char.isalpha():
            pattern = self._get_letter_pattern(char)
        else:
            return np.zeros(grid_size)

        result = np.zeros(grid_size)

        # Calculate position to center the character
        start_row = (grid_size[0] - self.font_size[0]) // 2
        start_col = (grid_size[1] - self.font_size[1]) // 2

        # Place the pattern in the center of the grid
        result[
            start_row : start_row + self.font_size[0],
            start_col : start_col + self.font_size[1],
        ] = pattern

        return result


class PatternLibraryWidget(QGroupBox):
    patternSelected = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__("Pattern Generator")
        self.text_generator = TextPatternGenerator()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Text pattern section
        text_group = QGroupBox("Text Pattern")
        text_layout = QHBoxLayout()

        self.text_input = QLineEdit()
        self.text_input.setMaxLength(1)
        self.text_input.returnPressed.connect(self.onTextPatternSelected)
        text_layout.addWidget(QLabel("Character:"))
        text_layout.addWidget(self.text_input)

        generate_text_btn = QPushButton("Generate")
        generate_text_btn.clicked.connect(self.onTextPatternSelected)
        text_layout.addWidget(generate_text_btn)

        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

        # Add Random Grid button
        random_btn = QPushButton("Random Grid")
        random_btn.clicked.connect(lambda: self.window().generateRandomGrid())
        layout.addWidget(random_btn)

        self.setLayout(layout)

    def onTextPatternSelected(self):
        char = self.text_input.text().upper()
        if char:
            pattern = self.text_generator.generate_pattern(char)
            self.patternSelected.emit(pattern)
            main_window = self.window()
            if main_window:
                main_window.updateResult()
            self.text_input.clear()


class MorphologicalGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Animation state
        self.animation_in_progress = False
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animateOperation)
        self.animation_timer.setInterval(5)  # Default animation speed
        self.current_row = 0
        self.current_col = 0
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Morphological Operations")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()

        # Left panel (input)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Input Grid (Click to Toggle)"))
        self.left_grid = EnhancedGridWidget(rows=10, cols=10, editable=True)
        self.left_grid.gridChanged.connect(self.updateResult)
        left_layout.addWidget(self.left_grid)
        self.explanation = OperationExplanationWidget()
        left_layout.addWidget(self.explanation)
        left_panel.setLayout(left_layout)

        # Middle panel (controls)
        middle_panel = QWidget()
        middle_layout = QVBoxLayout()
        
        # Operation selector
        middle_layout.addWidget(QLabel("Operation:"))
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Erosion", "Dilation", "Opening", "Closing"])
        self.operation_combo.currentTextChanged.connect(self.onOperationChanged)
        middle_layout.addWidget(self.operation_combo)

        # Structuring element
        middle_layout.addWidget(QLabel("Structuring Element:"))
        self.struct_element = EnhancedGridWidget(rows=3, cols=3, editable=True, button_size=20)
        self.struct_element.gridChanged.connect(self.updateResult)
        struct_grid = np.ones((3, 3))
        self.struct_element.setGrid(struct_grid)
        middle_layout.addWidget(self.struct_element)

        # Pattern library
        self.pattern_library = PatternLibraryWidget()
        self.pattern_library.patternSelected.connect(self.left_grid.setGrid)
        middle_layout.addWidget(self.pattern_library)
        middle_panel.setLayout(middle_layout)

        # Right panel (result)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Result"))
        self.right_grid = EnhancedGridWidget(rows=10, cols=10, editable=False)
        right_layout.addWidget(self.right_grid)
        right_panel.setLayout(right_layout)

        # Add all panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(middle_panel)
        main_layout.addWidget(right_panel)
        main_widget.setLayout(main_layout)

    def generateRandomGrid(self):
        random_grid = np.random.choice([0, 1], size=(10, 10), p=[0.7, 0.3])
        self.left_grid.setGrid(random_grid)
        self.updateResult()

    def onOperationChanged(self, operation):
        self.explanation.updateExplanation(operation)
        self.updateResult()

    def updateResult(self):
        if self.animation_in_progress:
            return
        
        # Store current state for animation
        self.input_grid = self.left_grid.getGrid()
        self.structure = self.struct_element.getGrid()
        self.operation = self.operation_combo.currentText()
        
        # Calculate final result for reference
        self.final_result = self.applyOperation(
            self.input_grid, self.structure, self.operation)
        
        # Initialize animation state
        self.current_row = 0
        self.current_col = 0
        self.animation_in_progress = True
        
        # Start animation timer
        self.animation_timer.start()

    def animateOperation(self):
        if not self.animation_in_progress:
            return

        rows, cols = self.input_grid.shape
        struct_rows, struct_cols = self.structure.shape
        half_struct_row = struct_rows // 2
        half_struct_col = struct_cols // 2
        
        # Calculate region affected by structuring element
        row_start = max(0, self.current_row - half_struct_row)
        row_end = min(rows, self.current_row + half_struct_row + 1)
        col_start = max(0, self.current_col - half_struct_col)
        col_end = min(cols, self.current_col + half_struct_col + 1)
        
        # Animate cells that will change
        for i in range(row_start, row_end):
            for j in range(col_start, col_end):
                current_state = bool(self.input_grid[i, j])
                final_state = bool(self.final_result[i, j])
                if current_state != final_state:
                    self.right_grid.buttons[i][j].startProcessingAnimation(final_state)
        
        # Move to next position
        self.current_col += 1
        if self.current_col >= cols:
            self.current_col = 0
            self.current_row += 1
            
        # Check if animation is complete
        if self.current_row >= rows:
            self.animation_in_progress = False
            self.animation_timer.stop()
            # Update any remaining cells to their final state
            self.right_grid.setGrid(self.final_result)

    def applyOperation(self, input_grid, structure, operation):
        if operation == "Erosion":
            return ndimage.binary_erosion(input_grid, structure=structure)
        elif operation == "Dilation":
            return ndimage.binary_dilation(input_grid, structure=structure)
        elif operation == "Opening":
            return ndimage.binary_opening(input_grid, structure=structure)
        elif operation == "Closing":
            return ndimage.binary_closing(input_grid, structure=structure)
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    morphological_gui = MorphologicalGUI()
    morphological_gui.show()
    sys.exit(app.exec_())
